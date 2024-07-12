"""
Label points name 1XX names
"""

from pathlib import Path
import argparse
from actions import *

def parse_args():
    parser = argparse.ArgumentParser()
    parser.description = __doc__

    parser.add_argument("file", type=Path, help="file to parse")
    parser.add_argument("--piece", type=str, help="Name of the piece to process")         
    parser.add_argument("--make_updates",  action='store_true', default=False, help="Make changes to the file")         

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    tree = parse_file(args.file)
    root = tree.getroot()
    piece = get_piece(root, args.piece)
    
    ids = place_label_ids(piece)
    print(ids)
    missing_ids, existing_label_ids = find_missing_place_labels(piece, ids)
    print(existing_label_ids)
   
    if args.make_updates:
        print('Adding new labels')
        newly_added_labels = add_labels(root,piece, missing_ids)
        print(f'The following label ids were added: {newly_added_labels}')
        add_place_labels_to_details(piece, newly_added_labels)
        write_file(tree, args.file)







if __name__ == "__main__":
    main()
