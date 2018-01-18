#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Project to Clean and Import the OpenStreet Maps XML File into MariaDB """
import logging
import os
import re
import xml.etree.cElementTree as ET
import unicodecsv as csv
import mysql.connector
import usaddress

LOGGER = logging.getLogger('Udacity_OSM')

PROD_FILE = '../data/tampa_florida.osm'
SAMPLE_FILE = '../data/tnc.osm'
DB_HOST = '127.0.0.1'
DB_NAME = 'udacity'
DB_USER = 'root'
DB_PASS = 'admin'
DB_SCHEMA = 'data_wrangling_schema.sql'

NODES_FIELDS = ['id', 'visible', 'version', 'changeset',
                'timestamp', 'user', 'uid', 'lat', 'lon']
ADDRESS_FIELDS = ['id', 'city', 'country', 'housenumber',
                  'postcode', 'state', 'street', 'unit']
WAYS_FIELDS = ['id', 'visible', 'version', 'changeset',
               'timestamp', 'user', 'uid']
TAGS_FIELDS = ['id', 'key', 'value']
WAYS_NODES_FIELDS = ['id', 'node_id', 'position']

STREET_FIXES = {
    "Ave": "Avenue",
    "Blvd": "Boulevard",
    "Dr": "Drive",
    "Pky": "Parkway",
    "Rd": "Road",
}

DIRECTION_FIXES = {
    "S": "South",
    "W": "West",
    "N": "North",
    "E": "East"
}


def setup_logging():
    """ Setup all logging detals here"""
    LOGGER.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fhand = logging.FileHandler('udacity_osm.log')
    fhand.setLevel(logging.FATAL)
    # create console handler with a higher log level
    chand = logging.StreamHandler()
    chand.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fhand.setFormatter(formatter)
    chand.setFormatter(formatter)
    # add the handlers to the logger
    LOGGER.addHandler(fhand)
    LOGGER.addHandler(chand)


def process_to_csv(file_in):
    """ Main process to clean data and save to CSV"""
    LOGGER.info("Processing elements in %s", file_in)
    nodes = []
    nodes_tags = []
    addresses = []
    ways = []
    ways_nodes = []
    ways_tags = []

    for _, elem in ET.iterparse(file_in):
        # Process the nodes
        if elem.tag == 'node':
            node = {}
            node_id = 0
            if elem.keys():
                for name, value in elem.items():
                    if name == 'id':
                        node_id = value
                    node[name] = value

                # Process any tags
                if len(elem):
                    address = {'id': node_id}
                    for tag in elem.iter('tag'):
                        # Build a seperate table for real addresses
                        if 'addr' in tag.attrib['k']:
                            address = add_address(tag, address)
                        else:
                            newtag = {'id': node_id}
                            newtag['key'] = tag.attrib['k'].lower()
                            newtag['value'] = tag.attrib['v']
                            nodes_tags.append(newtag)

                    if len(address) > 1:
                        address = audit_address(address)
                        addresses.append(address)

                nodes.append(node)

        # Process ways
        elif elem.tag == 'way':
            position = 0
            way = {}
            way_id = 0
            if elem.keys():
                for name, value in elem.items():
                    if name == 'id':
                        way_id = value
                    way[name] = value

                # Process any Children Found
                if len(elem):
                    # Process Tags
                    for tag in elem.iter('tag'):
                        way_tag = {'id': way_id}
                        way_tag['key'] = tag.attrib['k'].lower()
                        way_tag['value'] = tag.attrib['v']
                        ways_tags.append(way_tag)
                    # Process Node Relations
                    for ndr in elem.iter('nd'):
                        position += 1
                        way_node = {'id': way_id}
                        way_node['node_id'] = ndr.attrib['ref']
                        way_node['position'] = position
                        ways_nodes.append(way_node)

            ways.append(way)

    write_csv(nodes, 'output/nodes.csv', NODES_FIELDS)
    write_csv(nodes_tags, 'output/nodes_tags.csv', TAGS_FIELDS)
    write_csv(addresses, 'output/node_addresses.csv', ADDRESS_FIELDS)
    write_csv(ways, 'output/ways.csv', WAYS_FIELDS)
    write_csv(ways_tags, 'output/ways_tags.csv', TAGS_FIELDS)
    write_csv(ways_nodes, 'output/ways_nodes.csv', WAYS_NODES_FIELDS)
    return


