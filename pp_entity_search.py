#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
~Paweł Płatek
'''


import bisect
import logging

from rdflib import Graph, ConjunctiveGraph, URIRef, Literal, RDF
from rdflib.util import guess_format
from rdflib.term import BNode


L = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s')


def normalize(text):
    return str(text).lower().split()


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
        graph(Graph or ConjunctiveGraph)
        entity(URIRef)

    Returns:
        dict(class_name:list(list(str)))
            keys are: attributes, types, links
            values are lists of rdf labels as a list of strings 
    """
    L.debug('Computing text representation of %s', entity)

    # sanity checks
    assert isinstance(graph, Graph), 'graph is not Graph'
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # use this URIs for types
    type_uris = (RDF.type, URIRef('http://www.w3.org/2004/02/skos/core#subject'),
                    URIRef('http://purl.org/dc/elements/1.1/subject'))

    # store triples in sets
    attributes, types, links = list(), list(), list()
    entities_without_label = 0

    # iterate over all triples with the entity as the subject
    for triple_predicate, triple_object in graph.predicate_objects(entity):
        if isinstance(triple_object, Literal):
            attributes.append(normalize(triple_object))
        else:
            triple_object_text = normalize(graph.label(triple_object))
            if len(triple_object_text) == 0:
                entities_without_label += 1
                continue

            if triple_predicate in type_uris:
                types.append(triple_object_text)
            else:
                links.append(triple_object_text)

    result = {
        'attributes': attributes,
        'types': types,
        'links': links
    }
    L.debug('%d skipped, because of missing label', entities_without_label)
    L.debug('Found: %s, %s, %s',
                *[' '.join([str(len(cs)), cs_name]) for cs_name, cs in result.items()])
    return result


def text_retrieval_model_params(graph):
    # Dirichlet smoothed model of the entire collection of triples
    # D = node text representation
    # theta_c = collection of nodes
    # P(t|theta_c) == sum(D in theta_c)tf(t,D) / sum(D in theta_c)|D|
    probability_collection_denominator = 0
    for node in graph.all_nodes():
        if isinstance(node, Literal):
            triple_object_text = node
        else:
            triple_object_text = graph.label(node)
        probability_collection_denominator += len(normalize(triple_object_text))

    return probability_collection_denominator


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
        graph(Graph or ConjunctiveGraph)
        entity(URIRef)

    Returns:
        probability(float)
    """
    L.debug('Computing text-based probability for %s', entity)

    # normalize query
    relation = normalize(relation)

    # get text representations of the entity
    representations = text_representation(graph, entity)

    # precompute number of terms
    representations_lengths = {cs_name: sum(map(len, cs)) for
                                cs_name, cs in representations.items()}
    L.debug('Terms amount: %s, %s, %s',
                *[' '.join([str(v), 'terms in', k]) for k,v in representations_lengths.items()])

    # precompute model parameters
    probability_collection_denominator = text_retrieval_model_params(graph)

    # pseudo-counts or equivalent sample size
    ni = len(relation)

    # P(t|theta_c), it should depend on term t
    # but assume it is 1/ni, according to (4), page 182
    probability_collection = 1. / ni

    # this are experimental 
    representation_weights = {
        'attributes': 0.3,
        'types': 0.3,
        'links': 0.3
    }

    # P(R | theta_e) == product(t in R) P(t | theta_w_e)
    final_probability = 1
    for t in relation:
        L.debug('%s-> processing term %s', ' '*4, repr(t))

        # P(t | theta_w_e) == sum(cs in representations) P(t | theta_cs_e) * P(cs)
        term_probability = 0
        for cs_name, cs in representations.items():
            L.debug('%s-> estimating probability for %s', ' '*8, cs_name)

            # tf(t,e) is the term frequency of t in the representation document of e
            # http://mlwiki.org/index.php/TF-IDF#Term_Frequency
            tf = sum([one_label.count(t) for one_label in cs])

            # P(t|theta_c) == sum(D in theta_c)tf(t,D) / sum(D in theta_c)|D|
            # probability_collection_nominator = 0
            # for node in graph.all_nodes():
            #     if isinstance(node, Literal):
            #         triple_object_text = node
            #     else:
            #         triple_object_text = graph.label(node)
            #     probability_collection_nominator += normalize(triple_object_text).count(t)
            # probability_collection = float(probability_collection_nominator) / probability_collection_denominator

            # P(t | theta_cs_e) == [tf(t,e) + ni*P(t|theta_c)] / [|e| + ni]
            representation_probability = float(tf + ni*probability_collection) 
            representation_probability /= representations_lengths[cs_name] + ni
            L.debug('%s-> %f', ' '*8, representation_probability)

            # do the addition
            term_probability += representation_probability * representation_weights[cs_name]

        L.debug('%s-> probability: %f', ' '*4, term_probability)
        # do the multiplication
        final_probability *= term_probability

    L.debug('Probability: %f', final_probability)
    return final_probability


def test_text_approach():
    filename = './tmp.nq'
    graph = ConjunctiveGraph()
    graph.parse(filename, format=guess_format(filename))

    relation = 'hacker mitnick journalist'
    qres = graph.query( 
            '''SELECT DISTINCT ?s 
               WHERE { 
                  ?s ?p ?o 
               }''')
    L.info('Will rank %d entities', len(qres))

    ranking = []
    # for entity,_,_ in graph.triples((URIRef('http://dbpedia.org/resource/John_Markoff'),None,None)):
    for entity in qres:
        entity = entity[0]
        if not isinstance(entity, URIRef):
            continue

        rank = text_retrieval_model(relation, graph, entity)
        bisect.insort_right(ranking, (rank, entity))
        print(f'Rank for {entity}: {rank}')
        # break

    print('-'*30)
    print('Best matches:')
    for rank, entity in ranking[-20:][::-1]:
        print(f'{entity} - {rank}')


def main():
    pass


if __name__ == '__main__':
    L.setLevel('INFO')
    # main()
    test_text_approach()
