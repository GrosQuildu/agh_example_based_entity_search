#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
~Paweł Płatek
'''

import argparse
from os.path import isfile
from sys import exit
from typing import List

from rdflib import RDFS, BNode, URIRef
from yaml import YAMLError, safe_load

from example_based_entity_search.config import (  # type: ignore
    SPARQL_ENDPOINT, L)
from example_based_entity_search.utils import load_data  # type: ignore


def n3_format(node):
    """Format node (URIRef/Literal) to string in n3 format
    Converted multiline strings to a single line
    """
    return node.n3().replace('\n', '\\n').replace('"""', '"')


def get_and_store_data(sparql_endpoint: str, out_filename: str, entities: List[URIRef]):
    """
    Query remote endpoint for triples and save them in local file
    For every entity in the list get triples like:
        entity -> w/e -> Literal
        entity -> w/e -> URI
        URI -> label -> Literal
        w/e -> w/e -> entity

    Args:
        sparql_endpoint(str)
        out_filename(str)
        entities(list(URIRef))
    """
    entities_amount = len(entities)
    L.info('Getting data from remote endpoint "%s" for %d entities',
           sparql_endpoint, entities_amount)

    # load the endpoint
    try:
        graph = load_data(sparql_endpoint)
    except Exception as e:
        L.error('Error when loading data from `%s`: %s', sparql_endpoint, e)
        exit(1)

    # get triples for every entity in the list
    for i, entity in enumerate(entities):
        L.info('%d / %d', i, entities_amount)
        result = []

        # entity -> w/e -> w/e
        for triple_predicate, triple_object in graph.predicate_objects(
                subject=entity):
            # skip blank nodes
            if isinstance(triple_object, BNode):
                continue

            tr = (entity, triple_predicate, triple_object)
            result.append(tr)

            # URI -> label -> Literal
            if isinstance(triple_object, URIRef):
                try:
                    label = graph.label(triple_object)
                    if label:
                        result.append((triple_object, RDFS.label, label))
                except:
                    pass

        # w/e -> w/e -> entity
        for triple_subject, triple_predicate in graph.subject_predicates(
                object=entity):
            # skip blank nodes
            if isinstance(triple_subject, BNode):
                continue

            result.append((triple_subject, triple_predicate, entity))

        L.debug('Saving %d triples', len(result))
        with open(out_filename, 'a') as f:
            for tr in result:

                f.write(' '.join(map(n3_format, tr)))
                f.write(' <http://dbpedia.org/>')
                f.write(' .\n')


def main():
    # cmd line args
    parser = argparse.ArgumentParser(description='Capture data from \
        remote SPARQL endpoint and save it to local file in nqads format')
    parser.add_argument('filename', help='File to save data in')
    parser.add_argument(
        'sample_file',
        help='YAML file with entities as list of URIs under `sample_key` key')
    parser.add_argument(
        'sample_key', default='relevant',
        help='YAML key for entities list')
    parser.add_argument(
        '-e',
        '--endpoint',
        dest='sparql_endpoint',
        default=SPARQL_ENDPOINT,
        help='SPARQL endpoint url')
    parser.add_argument("-v", "--verbose", help="debug output",
                        action="store_true")

    # args parsing and sanity checks
    args = parser.parse_args()

    L.setLevel('INFO')
    if args.verbose:
        L.setLevel('DEBUG')

    if isfile(args.filename):
        L.warning('File `%s` exists, will append to it!', args.filename)

    if not isfile(args.sample_file):
        L.error('File `%s` do not exists, aborting!', args.sample_file)
        exit(1)

    try:
        with open(args.sample_file, 'r', encoding='utf8') as f:
            sample_data = safe_load(f)
    except YAMLError as e:
        L.error('Error loading sample file `%s`: %s', args.sample_file, e)
        exit(1)

    if not isinstance(sample_data, dict):
        L.error('Sampel data must be dictionary!')
        exit(1)

    if args.sample_key not in sample_data.keys():
        L.error('`%s` key not found in sample data', args.sample_key)
        exit(1)

    # do the job
    entities: List[URIRef] = list(map(URIRef, sample_data[args.sample_key]))
    get_and_store_data(args.sparql_endpoint, args.filename, entities)


if __name__ == '__main__':
    main()
