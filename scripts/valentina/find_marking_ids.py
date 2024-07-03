"""
Label points name 1XX names
"""


from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import re
import os
from dataclasses import dataclass
import shutil

def parse_args():
    parser = argparse.ArgumentParser()
    parser.description = __doc__

    parser.add_argument("file", type=Path, help="file to parse")
    parser.add_argument("--piece", default='A', type=str, help="Piece letter to search for")         
    parser.add_argument("--detail", type=str, help="Name of the detail to add labels to")         
    parser.add_argument("--draw", type=str, help="Name of the drawing to process")         
    parser.add_argument("--make_updates",  action='store_true', default=False, help="Make changes to the file")         

    args = parser.parse_args()
    return args

def parse_file(file):
    return ET.parse(file)

def find_base_ids(draw, piece_prefix=None):
    '''
    Find the ids that are not the result of transforms
    '''
    prefix_re = r'[a-zA-Z]' if piece_prefix is None else piece_prefix 
    name_re = r'^' + prefix_re + r'1[0-9]{2}$'

    calc = draw.find('.//calculation')
    points = calc.findall('.//point')
    label_points = [p.get('id') for p in points if re.match(name_re, p.get('name'))]
    return label_points

def find_derived_ids(draw, base_ids):
    '''
    Find the ids that result from operations on a set of base ids
    '''
    derived_ids = []

    calc = draw.find('.//calculation')
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

    return derived_ids

def current_max_id(root):
    '''
    find the current largest ID in the document
    '''
    ids = [int(t.get('id')) for t in root.findall('.//*[@id]')]
    id_refs = [int(t.get('idObject')) for t in root.findall('.//*[@idObject]')]
    return max(ids+id_refs)
    

def find_missing_place_labels(draw, label_points):
    '''
    determine which points do not yet have place labels created for them
    '''
    model = draw.find('.//modeling')
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

def add_labels(root, draw, missing_ids, spec=DEFAULT_LABEL_SPEC):
    '''
    Add a label for each of the missing ids
    '''
    model = draw.find('.//modeling')
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

def add_place_labels_to_details( draw, detail_name, label_ids):
    '''
    Injects a set of place label ids into a detail
    '''
    place_labels = draw.find(f'.//detail[@name="{detail_name}"]/placeLabels')
    assert place_labels is not None, f"Could not find place labels for: '{detail_name}'"
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

def get_draw(root, draw_name):
    return root.find(f'.//draw[@name="{draw_name}"]')



def main():
    args = parse_args()
    tree = parse_file(args.file)
    root = tree.getroot()
    draw = get_draw(root, args.draw)
    
    base_ids = find_base_ids(draw)
    print(base_ids)
    derived_ids = find_derived_ids(draw, base_ids)
    all_ids = base_ids + derived_ids
    missing_ids, existing_label_ids = find_missing_place_labels(draw, all_ids)
    print(existing_label_ids)
    print(missing_ids)
   
    if args.make_updates:
        print('Adding new labels')
        newly_added_labels = add_labels(root,draw, missing_ids)
        print(f'The following label ids were added: {newly_added_labels}')
        add_place_labels_to_details(draw, args.detail, newly_added_labels)
        write_file(tree, args.file)







if __name__ == "__main__":
    main()
