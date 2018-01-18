#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Parse the OSM file and count the numbers of unique tag """

import xml.etree.cElementTree as ET
import pprint

PROD_FILE = '../data/tampa_florida.osm'
SAMPLE_FILE = '../data/tnc.osm'

def count_unique_tags(filename):
    tags = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag in tags: 
            tags[elem.tag] += 1
        else:
            tags[elem.tag] = 1
    return tags
    
if __name__ == "__main__":
	pprint.pprint(count_unique_tags(PROD_FILE))