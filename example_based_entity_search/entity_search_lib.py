#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rank RDF entities based on query (plain text relation and example entities).

    Author: Paweł Płatek
"""


import bisect
from collections import defaultdict
from decimal import Decimal as D
from functools import lru_cache
from typing import Any, Callable, DefaultDict, Dict, List, Set, Tuple, Union

from rdflib import RDF, Literal, URIRef

from example_based_entity_search.config import D_PREC, L
from example_based_entity_search.utils import PPGraph, statistical_stats

Triple = Tuple[Union[None, URIRef], URIRef,
               Union[URIRef, Literal]]  # RDF triple
Query = Tuple[str, List[URIRef]]  # (relation, examples)
PreparsedData = Any
RetrievalModel = Callable[[PreparsedData, PPGraph, URIRef], D]
PreparsingFunc = Callable[[PPGraph, Query], PreparsedData]
# (mean_examples_ranking, [(0.23, "smthing"), ...])
Ranking = Tuple[D, List[Tuple[D, URIRef]]]


def normalize_relation(text: str) -> str:
    return str(text).lower()


def _text_representation(graph: PPGraph, entity: URIRef) -> Dict[str, DefaultDict[str, int]]:
    """Creates text representation of the entity.

    Entity is represented with triples that have the entity as a subject. Such triples
    are then divided into:
        - attributes: with literal objects
        - types: with 'type' predicates like /subject or /22-rdf-syntax-ns#type
        - links: all other
    Finally all URIs are expanded to text with /rdfs:label predicate.

    Args:
        graph(PPGraph)
        entity(URIRef)

    Returns:
        dict with keys: attributes, types, links
        values are lists of literals and rdf labels, as strings
    """
    L.debug('Computing text representation of %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), ['graph is not PPGraph', graph]
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # use this URIs for types
    type_uris = (RDF.type, URIRef('http://www.w3.org/2004/02/skos/core#subject'),
                 URIRef('http://purl.org/dc/elements/1.1/subject'))

    # store triples in sets
    attributes: DefaultDict[str, int] = defaultdict(int)
    types: DefaultDict[str, int] = defaultdict(int)
    links: DefaultDict[str, int] = defaultdict(int)
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

        for o in normalize_relation(value_to_use).split():
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


def _text_preparsing(graph: PPGraph, input_data: Query) -> Tuple[List[str], int]:
    """Normalize relation and compute dirichlet model parameters 
    """
    # unpack query
    relation, _ = input_data

    # normalize query
    relation_normalized = normalize_relation(relation).split()

    # pseudo-counts or equivalent sample size
    ni = graph.size

    return relation_normalized, ni


def _text_retrieval_model(preparsed_data: Tuple[List[str], int], graph: PPGraph, entity: URIRef) -> D:
    """Rates entity represented as text.

    Rate is equal to the probability of the entity being relevant to the relation.
    Probability formula is based on a language modeling approach.

    Dirichlet model computation is based on:
        http://mlwiki.org/index.php/Smoothing_for_Language_Models#Dirichlet_Prior_Smoothing
        https://www.coursera.org/lecture/text-retrieval/lesson-4-6-smoothing-methods-part-1-kM6Ie
        http://ciir.cs.umass.edu/pubfiles/ir-445.pdf
        (4) http://profsite.um.ac.ir/~monsefi/machine-learning/pdf/Machine-Learning-Tom-Mitchell.pdf

    Args:
        preparsed_data: preparsed relation, precomputed dirichlet parameters
        graph: RDF triples to use (graph represents whole word we know about)
        entity: RDF entity to rank

    Returns:
        Probability
    """
    L.debug('Computing text-based probability for %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), 'graph is not PPGraph'
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # unpack input data
    relation, ni = preparsed_data

    # get text representations of the entity, theta_e
    representations = _text_representation(graph, entity)

    # precompute number of terms
    representations_lengths = {cs_name: sum(cs.values()) for
                               cs_name, cs in representations.items()}

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
    #     probability_collection_denominator += len(normalize_relation(triple_object_text))

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
        L.debug('%s-> processing term %s', ' ' * 4, repr(t))

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
            #     probability_collection_nominator += normalize_relation(triple_object_text).count(t)
            # probability_collection = probability_collection_nominator / probability_collection_denominator

            # P(t | theta_cs_e) == [tf(t,e) + ni*P(t|theta_c)] / [|e| + ni]
            representation_probability = D(tf + ni * probability_collection)
            representation_probability /= representations_lengths[cs_name] + ni
            L.debug('%s-> probability for %s: %s (tf=%d, |e|=%d)', ' ' * 8,
                    cs_name, representation_probability.quantize(D_PREC), tf, representations_lengths[cs_name])

            # do the addition
            term_probability += representation_probability * \
                representation_weights[cs_name]

        L.debug('%s-> term probability: %s', ' ' * 8,
                term_probability.quantize(D_PREC))

        # do the multiplication
        final_probability *= term_probability

    L.debug('Probability: %s', final_probability)
    return final_probability


@lru_cache(1024)
def _triples_set_representation(graph: PPGraph, entity: URIRef) -> Set[Triple]:
    """Creates set representation of the entity.

    Set contains all triples that have the entity as a subject (outlinks)
    or an object (inlinks).

    Args:
        graph: RDF triples to use (graph represents whole word we know about)
        entity: RDF entity to rank

    Returns:
        set of RDF triples
    """
    L.debug('Computing triples set representation of %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), ['graph is not PPGraph', graph]
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    result = set()

    # outlinks
    for triple_predicate, triple_object in graph.predicate_objects(subject=entity):
        if isinstance(triple_object, Literal):
            result.add((None, triple_predicate, triple_object))
        elif isinstance(triple_object, URIRef):
            result.add((entity, triple_predicate, triple_object))
    outlinks = len(result)
    L.debug('%s-> outlinks: %s', ' ' * 4, outlinks)

    # inlinks
    for triple_subject, triple_predicate in graph.subject_predicates(object=entity):
        result.add((triple_subject, triple_predicate, entity))
    L.debug('%s-> inlinks: %s', ' ' * 4, len(result) - outlinks)

    return result


def _examples_preparsing(graph: PPGraph, input_data: Query) -> Dict[Triple, D]:
    """Convert example entities to frequency (number of occurences).

    Most of the final probability depends only on examples.
    So we need to compute it only once (not for every entity to rank).
    """
    # unpack query
    _, examples = input_data

    L.debug('Preparsing data for %d examples', len(examples))

    # get set representations
    examples_representations = []
    for example in examples:
        examples_representations.append(
            _triples_set_representation(graph, example))

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
    preparsed_examples = dict()
    for example_representation in examples_representations:
        for tr in example_representation:
            nominator = D(0)
            for x in examples_representations:
                if tr in x:
                    nominator += 1
            preparsed_examples[tr] = nominator / denominator

    L.debug('-' * 20)
    return preparsed_examples


def _example_retrieval_model(preparsed_data: Dict[Triple, D], graph: PPGraph, entity: URIRef):
    """Rates entity represented as set of triples.

    Rate is based on the similarity of sets.

    Args:
        preparsed_data: preparsed example entities
        graph: RDF triples to use (graph represents whole word we know about)
        entity: RDF entity to rank

    Returns:
        Probability
    """
    L.debug('Computing example-based probability for %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), 'graph is not PPGraph'
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # get set representations of the entity, e_l
    representation = _triples_set_representation(graph, entity)

    # P(e_l | theta_X) = sum(tr in X) P(e_l|tr) * P(tr|theta_X)
    # P(e_l|tr) = 1 if tr in e_l else 0
    # P(tr|theta_X) are in preparsed_data
    final_probability = D(0)
    for tr in preparsed_data.keys():
        if tr in representation:
            final_probability += preparsed_data[tr]

    L.debug('Probability: %s', final_probability)
    return final_probability


def rank(input_data: Query, preparsing_function: PreparsingFunc, retrieval_model: RetrievalModel, graph: PPGraph, entities_to_rank: List[URIRef]) \
        -> Ranking:
    """Rates entities based on provided model and input query.

    Args:
        input_data: query, it is passed to preparsing_function
        preparsing_function: function that takes input_data and returns stuff for retrieval_model
        retrieval_model: function implementing rating
        graph: RDF triples to use
        entities_to_rank: list of entities that should be rated

    Returns:
        Ordered/sorted list containing tuples: (rate, entity),
        best matching entities comes first
    """
    _, examples = input_data
    entities_to_rank_amount = len(entities_to_rank)
    entities_to_rank_progress = max(1, entities_to_rank_amount//10)
    L.info('Ranking %d entities', entities_to_rank_amount)

    # preparse before the loop for efficiency
    preparsed_data = preparsing_function(graph, input_data)
    ranking_score: D

    # do the ranking
    ranking: List[Tuple[D, URIRef]] = []
    for i, entity in enumerate(entities_to_rank):
        if i % entities_to_rank_progress == 0:
            L.info(' ~> ranking entity no %d / %d', i, entities_to_rank_amount)

        # score entity
        ranking_score = retrieval_model(preparsed_data, graph, entity)

        # insert and sort
        bisect.insort_right(ranking, (ranking_score, entity))
        L.debug('-'*20)

    # min/max normalization + best scored first
    max_val = ranking[-1][0]
    min_val = ranking[0][0]
    norm_denominator = max_val - min_val

    # rank examples themselves, for future use in combined approach
    ranking_with_examples = ranking[:]
    for i, entity in enumerate(examples):
        example_ranking = retrieval_model(preparsed_data, graph, entity)
        bisect.insort_right(ranking_with_examples, (example_ranking, entity))
    ranking_with_examples = ranking_with_examples[::-1]

    retrived_with_examples: List[bool] = []
    count_found_examples = 0
    for _, entity in ranking_with_examples:
        # assumed amount of relevant entities
        if count_found_examples == 10:
            break

        if entity in examples:
            count_found_examples += 1
            retrived_with_examples.append(True)
        else:
            retrived_with_examples.append(False)

    # average precision
    ap = statistical_stats(retrived_with_examples)['AvgPrec']

    L.info(" ~> normalization min = %s, max = %s", min_val, max_val)
    L.info(" ~> AP = %s", ap)
    return ap, [((v - min_val) / norm_denominator, entity) for v, entity in ranking[::-1]]


def rank_text_based(graph: PPGraph, input_data: Query, entities_to_rank: List[URIRef]) -> Ranking:
    """Rates entities based on text-based model and input query.

    Args:
        graph: RDF triples to use
        input_data: relation (topic) and examples
        entities_to_rank: list of entities that should be rated

    Returns:
        Ordered/sorted list containing tuples: (rate, entity),
        best matching entities comes first
    """
    return rank(input_data, _text_preparsing, _text_retrieval_model, graph, entities_to_rank)


def rank_examples_based(graph: PPGraph, input_data: Query, entities_to_rank: List[URIRef]) -> Ranking:
    """Rates entities based on example-based (structure) model  and input query.

    Args:
        graph: RDF triples to use
        input_data: relation (topic) and examples
        entities_to_rank: list of entities that should be rated

    Returns:
        Ordered/sorted list containing tuples: (rate, entity),
        best matching entities comes first
    """
    return rank(input_data, _examples_preparsing, _example_retrieval_model, graph, entities_to_rank)


def rank_combined(rankings: Tuple[Ranking, Ranking]) -> Ranking:
    lambda_param = D('0.5')
    delta_param = D('0.1')

    combined_ranking: DefaultDict[URIRef, D] = defaultdict(D)

    ranking_text, ranking_example = rankings
    ap_example, ranking_example_data = ranking_example
    ap_text, ranking_text_data = ranking_text
    overlap = min(ap_example, ap_text) / max(ap_example, ap_text)

    L.info("Overlap = %s", overlap)

    if overlap < delta_param and ap_example > ap_text:
        return ap_example, ranking_example_data

    elif overlap < delta_param and ap_example < ap_text:
        return ap_text, ranking_text_data

    else:
        for v, entity in ranking_example_data:
            combined_ranking[entity] += v * lambda_param

        for v, entity in ranking_text_data:
            combined_ranking[entity] += v * (1 - lambda_param)

        return D(1), [(v, k) for k, v in sorted(combined_ranking.items(), key=lambda item: item[1], reverse=True)]
