"""
Make a copy of a piece in the pattern 
"""

from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import copy
from actions import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.description = __doc__

    parser.add_argument("file", type=Path, help="file to parse")
    parser.add_argument(
        "--piece", default="A", type=str, help="Piece letter to search for"
    )
    parser.add_argument(
        "--new_name", type=str, help="Name of the detail to add labels to"
    )
    parser.add_argument(
        "--make_updates",
        action="store_true",
        default=False,
        help="Make changes to the file",
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    tree = parse_file(args.file)
    root = tree.getroot()

    next_id = current_max_id(root) + 1

    piece = get_piece(root, args.piece)
    new_piece = copy.deepcopy(piece)
    new_piece.set('name', args.new_name)

    next_id, id_mapping = reindex(new_piece, next_id, [root])
    update_refs(new_piece, id_mapping, [root])

    add_piece(root, new_piece)

    if args.make_updates:
        write_file(tree, args.file)


if __name__ == "__main__":
    main()
