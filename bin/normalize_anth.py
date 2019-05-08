#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2019 David Wei Chiang <dchiang@nd.edu>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Try to convert ACL Anthology XML format to a standard form, in
which:

- Outside of formulas, no LaTeX is used; only Unicode
- Formulas are tagged as <tex-math> and use LaTeX

Usage: python3 normalize_anth.py <infile> <outfile>

Bugs: 

- Doesn't preserve line breaks and indentation within text fields.
"""

import lxml.etree as etree
import re
import difflib
import logging
from latex_to_unicode import latex_to_xml
from fixedcase.protect import protect

logging.basicConfig(format='%(levelname)s:%(location)s %(message)s', level=logging.INFO)
def filter(r):
    r.location = location
    return True
logging.getLogger().addFilter(filter)

def replace_node(old, new):
    save_tail = old.tail
    old.clear()
    old.tag = new.tag
    old.attrib.update(new.attrib)
    old.text = new.text
    old.extend(new)
    old.tail = save_tail

def process(oldnode, informat):
    if oldnode.tag in ['url', 'href', 'mrf', 'doi', 'bibtype', 'bibkey',
                       'revision', 'erratum', 'attachment', 'paper',
                       'presentation', 'dataset', 'software', 'video']:
        return
    elif oldnode.tag in ['author', 'editor']:
        for oldchild in oldnode:
            process(oldchild, informat=informat)
    else:
        if informat == "latex":
            if len(oldnode) > 0:
                logging.error("field has child elements {}".format(', '.join(child.tag for child in oldnode)))
            oldtext = ''.join(oldnode.itertext())
            newnode = latex_to_xml(oldtext, trivial_math=True, fixed_case=True)
            newnode.tag = oldnode.tag
            newnode.attrib.update(oldnode.attrib)
            replace_node(oldnode, newnode)

    if oldnode.tag in ['title', 'booktitle']:
        protect(oldnode)

if __name__ == "__main__":
    import sys
    import argparse
    ap = argparse.ArgumentParser(description='Convert Anthology XML to standard format.')
    ap.add_argument('infile', help="XML file to read")
    ap.add_argument('outfile', help="XML file to write")
    ap.add_argument('-t', '--latex', action="store_true", help="Assume input fields are in LaTeX (not idempotent")
    args = ap.parse_args()

    if args.latex:
        informat = "latex"
    else:
        informat = "xml"

    tree = etree.parse(args.infile)
    root = tree.getroot()
    if not root.tail:
        # lxml drops trailing newline
        root.tail = "\n"
    for paper in root.findall('paper'):
        fullid = "{}-{}".format(root.attrib['id'], paper.attrib['id'])
        for oldnode in paper:
            location = "{}:{}".format(fullid, oldnode.tag)
            process(oldnode, informat=informat)
                
    tree.write(args.outfile, encoding="UTF-8", xml_declaration=True)
