'''
A collection on common actions form manipulating valentina XML files to be 
used by individual scripts
'''

import xml.etree.ElementTree as ET
import re
import os
from dataclasses import dataclass
import shutil

def parse_file(file):
    return ET.parse(file)

def place_label_ids(piece, piece_prefix=None):
    '''
    Find the ids that are not the result of transforms
    '''
    prefix_re = r'[a-zA-Z]' if piece_prefix is None else piece_prefix 
    name_re = r'^' + prefix_re + r'1[0-9]{2}$'

    calc = piece.find('.//calculation')
    points = calc.findall('.//point')
    label_points = [p.get('id') for p in points if re.match(name_re, p.get('name'))]
    derived_points = find_derived_ids(piece, label_points)
    return label_points + derived_points

def find_derived_ids(piece, base_ids):
    '''
    Find the ids that result from operations on a set of base ids
    '''
    derived_ids = []

    calc = piece.find('.//calculation')
    operations = calc.findall('operation')
    for operation in operations:
        source = operation.find('source')
        assert source is not None
        dest = operation.find('destination')
        assert dest is not None
        source_items = source.findall('item')
        dest_items = dest.findall('item')
        assert len(source_items) == len(dest_items)
        for source_item, dest_item in zip(source_items, dest_items):
            if source_item.get('idObject') in base_ids:
                derived_ids.append(dest_item.get('idObject'))
    if len(derived_ids) > 0:
        derived_ids += find_derived_ids(piece, derived_ids)

    return derived_ids

def current_max_id(root):
    '''
    find the current largest ID in the document
    '''
    ids = [int(t.get('id')) for t in root.findall('.//*[@id]')]
    id_refs = [int(t.get('idObject')) for t in root.findall('.//*[@idObject]')]
    return max(ids+id_refs)
    

def find_missing_place_labels(piece, label_points):
    '''
    determine which points do not yet have place labels created for them
    '''
    model = piece.find('.//modeling')
    points = model.findall('point[@type="placeLabel"]')
    existing_ids = [p.get('idObject') for p in points]
    missing_ids = [i for i in label_points if i not in existing_ids]
    existing_label_ids = [i for i in label_points if i in existing_ids]
    return  missing_ids, existing_label_ids

@dataclass 
class LabelSpec:
    height: str
    width: str
    angle: str
    placeLabelType: str
    visible: str

DEFAULT_LABEL_SPEC = LabelSpec("2", "2", "0", "2", "1")

def add_labels(root, piece, missing_ids, spec=DEFAULT_LABEL_SPEC):
    '''
    Add a label for each of the missing ids
    '''
    model = piece.find('.//modeling')
    starting_id = current_max_id(root) + 1
    newly_added_labels = []
    for i, missing_id in enumerate(missing_ids):
        attribs = {
            'angle': str(spec.angle),
            'height': str(spec.height),
            'id': str(starting_id + i),
            'idObject': str(missing_id),
            'inUse': 'false',
            'placeLabelType': str(spec.placeLabelType),
            'type': 'placeLabel',
            'visible': str(spec.visible),
            'width': str(spec.width),
        }
        label = ET.Element('point', attrib=attribs)
        model.append(label)
        newly_added_labels.append(attribs['id'])
    return newly_added_labels

def add_place_labels_to_details( piece , label_ids):
    '''
    Injects a set of place label ids into a detail
    '''
    place_labels = piece.find(f'.//detail/placeLabels')
    if place_labels is None:
        print('placeLabels tag did not exist... adding it')
        detail = piece.find(f'.//detail')
        place_labels = ET.Element('placeLabels')
        detail.insert(len(detail)-1, place_labels)

    for label_id in label_ids:
        record = ET.Element('record')
        record.text = str(label_id)
        place_labels.append(record)

def write_file(tree, filepath, create_backup=True):
    if create_backup:
        if os.path.exists(filepath):
            dest = filepath.parent / (filepath.name +'.backup')
            i = 1
            while os.path.exists(dest):
               i += 1 
               dest = filepath.parent / (filepath.name +f'.backup{i}')
               assert i < 10, 'Too many backups, go and delete some'
            shutil.copyfile(filepath, dest)
            assert os.path.exists(dest)
    with open(filepath, 'wb') as f:
        ET.indent(tree)
        tree.write(f, encoding='utf-8')

def get_piece(root, name):
    res = root.find(f'.//draw[@name="{name}"]')
    if res is None:
        raise ValueError(f'Piece with name "{name}" was not able to be found')
    return res

def add_piece(root, piece):
    root.append(piece)


def id_key( elem, path):
    '''
    Return the name of the attrib that contains the id for this type of elem
    '''
    if elem.tag == 'item':
        parent = path[-1]
        if parent.tag == 'source':
            # source items in operations only have ref and no id
            return None
        else:
            return 'idObject'
    return 'id'

def reindex(elem, new_base, path):
    '''
    walks through 'elem' and all of its children. Updates their ids to new values starting with 'new_base'
    '''
    id_mapping = {}

    def replace_id(e, id):
        '''If the element has an id, replace it and return the next id that should be used, otherwise just return the passed id'''
        nonlocal id_mapping
        id_name = id_key(e, path) 
        if id_name in e.attrib.keys():
            old_id = int(e.get(id_name))
            id_mapping[old_id] = id
            e.set(id_name, str(id))
            return id + 1
        return id
        
    current_id = replace_id(elem, new_base)
    path.append(elem)
    for child in elem:
        current_id, id_m = reindex(child, current_id, path)
        id_mapping.update(id_m)
    path.pop()
    return current_id, id_mapping

def find_parent(root, child_tag):
    for parent in root.iter():
        for child in parent:
            if child.tag == child_tag:
                return parent
    raise RuntimeError(f'No parent found for {child_tag}')

def ref_keys( elem, path):
    '''
    Return a list of the attribs that contain id references for the given elem type
    '''
    if elem.tag == 'item':
        parent = path[-1]
        if parent.tag == 'source':
            # source items are refs, others are ids
            return ['idObject']
        elif parent.tag == 'group':
            # group ref tools i guess
            return ['tool']
        else:
            return []
    if elem.tag == 'record':
        return ['TEXT_CONTENTS']
    return ['idObject', 'basePoint', 'firstPoint', 'secondPoint', 'center', 'arc']

def update_refs(elem, id_mapping, path):
    '''
    Walks the tree under 'elem' and uses 'id_mapping' to update all known id references to new values
    '''
    def replace_ref(e):
        '''
        If the element has an id reference, replace it
        '''
        names = ref_keys( e, path)
        for name in names:
            try: 
                if name == 'TEXT_CONTENTS':
                    e.text = str(id_mapping[int(e.text)])
                else:
                    if name in e.attrib.keys():
                        e.set(name, str(id_mapping[int(e.get(name))]))
            except Exception as err:
                print(f'Failed to update ref for: {e.tag}')
    replace_ref(elem)    
    path.append(elem)
    for child in elem:
        update_refs(child, id_mapping, path)
    path.pop()


def test_apply(file, func, *args, **kwargs):
    root = parse_file(file).getroot()
    func(root, *args, **kwargs)
    ET.dump(root)
