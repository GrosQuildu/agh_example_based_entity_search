#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
~Paweł Płatek
'''


import argparse
import bisect
from collections import defaultdict
from decimal import Decimal as D
from functools import lru_cache
from os.path import isdir, isfile
from random import shuffle

from rdflib import RDF, Literal, URIRef
from yaml import YAMLError, safe_load

from config import D_PREC, EXAMPLES_AMOUNT, URI_PREFIX, L  # type: ignore
from utils import PPGraph, load_data  # type: ignore


def normalize(text):
    return str(text).lower()


def text_representation(graph, entity):
    """
    Create text representation of the entity. It is represented
    with triples that have the entity as a subject. Such triples
    are then divided into:
        - attributes: with literal objects
        - types: with 'type' predicates like /subject or /22-rdf-syntax-ns#type
        - links: all other
    Finally all URIs are expanded to text with /rdfs:label predicate.

    Args:
        graph(PPGraph)
        entity(URIRef)

    Returns:
        dict(class_name:list(str))
            keys are: attributes, types, links
            values are lists of rdf labels as strings 
    """
    L.debug('Computing text representation of %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), ['graph is not PPGraph', graph]
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # use this URIs for types
    type_uris = (RDF.type, URIRef('http://www.w3.org/2004/02/skos/core#subject'),
                 URIRef('http://purl.org/dc/elements/1.1/subject'))

    # store triples in sets
    attributes, types, links = defaultdict(
        int), defaultdict(int), defaultdict(int)
    entities_without_label = 0

    # require only `threshold` objects of all type
    threshold = 999

    # iterate over all triples with the entity as the subject
    for triple_predicate, triple_object in graph.predicate_objects(entity):
        cs_to_use = None
        value_to_use = None

        if isinstance(triple_object, Literal):
            cs_to_use = attributes
            value_to_use = triple_object

        elif isinstance(triple_object, URIRef):
            value_to_use = graph.label(triple_object)
            if not value_to_use or len(value_to_use) == 0:
                entities_without_label += 1
                continue

            if triple_predicate in type_uris:
                cs_to_use = types
            else:
                cs_to_use = links

        else:
            continue

        for o in normalize(value_to_use).split():
            cs_to_use[o] += 1

        if all([sum(cs.values()) >= threshold for cs in [attributes, types, links]]):
            break

    result = {
        'attributes': attributes,
        'types': types,
        'links': links
    }
    if entities_without_label > 0:
        L.debug('%d skipped, because of missing label', entities_without_label)
    L.debug('Found: %s, %s, %s',
            *[' '.join([str(sum(cs.values())), 'terms in', cs_name]) for cs_name, cs in result.items()])
    return result


def text_retrieval_model(relation, graph, entity):
    """
    Rank entities (represented as text) based on the probability of
    being relevant to the relation. Based on a language modeling approach.

    Dirichlet model computation is based on:
        http://mlwiki.org/index.php/Smoothing_for_Language_Models#Dirichlet_Prior_Smoothing
        https://www.coursera.org/lecture/text-retrieval/lesson-4-6-smoothing-methods-part-1-kM6Ie
        http://ciir.cs.umass.edu/pubfiles/ir-445.pdf
        (4) http://profsite.um.ac.ir/~monsefi/machine-learning/pdf/Machine-Learning-Tom-Mitchell.pdf

    Args:
        relation(str)
        graph(PPGraph)
        entity(URIRef)

    Returns:
        probability(Decimal)
    """
    L.debug('Computing text-based probability for %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), 'graph is not PPGraph'
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # normalize query
    relation = normalize(relation).split()

    # get text representations of the entity, theta_e
    representations = text_representation(graph, entity)

    # precompute number of terms
    representations_lengths = {cs_name: sum(cs.values()) for
                               cs_name, cs in representations.items()}

    # pseudo-counts or equivalent sample size
    ni = graph.size

    # denominator of "Dirichlet smoothed model of the entire collection of triples"
    # P(t|theta_c) == sum(D in theta_c)tf(t,D) / sum(D in theta_c)|D|
    # D = node text representation
    # theta_c = collection of nodes
    # we do not compute that, too time consuming
    #
    # probability_collection_denominator = D(0)
    # for node in graph.all_nodes():
    #     if isinstance(node, Literal):
    #         triple_object_text = node
    #     else:
    #         triple_object_text = graph.label(node)
    #     probability_collection_denominator += len(normalize(triple_object_text))

    # P(t|theta_c), it should depends on term t
    # but assume it is 1/ni, according to (4), page 182
    probability_collection = D(1) / D(ni)

    # this are experimental
    representation_weights = {
        'attributes': D('0.4'),
        'types': D('0.4'),
        'links': D('0.2')
    }

    # P(R | theta_e) == product(t in R) P(t | theta_w_e)
    final_probability = D('1.0')
    for t in relation:
        L.debug('%s-> processing term %s', ' '*4, repr(t))

        # P(t | theta_w_e) == sum(cs in representations) P(t | theta_cs_e) * P(cs)
        term_probability = D('0.0')
        for cs_name, cs in representations.items():
            # tf(t,e) is the term frequency of t in the representation document of e
            # http://mlwiki.org/index.php/TF-IDF#Term_Frequency
            tf = cs[t]

            # "Dirichlet smoothed model of the entire collection of triples"
            # P(t|theta_c) == sum(D in theta_c)tf(t,D) / sum(D in theta_c)|D|
            # we do not compute that, too time consuming
            #
            # probability_collection_nominator = D(0)
            # for node in graph.all_nodes():
            #     if isinstance(node, Literal):
            #         triple_object_text = node
            #     else:
            #         triple_object_text = graph.label(node)
            #     probability_collection_nominator += normalize(triple_object_text).count(t)
            # probability_collection = probability_collection_nominator / probability_collection_denominator

            # P(t | theta_cs_e) == [tf(t,e) + ni*P(t|theta_c)] / [|e| + ni]
            representation_probability = D(tf + ni*probability_collection)
            representation_probability /= representations_lengths[cs_name] + ni
            L.debug('%s-> probability for %s: %s (tf=%d, |e|=%d)', ' '*8,
                    cs_name, representation_probability.quantize(D_PREC), tf, representations_lengths[cs_name])

            # do the addition
            term_probability += representation_probability * \
                representation_weights[cs_name]

        L.debug('%s-> term probability: %s', ' '*8,
                term_probability.quantize(D_PREC))

        # do the multiplication
        final_probability *= term_probability

    L.debug('Probability: %s', final_probability)
    return final_probability


@lru_cache(1024)
def triples_set_representation(graph, entity):
    """
    Create set representation of the entity. Set containts all
    triples that have the entity as a subject (outlinks)
    or an object (inlinks).

    Args:
        graph(PPGraph)
        entity(URIRef)

    Returns:
        set(tuple(URIRef, URIRef, URIRef/Literal))
    """
    L.debug('Computing triples set representation of %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), ['graph is not PPGraph', graph]
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    result = set()

    # outlinks
    for triple_predicate, triple_object in graph.predicate_objects(subject=entity):
        result.add((triple_predicate, triple_object))
    outlinks = len(result)
    L.debug('%s-> outlinks: %s', ' '*4, outlinks)

    # inlinks
    for triple_subject, triple_predicate in graph.subject_predicates(object=entity):
        result.add((triple_predicate, triple_subject))
    L.debug('%s-> inlinks: %s', ' '*4, len(result) - outlinks)

    return result


def examples_preparsing(graph, examples):
    """
    Most of the final probability depends only on examples
    So we need to compute it only once
    """
    L.debug('Preparsing data for %d examples', len(examples))

    # get set representations
    examples_representations = []
    for example in examples:
        examples_representations.append(
            triples_set_representation(graph, example))

    # n(tr, x) = 1 if tr in x else 0
    # denominator of P(tr|theta_X) = denominator = sum(tr in all(x in X)) sum(x in X) n(tr, x)
    denominator = D(0)
    for example_representation in examples_representations:
        for tr in example_representation:
            for x in examples_representations:
                if tr in x:
                    denominator += 1
    L.debug('Denominator: %s', denominator)

    # P(e_l | theta_X) = sum(tr in X) P(e_l|tr) * P(tr|theta_X)
    # P(tr|theta_X) = sum(x in X) n(tr, x) / dem
    # we can precompute P(tr|theta_X)
    P_examples = dict()
    for example_representation in examples_representations:
        for tr in example_representation:
            nominator = D(0)
            for x in examples_representations:
                if tr in x:
                    nominator += 1
            P_examples[tr] = nominator / denominator

    L.debug('-'*20)
    return P_examples


def example_retrieval_model(P_examples, graph, entity):
    """
    Rank entities (represented as set of triples) based on the similarity of sets.

    Args:
        P_examples(dict(triple: Decimal))
        graph(PPGraph)
        entity(URIRef)

    Returns:
        probability(Decimal)
    """
    L.debug('Computing example-based probability for %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), 'graph is not PPGraph'
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # get set representations of the entity, e_l
    representation = triples_set_representation(graph, entity)

    # P(e_l | theta_X) = sum(tr in X) P(e_l|tr) * P(tr|theta_X)
    # P(e_l|tr) = 1 if tr in e_l else 0
    # P(tr|theta_X) are in P_examples
    final_probability = D(0)
    for tr in P_examples.keys():
        if tr in representation:
            final_probability += P_examples[tr]

    L.debug('Probability: %s', final_probability)
    return final_probability


def rank(retrieval_model, input_data, graph, entities_to_rank):
    entities_to_rank_amount = len(entities_to_rank)
    entities_to_rank_progress = max(1, entities_to_rank_amount//10)
    L.info('Ranking %d entities', entities_to_rank_amount)

    ranking = []
    for i, entity in enumerate(entities_to_rank):
        if i % entities_to_rank_progress == 0:
            L.info(' ~> ranking entity no %d / %d', i, entities_to_rank_amount)
        ranking_score = retrieval_model(input_data, graph, entity)
        bisect.insort_right(ranking, (ranking_score, entity))
        L.debug('-'*20)
        # break

    # best scored first
    ranking = ranking[::-1]
    return ranking


def print_ranking(name, ranking, relevant=None):
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


def shell(graph):
    L.info('-~'*30)
    L.info('Starting interactive shell')

    def print_help():
        print('h/help - print this help')
        print('l/load - load more triples from local files')
        print('q/query - make query')
        print('e/exit - exit shell')

    def do_load(graph: PPGraph) -> PPGraph:
        triples_path = input('Path to triples file: ')
        if not isfile(triples_path) and not isdir(triples_path):
            L.error('`%s` - no such file or directory', triples_path)
            return

        try:
            graph = load_data(triples_path, graph)
        except Exception as e:
            L.error('Error when loading data from `%s`: %s', triples_path, e)

        return graph

    def parse_entity_from_string(graph: PPGraph, entity_string: str) -> URIRef:
        if entity_string.startswith('<'):
            entity_string = entity_string[1:-1]
            L.warning('Entity starts with `<`, trimming to `%s`', entity_string)
        if not entity_string.startswith('http'):
            entity_string = URI_PREFIX + entity_string
            L.warning('Entity not an URI, prepending `%s`', URI_PREFIX)
        return URIRef(entity_string)

    def do_query(graph: PPGraph) -> None:
        relation = input('Relation (R), as plain text: ')

        print('Examples (X), as URIs. Enter (blank line) to finish:')
        examples = []
        while True:
            example = input('   > ').strip()
            if len(example) == 0:
                break
            examples.append(parse_entity_from_string(graph, example))

        print('Entities to rank, as URIs. Enter (blank line) to finish:')
        entities_to_rank = []
        while True:
            entity = input('   > ').strip()
            if len(entity) == 0:
                break
            entities_to_rank.append(parse_entity_from_string(graph, entity))

        # prepare examples for efficiency
        P_examples = examples_preparsing(graph, examples)

        # make the ranking
        ranking_text = rank(text_retrieval_model,
                            relation, graph, entities_to_rank)

        ranking_example = rank(example_retrieval_model,
                               P_examples, graph, entities_to_rank)

        print_ranking('text-based', ranking_text)
        print_ranking('example-based', ranking_example)

    print_help()
    while True:
        choice = input('> ').lower()
        if choice in ['h', 'help']:
            print_help()
        elif choice in ['l', 'load']:
            graph = do_load(graph)
        elif choice in ['q', ' query']:
            do_query(graph)
        elif choice in ['e', 'exit']:
            break
        else:
            print('Wrong input')
            print_help()


def rank_from_sample_file(graph, sample_file):
    L.info('Preparing ranking for sample file')

    if not isfile(sample_file):
        L.error('File `%s` do not exists, aborting!', sample_file)
        return

    try:
        with open(sample_file, 'r') as f:
            sample_data = safe_load(f)
    except YAMLError as e:
        L.error('Error loading sample file `%s`: %s', sample_file, e)
        return

    if not isinstance(sample_data, dict):
        L.error('Sampel data must be dictionary!')
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

    if len(relevant) <= EXAMPLES_AMOUNT:
        L.warning(
            'There is only %d relevant entities in sample data, all will be used as input examples', len(relevant))

    # select random examples from relevant entities
    examples = relevant[:]
    shuffle(examples)
    examples = examples[:EXAMPLES_AMOUNT]
    for example in examples:
        entities_to_rank.remove(example)

    # prepare examples for efficiency
    P_examples = examples_preparsing(graph, examples)

    # make the ranking
    ranking_text = rank(text_retrieval_model,
                        sample_data['topic'], graph, entities_to_rank)

    ranking_example = rank(example_retrieval_model,
                           P_examples, graph, entities_to_rank)

    print_ranking('text-based', ranking_text, relevant)
    print_ranking('example-based', ranking_example, relevant)


def main():
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

    if args.verbose:
        L.setLevel('DEBUG')

    # triples graph
    try:
        graph = load_data(args.triples_data)
    except Exception as e:
        L.error('Error when loading data from `%s`: %s', args.triples_data, e)
        exit(1)

    # execute query from sample file
    if args.sample_file:
        rank_from_sample_file(graph, args.sample_file)

    # execute queries from shell
    if args.shell:
        shell(graph)


if __name__ == '__main__':
    L.setLevel('INFO')
    main()
