#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
~Paweł Płatek
'''


import bisect
from collections import defaultdict
from decimal import Decimal as D
import logging
from os.path import isfile
from yaml import safe_load

from rdflib import Graph, ConjunctiveGraph, URIRef, Literal, BNode, RDF, RDFS
from rdflib.util import guess_format
from rdflib.term import BNode
from rdflib.plugins.stores.sparqlstore import SPARQLStore

PREFIXES = '''PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX : <http://dbpedia.org/resource/>
PREFIX dbpedia2: <http://dbpedia.org/property/>
PREFIX dbpedia: <http://dbpedia.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
'''

LANGS = ['en', '']

D_PREC = D('0.00000')

L = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s')


class PPGraph:
    """
    Wrapper for rdflib.Graph
    To unify SPARQLStore and Graph objects
    """
    def __init__(self, store):
        supported_backends = [SPARQLStore, Graph, ConjunctiveGraph]
        assert any([isinstance(store, backend) for backend in supported_backends])
        self.store = store

    def __getattr__(self, name):
        attr = getattr(self.store, name, None)
        if attr is not None:
            return attr

    def triples(self, *args, **kwargs):
        """Lame but SPARQLStore returns different stuff than Graph"""
        if isinstance(self.store, SPARQLStore):
            for x, _ in self.store.triples(*args, **kwargs):
                yield x
        else:
            for x in self.store.triples(*args, **kwargs):
                yield x

    # copied from graph.py
    def subjects(self, predicate=None, object=None):
        """A generator of subjects with the given predicate and object"""
        for s, p, o in self.triples((None, predicate, object)):
            yield s

    def predicates(self, subject=None, object=None):
        """A generator of predicates with the given subject and object"""
        for s, p, o in self.triples((subject, None, object)):
            yield p

    def objects(self, subject=None, predicate=None):
        """A generator of objects with the given subject and predicate"""
        for s, p, o in self.triples((subject, predicate, None)):
            yield o

    def subject_predicates(self, object=None):
        """A generator of (subject, predicate) tuples for the given object"""
        for s, p, o in self.triples((None, None, object)):
            yield s, p

    def subject_objects(self, predicate=None):
        """A generator of (subject, object) tuples for the given predicate"""
        for s, p, o in self.triples((None, predicate, None)):
            yield s, o

    def predicate_objects(self, subject=None):
        """A generator of (predicate, object) tuples for the given subject"""
        for s, p, o in self.triples((subject, None, None)):
            yield p, o
    # copied end

    def label(self, entity):
        if self.__getattr__('preferredLabel') is not None:
            return self.__getattr__('preferredLabel')(entity, lang=LANGS[0])
        elif self.__getattr__('label') is not None:
            return self.__getattr__('label')(entity)
        else:
            results = self.store.query(PREFIXES+
                    '''SELECT DISTINCT ?l
                       WHERE {{ 
                          {} rdfs:label ?l .
                       }}'''.format(entity.n3()))

            for label in results:
                if label[0].language in LANGS:
                    return label[0].value


def test_ppgraph():
    store = SPARQLStore('http://dbpedia.org/sparql')

    filename = './tmp.nq'
    local_graph = ConjunctiveGraph()
    local_graph.parse(filename, format=guess_format(filename))

    to_test = [store, local_graph]

    for backend in to_test:
        graph = PPGraph(backend)

        # can query
        results = graph.query(PREFIXES+
                '''SELECT DISTINCT ?s 
                   WHERE { 
                      ?s rdf:type foaf:Person
                   } LIMIT 10''')
        assert len(results) == 10

        # triples
        t_subject = URIRef('http://dbpedia.org/resource/John_Markoff')
        t_predicate = RDF.type
        t_object = URIRef('http://dbpedia.org/class/yago/LivingThing100004258')
        for s, p, o in graph.triples((t_subject, t_predicate, t_object)):
            assert s == t_subject
            assert p == t_predicate
            assert o == t_object

        # subject/predicate/object helpers
        for p, o in graph.predicate_objects((t_subject)):
            assert isinstance(p, URIRef) or isinstance(p, Literal) or isinstance(p, BNode)
            assert isinstance(o, URIRef) or isinstance(o, Literal) or isinstance(o, BNode)


def load_data(data_url):
    if isfile(data_url):
        L.info('Loading from local file: "%s"', data_url)
        store = ConjunctiveGraph()
        store.parse(data_url, format=guess_format(data_url))
    else:
        L.info('Loading remote SPARQL endpoint')
        store = SPARQLStore(data_url)
    return PPGraph(store)


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
        graph(Graph or ConjunctiveGraph)
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
    attributes, types, links = defaultdict(int), defaultdict(int), defaultdict(int)
    entities_without_label = 0

    # require only `threshold` objects of all type
    threshold = 999

    # iterate over all triples with the entity as the subject
    for triple_predicate, triple_object in graph.predicate_objects(entity):
        cs_to_use = None
        value_to_use = None

        if isinstance(triple_object, Literal):
            # use only english, should be more efficient method for that
            if triple_object.language not in LANGS:
                continue
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
        graph(Graph or ConjunctiveGraph)
        entity(URIRef)

    Returns:
        probability(float)
    """
    L.debug('Computing text-based probability for %s', entity)

    # sanity checks
    assert isinstance(graph, PPGraph), 'graph is not PPGraph'
    assert isinstance(entity, URIRef), ['entity is not URIRef', entity]

    # normalize query
    relation = normalize(relation).split()

    # get text representations of the entity
    representations = text_representation(graph, entity)

    # precompute number of terms
    representations_lengths = {cs_name: sum(cs.values()) for
                                cs_name, cs in representations.items()}

    # pseudo-counts or equivalent sample size
    ni = len(relation)

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
        'attributes': D('0.33'),
        'types': D('0.33'),
        'links': D('0.33')
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
            term_probability += representation_probability * representation_weights[cs_name]

        L.debug('%s-> term probability: %s', ' '*8, term_probability.quantize(D_PREC))

        # do the multiplication
        final_probability *= term_probability

    L.debug('Probability: %s', final_probability)
    return final_probability


def rank_text_based(graph, relation, entities_to_rank):
    ranking = []
    for entity in entities_to_rank:
        rank = text_retrieval_model(relation, graph, entity)
        bisect.insort_right(ranking, (rank, entity))
        L.debug('-'*20)
        break

    # best scored first
    ranking = ranking[::-1] 

    return ranking


def main():
    data_url = 'http://dbpedia.org/sparql'
    graph = load_data(data_url)

    with open('./pp_data/sample1.yml', 'r') as f:
        sample_data = safe_load(f)

    entities_to_rank = []
    for relevant_URI in sample_data['relevant']:
        entities_to_rank.append(URIRef(relevant_URI))
    for relevant_URI in sample_data['not_relevant']:
        entities_to_rank.append(URIRef(relevant_URI))

    ranking = rank_text_based(graph, sample_data['topic'], entities_to_rank)

    L.info('-'*30)
    L.info('Ranking:')
    for rank, entity in ranking:
        L.info(f'{entity} - {rank}')


if __name__ == '__main__':
    L.setLevel('DEBUG')
    # test_ppgraph()
    main()
