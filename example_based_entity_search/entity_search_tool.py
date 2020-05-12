#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rank RDF entities based on query (plain text relation and example entities).

    Author: Paweł Płatek
"""


import argparse
from decimal import Decimal as D
from sys import exit
from typing import List, Optional, Tuple

from rdflib import URIRef

from example_based_entity_search.config import D_PREC, URI_PREFIX, L
from example_based_entity_search.entity_search_lib import (rank_combined,
                                                           rank_examples_based,
                                                           rank_text_based)
from example_based_entity_search.utils import (PPGraph, data_from_sample_file,
                                               load_data, statistical_stats)


def do_all_rankings(graph: PPGraph, topic: str, examples: List[URIRef], entities_to_rank: List[URIRef], relevant: List[URIRef] = None):
    """Ranks entities and prints results."""
    # make the rankings
    ranking_text = rank_text_based(graph, (topic, examples), entities_to_rank)
    ranking_example = rank_examples_based(
        graph, (topic, examples), entities_to_rank)
    ranking_combined = rank_combined((ranking_text, ranking_example))

    # and print the results
    print_ranking('text-based', ranking_text[1], relevant)
    print_ranking('example-based', ranking_example[1], relevant)
    print_ranking('combined', ranking_combined[1], relevant)


def print_ranking(name: str, ranking: List[Tuple[D, URIRef]], relevant: Optional[List[URIRef]] = None):
    """Prints ranking. If relevant entities are provided, also prints statistics."""
    print('-'*30)
    print(f'Ranking - {name}:')
    if not relevant:
        for ranking_score, entity in ranking:
            print(f' {entity} - {ranking_score}')
        return

    # how many top entities we would return in ideal case
    # paper sets this to 100
    evaluation_limit = len(relevant)
    retrived: List[bool] = []
    for i, (ranking_score, entity) in enumerate(ranking):
        if entity in relevant:
            if i < evaluation_limit:
                retrived.append(True)
            print(f' OO {entity} - {ranking_score}')
        else:
            if i < evaluation_limit:
                retrived.append(False)
            print(f' xx {entity} - {ranking_score}')

    print('~'*10)
    stats = statistical_stats(retrived)
    for k, v in stats.items():
        print(f' {k} -> {v.quantize(D_PREC)}')


def shell(graph: PPGraph):
    """Run interactive query shell."""
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
        topic = input('Relation (topic, R), as plain text: ')

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

        do_all_rankings(graph, topic, examples, entities_to_rank)

    def do_sample(graph):
        sample_file = input('Sample file to use: ')
        do_all_rankings(graph, *data_from_sample_file(sample_file))

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
        do_all_rankings(graph, *data_from_sample_file(args.sample_file))

    # execute queries from shell
    if args.shell:
        shell(graph)

    return 0


if __name__ == '__main__':
    exit(main())
