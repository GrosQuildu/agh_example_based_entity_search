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
from example_based_entity_search.utils import PPGraph

Triple = Tuple[Union[None, URIRef], URIRef, Union[URIRef, Literal]]
RetrievalModel = Callable[[Any, PPGraph, URIRef], D]


def normalize(text):
    return str(text).lower()


def text_representation(graph: PPGraph, entity: URIRef) -> Dict[str, Dict[str, int]]:
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

        for o in normalize(value_to_use).split():
            cs_to_use[o] += 1

        if all([sum(cs.values()) >= threshold for cs in [attributes, types, links]]):
            break

    result = {
        'attributes': dict(attributes),
        'types': dict(types),
        'links': dict(links)
    }
    if entities_without_label > 0:
        L.debug('%d skipped, because of missing label', entities_without_label)
    L.debug('Found: %s, %s, %s',
            *[' '.join([str(sum(cs.values())), 'terms in', cs_name]) for cs_name, cs in result.items()])
    return result


def text_retrieval_model(relation: str, graph: PPGraph, entity: URIRef) -> D:
    """Rates entity represented as text.

    Rate is equal to the probability of the entity being relevant to the relation.
    Probability formula is based on a language modeling approach.

    Dirichlet model computation is based on:
        http://mlwiki.org/index.php/Smoothing_for_Language_Models#Dirichlet_Prior_Smoothing
        https://www.coursera.org/lecture/text-retrieval/lesson-4-6-smoothing-methods-part-1-kM6Ie
        http://ciir.cs.umass.edu/pubfiles/ir-445.pdf
        (4) http://profsite.um.ac.ir/~monsefi/machine-learning/pdf/Machine-Learning-Tom-Mitchell.pdf

    Args:
        relation: plain text query describing entities we are looking for
        graph: RDF triples to use (graph represents whole word we know about)
        entity: RDF entity to rank

    Returns:
        Probability
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
            #     probability_collection_nominator += normalize(triple_object_text).count(t)
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
def triples_set_representation(graph: PPGraph, entity: URIRef) -> Set[Triple]:
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


def examples_preparsing(graph, examples):
    """Convert example entities to Most of the final probability depends only on examples.

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

    L.debug('-' * 20)
    return P_examples


def example_retrieval_model(P_examples: Dict[Triple, D], graph: PPGraph, entity: URIRef):
    """Rates entity represented as set of triples.

    Rate is based on the similarity of sets.

    Args:
        P_examples: preparsed example entities
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


def rank(retrieval_model: RetrievalModel, input_data: Any, graph: PPGraph, entities_to_rank: List[URIRef]) \
        -> List[Tuple[D, URIRef]]:
    """Rates entities based on provided model and input query.

    Args:
        retrieval_model: function implementing rating function
        input_data: something to rate, it is passed to retrieval_model function as first argument
        graph: RDF triples to use
        entities_to_rank: list of entities that should be rated

    Returns:
        Ordered/sorted list containing tuples: (rate, entity),
        best matching entities comes first
    """
    entities_to_rank_amount = len(entities_to_rank)
    entities_to_rank_progress = max(1, entities_to_rank_amount//10)
    L.info('Ranking %d entities', entities_to_rank_amount)

    ranking: List[Tuple[D, URIRef]] = []
    for i, entity in enumerate(entities_to_rank):
        if i % entities_to_rank_progress == 0:
            L.info(' ~> ranking entity no %d / %d', i, entities_to_rank_amount)
        ranking_score = retrieval_model(input_data, graph, entity)
        bisect.insort_right(ranking, (ranking_score, entity))
        L.debug('-'*20)

    # best scored first
    ranking = ranking[::-1]
    return ranking
