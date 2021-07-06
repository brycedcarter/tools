#!/usr/bin/env python3

"""
Script for adding timestamps, prefixes, and suffixes to files and directories

Author: Bryce Carter
Date Created: 2021-05-28
"""
# standard imports
import argparse
import os
import re
from datetime import datetime

# constants
FILENAME_RE = re.compile(r'[a-fA-F0-9\.\(\)\-\_]*')


def recursive_rename(directory: str,
                     prefix: str,
                     suffix: str,
                     timestamp_suffix: str,
                     include_date: bool,
                     include_time: bool):
    """
    Walk through a directory recursivly and rename all contents

    Arguments:
        directory -- the directory in which to start the walk
        prefix -- text to prepend to all contents of directory
        suffix -- text to append to all contents of directory
            (before timestamp if any)
        timestamp_suffix -- text to append to all contents of directory
            (after timestamp if any)
        include_date -- flag to indicate that the datestamp should be appended
            to all contents of directory
        include_time -- flag to indicate that the time should be included in
            addition to the date. NOTE: if this options is specified, it will
            imply "incude_date"
    """
    files = []

    # construct the timestamp suffix
    if include_date:
        timestamp_string = datetime.now().strftime('_%m-%d-%Y')
    else:
        timestamp_string = ''

    if include_time:
        timestamp_string = datetime.now().strftime('_%m-%d-%Y_%H-%M-%S')

    for base_path, dirs, files in os.walk(directory, topdown=False):
        for name in files+dirs:
            main_name, extension = os.path.splitext(name)
            original_name = os.path.join(base_path, name)
            new_name = os.path.join(base_path,
                                    prefix
                                    + main_name
                                    + suffix
                                    + timestamp_string
                                    + timestamp_suffix
                                    + extension)
            os.rename(original_name, new_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # positional args
    parser.add_argument('directory')
    # flag args
    parser.add_argument('-d',
                        '--datestamp',
                        action='store_true',
                        help='flag to denote that the datestamp should be '
                             'appended to all files and folders')
    parser.add_argument('-t',
                        '--timestamp',
                        action='store_true',
                        help='flag to denote that the timestamp should be '
                             'included as well as the date stamp')
    # value args
    parser.add_argument('--pre',
                        help='a custom prefix string to prepend before the '
                             'orginal filename',
                        default='')
    parser.add_argument('--suf',
                        help='a custom string to prepend before the timestamp',
                        default='')
    parser.add_argument('--suf_t',
                        help='a custom string to append after the timestamp',
                        default='')

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f'The specified path "{args.directory}" is not a directory. '
              f'Exiting...')
        exit(1)

    if not FILENAME_RE.match(args.pre):
        print(f'The provided prefix of "{args.pre}" is not acceptable for a '
              f'filename. Exiting...')
        exit(1)

    if not FILENAME_RE.match(args.suf):
        print(f'The provided suffix of "{args.suf}" is not acceptable for a '
              f'filename. Exiting...')
        exit(1)

    if not FILENAME_RE.match(args.suf_t):
        print(f'The provided timestamp suffix of "{args.suf_t}" is not '
              f'acceptable for a filename. Exiting...')
        exit(1)

    recursive_rename(args.directory,
                     args.pre,
                     args.suf,
                     args.suf_t,
                     args.datestamp,
                     args.timestamp)