def write_csv(data, file_out, header):
    """ Writes a list(dict) out to a quoted CSV file"""

    LOGGER.info("Writing %s with %s records", file_out, len(data))
    with open(file_out, 'wb') as output:
        writer = csv.DictWriter(output, header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(data)


def audit_address(address):
    """ Checks for valid street types and other address issues"""
    if 'housenumber' in address:

        num = address['housenumber']
        addy = usaddress.tag(num)
        if 'AddressNumber' in addy[0]:
            address['housenumber'] = addy[0]['AddressNumber']
        if 'street' in address and 'StreetNamePreDirectional' in addy[0]:
            address['street'] = str.format('{} {}', addy[0]['StreetNamePreDirectional'], address['street'])

    if 'street' in address:
        street = address['street']
        try:
            addy = usaddress.tag(street)

        except Exception:
            # Nothing to parse, just ignore it
            pass

        if 'addresscalc' in locals():
            if 'housenumber' not in address and 'AddressNumber' in addy[0]:
                address['housenumber'] = addy[0]['AddressNumber']

            # Remove Street Number from Name
            direction = addy[0]['StreetNamePreDirectional'] if 'StreetNamePreDirectional' in addy[0] else ''
            streetname = addy[0]['StreetName'] if 'StreetName' in addy[0] else ''
            streettype = addy[0]['StreetNamePostType'] if 'StreetNamePostType' in addy[0] else ''

            street = str.format('{} {} {}', direction, streetname, streettype).strip()

        # Check that any common abbreviations are spelled out
        pat = re.compile(r'\b(' + '|'.join(STREET_FIXES.keys()) + r')\b')
        street = pat.sub(lambda x: STREET_FIXES[x.group()], street)

        # Update directional abbreviations to full words
        pat = re.compile(r'\b(' + '|'.join(DIRECTION_FIXES.keys()) + r')\b')
        street = pat.sub(lambda x: DIRECTION_FIXES[x.group()], street)

        address['street'] = street

    return address


def add_address(tag, address):
    """ Create or update an address dictionary"""
    key = tag.attrib['k']
    value = tag.attrib['v']

    if 'housenumber' in key:
        address['housenumber'] = value

    if 'unit' in key:
        address['unit'] = value

    if 'street' in key:
        address['street'] = value

    if 'city' in key:
        address['city'] = value

    if 'state' in key:
        address['state'] = value

    if 'country' in key:
        address['country'] = value

    if 'postcode' in key:
        address['postcode'] = value

    return address


def update_database():
    """ Process CSV files into the database"""
    conn = mysql.connector.connect(user=DB_USER,
                                   password=DB_PASS,
                                   host=DB_HOST)
    cur = conn.cursor()
    cur.execute('use {};'.format(DB_NAME))
    cur.execute('SET GLOBAL connect_timeout=7200;')
    cur.execute('SET GLOBAL wait_timeout=7200;')
    cur.execute('SET GLOBAL interactive_timeout=7200;')

    # Nodes
    if 1 == 1:
        LOGGER.info("Reading Node Table from CSV")
        with open('output/nodes.csv', 'rb') as file:
            datareader = csv.DictReader(file)
            db_out = [(i['id'], i['lat'], i['lon'], i['user'],
                       i['uid'], i['version'], i['changeset'],
                       i['timestamp'])
                      for i in datareader]

        length = len(db_out)
        count = 0
        LOGGER.info("Loading Node table into DB ")
        while count <= length:
            lastcount = count
            count += 100000
            to_process = db_out[lastcount:count]
            cur.executemany("INSERT INTO nodes (id, lat, lon, user, uid, version, changeset, timestamp) \
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", to_process)
            conn.commit()
        LOGGER.info("%d records written to Node table", length)

    # Node Tags
    if 1 == 1:   
        LOGGER.info("Reading Node Tags Table from CSV")
        with open('output/nodes_tags.csv', 'rb') as file:
            datareader = csv.DictReader(file)
            db_out = [(i['id'], i['key'], i['value'])
                      for i in datareader]

        length = len(db_out)
        count = 0
        LOGGER.info("Loading Node Tags table into DB ")
        while count <= length:
            lastcount = count
            count += 100000
            to_process = db_out[lastcount:count]
            cur.executemany("INSERT INTO nodes_tags (`node_id`, `key`, `value`) \
                            VALUES (%s, %s, %s);", to_process)
            conn.commit()
        LOGGER.info("%s records written to Nodes Tags table", len(db_out))

    # Node Address
    if 1 == 1:
        LOGGER.info("Reading Node Address Table from CSV")
        with open('output/node_addresses.csv', 'rb') as file:
            datareader = csv.DictReader(file)
            db_out = [(i['id'], i['housenumber'], i['unit'], i['street'],
                       i['city'], i['state'], i['country'], i['postcode'])
                      for i in datareader]

        length = len(db_out)
        count = 0
        LOGGER.info("Loading Node Address table into DB ")
        while count <= length:
            lastcount = count
            count += 100000
            to_process = db_out[lastcount:count]
            cur.executemany("INSERT INTO nodes_address (node_id, number, unit, street, city, state, country, postcode) \
                            VALUES (%s, %s, %s, %s, %s ,%s ,%s ,%s);", to_process)
            conn.commit()
        LOGGER.info("%s records written to Nodes Adddress table", len(db_out))

    # Ways
    if 1 == 1:
        LOGGER.info("Reading Ways Table from CSV")
        with open('output/ways.csv', 'rb') as file:
            datareader = csv.DictReader(file)
            db_out = [(i['id'], i['user'], i['uid'], i['version'],
                       i['changeset'], i['timestamp'])
                      for i in datareader]

        length = len(db_out)
        count = 0
        LOGGER.info("Loading Ways table into DB ")
        while count <= length:
            lastcount = count
            count += 100000
            to_process = db_out[lastcount:count]
            cur.executemany("INSERT INTO ways (id, user, uid, version, changeset, timestamp) \
                            VALUES (%s, %s, %s, %s, %s ,%s);", to_process)
            conn.commit()
        LOGGER.info("%s records written to Ways table", len(db_out))

    # Ways Tags
    if 1 == 1:
        LOGGER.info("Reading Ways Tags Table from CSV")
        with open('output/ways_tags.csv', 'rb') as file:
            datareader = csv.DictReader(file)
            db_out = [(i['id'], i['key'], i['value'])
                      for i in datareader]

        length = len(db_out)
        count = 0
        LOGGER.info("Loading Ways Tags table into DB ")
        while count <= length:
            lastcount = count
            count += 100000
            to_process = db_out[lastcount:count]
            cur.executemany("INSERT INTO ways_tags (`ways_id`, `key`, `value`) \
                            VALUES (%s, %s, %s);", to_process)
            conn.commit()
        LOGGER.info("%s records written to Ways Tags table", len(db_out))

    # Ways Nodes
    if 1 == 1:
        LOGGER.info("Reading Ways Nodes Table from CSV")
        with open('output/ways_nodes.csv', 'rb') as file:
            datareader = csv.DictReader(file)
            db_out = [(i['id'], i['node_id'], i['position'])
                      for i in datareader]
        length = len(db_out)
        count = 0
        LOGGER.info("Loading Ways Nodes table into DB ")
        while count <= length:
            lastcount = count
            count += 100000
            to_process = db_out[lastcount:count]
            cur.executemany("INSERT INTO ways_nodes (`ways_id`, `node_id`, `position`) \
                            VALUES (%s, %s, %s);", to_process)
            conn.commit()
        LOGGER.info("%s records written to Ways Nodes table", len(db_out))


def database_setup():
    """Setup the database objects"""
    conn = mysql.connector.connect(user=DB_USER,
                                   password=DB_PASS,
                                   host=DB_HOST)
    cur = conn.cursor()

    #  Create the Database if not exists
    cur.execute('CREATE DATABASE IF NOT EXISTS {}'.format(DB_NAME))
    cur.execute('USE {};'.format(DB_NAME))

    # Import OSM Database Schema and Execute it one by one
    file = open(DB_SCHEMA, 'r')
    sql = file.read()
    file.close()

    for command in sql.split(';'):
        try:
            if len(command.strip()) > 0:
                cur.execute(command)
        except mysql.connector.Error as err:
            LOGGER.info(command)
            LOGGER.info("Error: {}".format(err))

    LOGGER.info("Database and Schema Created")
    conn.close()


if __name__ == "__main__":
    # Ensure our output directory exists
    setup_logging()
    if not os.path.exists('./output'):
        os.makedirs('./output/')

    MB = float(float(1024) ** 2)
    LOGGER.info("SAMPLE FILE SIZE: %s MB", "{:.2f}".format(os.stat(SAMPLE_FILE).st_size / MB))
    LOGGER.info("PROD FILE SIZE: %s MB", "{:.2f}".format(os.stat(PROD_FILE).st_size / MB))
    database_setup()
    process_to_csv(PROD_FILE)
    update_database()
