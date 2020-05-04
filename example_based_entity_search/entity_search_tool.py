#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rank RDF entities based on query (plain text relation and example entities).

    Author: Paweł Płatek
"""


import argparse
from decimal import Decimal as D
from os.path import isfile
from random import shuffle
from sys import exit
from typing import List, Optional, Tuple

from rdflib import URIRef
from yaml import YAMLError, safe_load

from example_based_entity_search.config import EXAMPLES_AMOUNT, URI_PREFIX, L
from example_based_entity_search.entity_search_lib import (
    example_retrieval_model, examples_preparsing, rank, text_retrieval_model)
from example_based_entity_search.utils import PPGraph, load_data


def print_ranking(name: str, ranking: List[Tuple[D, URIRef]], relevant: Optional[List[URIRef]] = None):
    print('-'*30)
    print(f'Ranking - {name}:')
    for ranking_score, entity in ranking:
        if relevant:
            if entity in relevant:
                print(f' OK {entity} - {ranking_score}')
            else:
                print(f' NO {entity} - {ranking_score}')
        else:
            print(f' {entity} - {ranking_score}')


def shell(graph: PPGraph):
    """Run interactive query shell"""
    L.info('-~'*30)
    L.info('Starting interactive shell')

    def print_help():
        print('h/help - print this help')
        print('l/load - load more triples from local files')
        print('q/query - make query')
        print('s/sample - make query from sample file')
        print('e/exit - exit shell')

    def do_load(a_graph: PPGraph) -> PPGraph:
        triples_path = input('Path to triples file or SPARQL endpoint url: ')

        try:
            a_graph = load_data(triples_path, a_graph)
        except Exception as e:
            L.error('Error when loading data from `%s`: %s', triples_path, e)

        return a_graph

    def parse_entity_from_string(entity_string: str) -> URIRef:
        if entity_string.startswith('<'):
            entity_string = entity_string[1:-1]
            L.warning('Entity starts with `<`, trimming to `%s`', entity_string)
        if not entity_string.startswith('http'):
            entity_string = URI_PREFIX + entity_string
            L.warning('Entity not an URI, prepending `%s`', URI_PREFIX)
        return URIRef(entity_string)

    def do_query(a_graph: PPGraph) -> None:
        relation = input('Relation (R), as plain text: ')

        examples_amount = None
        while not examples_amount:
            try:
                examples_amount = int(input('Number of examples (integer): '))
            except:
                L.error('Bad integer! Try harder.')

        print('Examples (X), as URIs.')
        examples = []
        for _ in range(examples_amount):
            while True:
                example = input('   > ').strip()
                if len(example) > 0:
                    break
            examples.append(parse_entity_from_string(example))

        print('Entities to rank, as URIs. Enter (blank line) to finish:')
        entities_to_rank = []
        while True:
            entity = input('   > ').strip()
            if len(entity) == 0:
                break
            entities_to_rank.append(parse_entity_from_string(entity))

        # prepare examples for efficiency
        P_examples = examples_preparsing(graph, examples)

        # make the ranking
        ranking_text = rank(text_retrieval_model,
                            relation, graph, entities_to_rank)

        ranking_example = rank(example_retrieval_model,
                               P_examples, graph, entities_to_rank)

        print_ranking('text-based', ranking_text)
        print_ranking('example-based', ranking_example)

    def do_sample(graph):
        sample_file = input('Sample file to use: ')
        rank_from_sample_file(graph, sample_file)

    print_help()
    while True:
        choice = input('> ').lower()
        if choice in ['h', 'help']:
            print_help()
        elif choice in ['l', 'load']:
            graph = do_load(graph)
        elif choice in ['q', 'query']:
            do_query(graph)
        elif choice in ['s', 'sample']:
            do_sample(graph)
        elif choice in ['e', 'exit']:
            break
        else:
            print('Wrong input')
            print_help()


def rank_from_sample_file(graph, sample_file):
    L.info('Preparing ranking for sample file `%s`', sample_file)

    if not isfile(sample_file):
        L.error('File `%s` do not exists, aborting!', sample_file)
        return

    try:
        with open(sample_file, 'r', encoding='utf8') as f:
            sample_data = safe_load(f)
    except (UnicodeDecodeError, YAMLError) as e:
        L.error('Error loading sample file `%s`: %s', sample_file, e)
        return

    if not isinstance(sample_data, dict):
        L.error('Sample data must be dictionary!')
        return

    for required_key in ['topic', 'relevant', 'not_relevant']:
        if required_key not in sample_data.keys():
            L.error('`%s` key not found in sample data', required_key)
            return

    # convert strings to URIRefs and prepare data
    relevant = list(map(URIRef, sample_data['relevant']))
    not_relevant = list(map(URIRef, sample_data['not_relevant']))
    entities_to_rank = relevant[:] + not_relevant[:]

    if len(relevant) == 0:
        L.error('No relevant entities specified in the sample data')
        return

    examples_amount = EXAMPLES_AMOUNT
    random_examples = True
    if 'examples' in sample_data:
        try:
            examples_amount = int(sample_data['examples'])
            random_examples = False
            L.info('Using top %d entities as examples', examples_amount)
        except Exception as e:
            L.error('Error reading amount of examples from YAML file: %s', e)

    if len(relevant) <= examples_amount:
        L.warning(
            'There is only %d relevant entities in sample data, trimming amount of examples', len(relevant))

    # select random examples from relevant entities
    examples = relevant[:]
    if random_examples:
        shuffle(examples)
    examples = examples[:examples_amount]
    for example in examples:
        entities_to_rank.remove(example)

    # prepare examples for efficiency
    preparsed_examples = examples_preparsing(graph, examples)

    # make the ranking
    ranking_text = rank(text_retrieval_model,
                        sample_data['topic'], graph, entities_to_rank)

    ranking_example = rank(example_retrieval_model,
                           preparsed_examples, graph, entities_to_rank)

    print_ranking('text-based', ranking_text, relevant)
    print_ranking('example-based', ranking_example, relevant)


def main():
    """Tool entry point"""
    # cmd line args
    parser = argparse.ArgumentParser(description='Rank entities')
    parser.add_argument(
        'triples_data',
        help='Path to directory with triple files or path to triple file or SPARQL endpoint url')
    parser.add_argument(
        '-s', '--sample_file',
        help='YAML file with keys: `topic`, `relevant` and `not_relevant`')
    parser.add_argument(
        '--shell', action='store_true',
        help='Run interactive shell')
    parser.add_argument("-v", "--verbose", help="debug output",
                        action="store_true")

    # args parsing and sanity checks
    args = parser.parse_args()

    L.setLevel('INFO')
    if args.verbose:
        L.setLevel('DEBUG')

    # triples graph
    try:
        graph = load_data(args.triples_data)
    except Exception as e:
        L.error('Error when loading data from `%s`: %s', args.triples_data, e)
        return 1

    # execute query from sample file
    if args.sample_file:
        rank_from_sample_file(graph, args.sample_file)

    # execute queries from shell
    if args.shell:
        shell(graph)

    return 0


if __name__ == '__main__':
    exit(main())
