#! /usr/bin/env python3

import sys
import xml.etree.ElementTree as etree
from urllib.request import urlopen
from argparse import ArgumentParser
from subprocess import call

# List of URL to skip
url_skiplist = []

def import_url(url, parent, after):
    insert_offset = 1
    to_flatten = load_tree_from_url(url)
    for child in to_flatten.getroot():
        parent.insert(list(parent).index(after) + insert_offset, child)
        insert_offset += 1

def flatten_imports(parent, tag):
    while True:
        import_el = parent.find(tag)
        if import_el is None:
            break

        # Get URL from location or schemaLocation tag
        url = import_el.get('location') or import_el.get('schemaLocation')
        if not url:
            return

        # Import the URLs found and replace their content with the import line
        if url not in url_skiplist:
            if options.verbose:
                print(f'Importing URL: {url}')
            import_url(url, parent, import_el)
            url_skiplist.append(url)
        parent.remove(import_el)

def load_tree_from_url(url):
    try:
        with urlopen(url) as fp:
            tree = etree.parse(fp)
        return tree
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        sys.exit(1)

def flatten_wsdl(url, output):
    tree = load_tree_from_url(url)
    root = tree.getroot()

    # Process WSDL imports
    flatten_imports(root, '{http://schemas.xmlsoap.org/wsdl/}import')

    # Process XSD imports
    for schema in root.findall('.//{http://www.w3.org/2001/XMLSchema}schema'):
        flatten_imports(schema, '{http://www.w3.org/2001/XMLSchema}import')

    tree.write(output, encoding='unicode')

# Process command line arguments
parser = ArgumentParser(description="Flatten WSDL imports into a single file")
parser.add_argument('url', help='URL of the WSDL file to process')
parser.add_argument('-f', '--filename', help='Output file to write to')
parser.add_argument('-n', '--namespace', help='Override the default namespace')
parser.add_argument('-t', '--tidy', action="store_true",
                    help='Run |tidy| on the file after flattening. Requires -f')
parser.add_argument('-v', '--verbose', action="store_true", help='Enable verbose output')
options = parser.parse_args()

if options.namespace:
    print('WARNING: the NAMESPACE option is not yet implemented.')

if not options.filename and options.tidy:
    parser.print_help()
    sys.exit()

out = open(options.filename, 'w+') if options.filename else sys.stdout

# Flatten the WSDL!
try:
    print("Processing:", options.url)
    flatten_wsdl(options.url, out)
finally:
    if options.filename:
        out.close()

if options.tidy:
    tidy_args = ['tidy', '-mi', '-xml', options.filename]
    if not options.verbose:
        tidy_args.insert(1, '-q')
    call(tidy_args)
