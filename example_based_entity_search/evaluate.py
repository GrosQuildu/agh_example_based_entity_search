#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Statistical evaluation for the lib.

    Author: Paweł Płatek
"""


import argparse
from collections import defaultdict
from decimal import Decimal as D
from glob import glob
from os.path import join as path_join
from typing import DefaultDict, Dict, List, Set

from rdflib import URIRef

from example_based_entity_search.config import D_PREC, L
from example_based_entity_search.entity_search_lib import (
    example_retrieval_model, examples_preparsing, rank, text_retrieval_model)
from example_based_entity_search.utils import (PPGraph, data_from_sample_file,
                                               load_data, statistical_stats)


def load_graph(evaluation_data: str):
    triples = glob(path_join(evaluation_data, '*.nq'))

    # load all graphs
    graph = None
    for one_triples_graph_path in triples:
        graph = load_data(one_triples_graph_path, graph)

    return graph


def evaluation(graph: PPGraph, evaluation_data: str):
    samples = glob(path_join(evaluation_data, '*.yml'))

    # collect all entities
    entities_to_rank_unique: Set[URIRef] = set()
    for sample_file in samples:
        _, examples, entities_to_rank_part, _ = data_from_sample_file(
            sample_file)
        entities_to_rank_unique.update(examples)
        entities_to_rank_unique.update(entities_to_rank_part)

    entities_to_rank: List[URIRef] = list(entities_to_rank_unique)
    mean_stats: Dict[str, DefaultDict[str, D]] = {
        'text': defaultdict(D), 'examples': defaultdict(D)}
    mean_stats_denominator = {'text': 0, 'examples': 0}

    # do ranking for every sample file
    for sample_file in samples:
        print(f'Stats for `{sample_file}`:')
        topic, examples, _, relevant = data_from_sample_file(
            sample_file)

        entities_to_rank_wo_examples = entities_to_rank[:]
        for example in examples:
            if example in entities_to_rank_wo_examples:
                entities_to_rank_wo_examples.remove(example)

        # preparse examples for efficiency
        preparsed_examples = examples_preparsing(graph, examples)

        # make the ranking
        for ranking_type in mean_stats.keys():
            print(f'  Ranking with `{ranking_type}-based` method')
            if ranking_type == 'text':
                ranking = rank(text_retrieval_model,
                               topic, graph, entities_to_rank_wo_examples)
            else:
                ranking = rank(example_retrieval_model,
                               preparsed_examples, graph, entities_to_rank_wo_examples)

            # how many top entities we would return in ideal case
            # paper sets this to 100
            evaluation_limit = len(relevant)
            relevant_retrived = 0
            for i, (ranking_score, entity) in enumerate(ranking):
                if i < evaluation_limit:
                    if entity in relevant:
                        relevant_retrived += 1
                        print(f'OO {entity} - {ranking_score}')
                    else:
                        pass
                        print(f'xx {entity} - {ranking_score}')
                else:
                    break

            stats = statistical_stats(relevant_retrived, evaluation_limit)
            for k, v in stats.items():
                print(f'    {k} -> {v.quantize(D_PREC)}')
                mean_stats[ranking_type][k] += v
            mean_stats_denominator[ranking_type] += 1

    print('Mean stats:')
    for ranking_type in mean_stats.keys():
        print(f'  Ranking with `{ranking_type}-based` method')
        for k, v in mean_stats[ranking_type].items():
            print(
                f'    {k} -> {(v / mean_stats_denominator[ranking_type]).quantize(D_PREC)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate ebes library.')
    parser.add_argument(
        'evaluation_data',
        help='Path to directory with triple files (.nq) and sample files (.yml)')
    parser.add_argument("-v", "--verbose", help="debug output",
                        action="store_true")

    args = parser.parse_args()

    L.setLevel('WARNING')
    if args.verbose:
        L.setLevel('DEBUG')

    print('Loading graphs...')
    graph = load_graph(args.evaluation_data)

    evaluation(graph, args.evaluation_data)
