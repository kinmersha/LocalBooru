# Usage: python3 LocalBooru.py -a|-s [-a] [-c] [-s] [-t] arg1 arg2 ...
# To add an image:
# python3 LocalBooru.py -a path/to/file.png -artist Bob -character susie -rating safe -series generic_show -tags female clothed cute

import atexit
import getopt
import pickle
import shutil
import sys
import uuid

from collections import namedtuple

import logging
logging.basicConfig(level=logging.DEBUG)

import pprint
pp = pprint.PrettyPrinter(indent=4)


# Tags are expected as arguments IFF if the -t flag is given
short_opt = "hA:LR:Sa:c:r:s:"
long_opt = "help add= list remove= search artist= character= rating= series=".split(" ")


def save_obj(name, obj):
    with open(f'data/{name}.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open(f'data/{name}.pkl', 'rb') as f:
        return pickle.load(f)

# Load database
try:
    file_index = load_obj('file_index')
    logging.info('Loaded file_index')
    shutil.copy2('data/file_index.pkl', 'data/file_index.pkl.backup')
    logging.info('Backed up file_index')
except FileNotFoundError:
    file_index = dict() # No existing index

try:
    tag_list = load_obj('tag_list')
    logging.info('Loaded tag_list')
    shutil.copy2('data/tag_list.pkl', 'data/tag_list.pkl.backup')
    logging.info('Backed up tag_list')
except FileNotFoundError:
    tag_list = dict() # No existing tag list

################################################################################

def add(inputfile, tags):
    """Add a file to the database.

    :param inputfile: Path to file to add.
    :param tags: Set of tags for the file.

    :returns: Nothing.
    """
    file_id = str(uuid.uuid4())
    shutil.copy2(inputfile, 'data/' + file_id)

    tags.add(f'fid:{file_id}')
    file_index[file_id] = tags
    for tag in tags:
        if tag in tag_list:
            tag_list[tag].append(file_id)
        else:
            tag_list[tag] = [file_id]

    logging.info(f'Created file "{file_id}"')

def list_tags():
    """List all tags in the database by printing to stdout.

    :returns: Nothing.
    """
    for tag in sorted(tag_list.keys()):
        # Don't print out every unique file id
        if not 'fid:' in tag:
            print('{}: {}'.format(tag, len(tag_list[tag])))

def remove(fid):
    """Remove an image from the database. If the file is not in the database,
    the method does nothing.

    :param fid: The uuid of the file to remove.

    :returns: Nothing.
    """
    # Returns file_index[fid] or None if fid is not in file_index.
    rm_tags = file_index.pop(fid, None)
    if rm_tags:
        logging.info('Removing file "{}".'.format(fid))
        for tag in rm_tags:
            tag_list[tag].remove(fid)
    else:
        logging.info('File "{}" not found.'.format(fid))

def search(tags):
    """Search the database.

    :param tags: Set of tags to search by.

    :returns: Set of file_ids for files that have all listed tags.
    """
    sets = []
    for tag in tags:
        if tag in tag_list:
            sets.append(set(tag_list[tag]))

    if sets:
        results = set.intersection(*sets)
        pp.pprint(results)
        return results
    else:
        print('No files tagged with "{}" found.'.format(" ".join(sorted(tags))))
        return None

################################################################################

def main(args):
    help_str = 'LocalBooru.py [-A filename] | [-L] | [-R uuid] | [-S]  -a <artist> -c <character> -r <rating> -s <series> <tag1 tag2 ...>'

    try:
        opts, args = getopt.gnu_getopt(args, short_opt, long_opt)
    except getopt.GetoptError:
        print(help_str)
        sys.exit(2)

    # Parse input
    tags = []
    for opt, arg in opts:
        if opt == '-h':
            print(help_str)
            sys.exit()
        elif opt in ("-A", "--add"):
            operation = 'add'
            filename = arg
        elif opt in ("-L", "--list"):
            operation = 'list'
        elif opt in ("-R", "--remove"):
            operation = 'remove'
            fid = arg
        elif opt in ("-S", "--search"):
            operation = 'search'
        elif opt in ("-a", "--artist"):
            tags.append(f'artist:{arg}')
        elif opt in ("-c", "--character"):
            tags.append(f'character:{arg}')
        elif opt in ("-r", "--rating"):
            tags.append(f'rating:{arg}')
        elif opt in ("-s", "--series"):
            tags.append(f'series:{arg}')

    # Append all tags (non-specific args; get_opt removes all used options
    # and arguments from the argument list it is passed).
    tags = set(tags + args)

    # Perform DB operation
    if operation == 'add':
        add(filename, tags)
    elif operation == 'list':
        list_tags()
    elif operation == 'remove':
        remove(fid)
    elif operation == 'search':
        search(tags)


def exit_handler():
    save_obj('file_index', file_index)
    save_obj('tag_list', tag_list)
    logging.info('Saved updated indices')


if __name__ == "__main__":
    atexit.register(exit_handler)
    main(sys.argv[1:])
