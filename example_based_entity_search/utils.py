#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utilities for RDF handling.

    Author: Paweł Płatek
"""

from decimal import Decimal as D
from glob import glob
from os.path import isdir, isfile
from random import shuffle
from typing import Dict, List, Optional, Tuple

from rdflib import RDF, RDFS, BNode, ConjunctiveGraph, Graph, Literal, URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from rdflib.util import guess_format
from yaml import YAMLError, safe_load

from example_based_entity_search.config import (EXAMPLES_AMOUNT, LANGS,
                                                PREFIXES, SPARQL_ENDPOINT,
                                                TRIPLE_FILE_EXTENSIONS, L)


class PPGraph:
    """Uniform interface for rdflib.Graph and rdflib.SPARQLStore."""

    def __init__(self, store):
        supported_backends = [SPARQLStore, Graph, ConjunctiveGraph]
        assert any(
            [isinstance(store, backend) for backend in supported_backends]), store
        self.store = store
        self._size = None  # lazy binding

    def __getattr__(self, name):
        attr = getattr(self.store, name, None)
        if attr is not None:
            return attr

    def triples(self, *args, **kwargs):
        """Lame but SPARQLStore returns different stuff than Graph."""

        def check_triple(tr):
            if isinstance(tr[0], BNode) or isinstance(tr[2], BNode):
                return False
            if isinstance(tr[2], Literal) and tr[2].language not in LANGS:
                return False
            return True

        if isinstance(self.store, SPARQLStore):
            for tr, _ in self.store.triples(*args, **kwargs):
                if not check_triple(tr):
                    continue
                yield tr
        else:
            for tr in self.store.triples(*args, **kwargs):
                if not check_triple(tr):
                    continue
                yield tr

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
            for the_lang in LANGS:
                label = self.__getattr__('preferredLabel')(
                    entity, lang=the_lang)
                if label:
                    return label

        elif self.__getattr__('label') is not None:
            return self.__getattr__('label')(entity)

        else:
            for label in self.objects(entity, RDFS.label):
                if label.language in LANGS:
                    return label

    def parse(self, *args, **kwargs):
        if isinstance(self.store, SPARQLStore):
            L.warning(
                'Switching PPGraph backend from remote endpoint to local files')
            self.store = ConjunctiveGraph()
        self._size = None  # will need to recompute that
        return self.store.parse(*args, **kwargs)

    @property
    def size(self):
        if isinstance(self.store, SPARQLStore):
            return 13370  # just something big

        if self._size:
            return self._size

        results = self.store.query(PREFIXES + '''SELECT (count(?s) as ?X) 
                       WHERE {  
                          ?s ?p ?o . 
                       }''')
        self._size = list(results)[0][0].value
        return self._size


def load_data(data_url: str, old_graph: Optional[PPGraph] = None) -> PPGraph:
    """Create new PPGraph or add triples to the provided one.

    Args:
        data_url: path to RDF file or url address of SPARQL endpoint,
                    passing an url will invalidate old_graph
        old_graph: existing graph, will add triples to it

    Returns:
        Graph with triples loaded from data_url (lazy loaded in case of SPARQL endpoint)
    """
    if old_graph:
        graph = old_graph
    else:
        graph = PPGraph(ConjunctiveGraph())

    if isfile(data_url):
        L.info('Loading triples from file `%s`', data_url)
        data_format = guess_format(data_url)
        graph.parse(data_url, format=data_format)

    elif isdir(data_url):
        L.info('Loading triples from files in directory `%s`', data_url)
        for extension in TRIPLE_FILE_EXTENSIONS:
            triples_files = glob(f'{data_url}/*.{extension}')
            if len(triples_files) > 0:
                L.info('Found %d `.%s` files', len(triples_files), extension)

            for i, triples_file in enumerate(triples_files):
                data_format = guess_format(triples_file)
                L.debug('%d / %d (`%s`), data format: %s', i, len(triples_files),
                        triples_file, data_format)
                graph.parse(triples_file, format=data_format)

    else:
        L.info('Using remote graph from SPARQL endpoint `%s`', data_url)
        graph = PPGraph(SPARQLStore(data_url))

        # early fail
        try:
            graph.query('''SELECT DISTINCT ?s 
                   WHERE { 
                      ?s rdf:type foaf:Person
                   } LIMIT 1''')
        except Exception as e:
            L.error("Can't load data from remote endpoint")
            raise e

    return graph


def test_ppgraph(data_urls: List[str]):
    for data_url in data_urls:
        L.info('Test with %s', data_url)
        graph = load_data(data_url)

        # can query
        results = graph.query(PREFIXES + '''SELECT DISTINCT ?s 
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
            assert isinstance(p, URIRef) or isinstance(
                p, Literal) or isinstance(p, BNode)
            assert isinstance(o, URIRef) or isinstance(
                o, Literal) or isinstance(o, BNode)


def data_from_sample_file(sample_file: str) -> \
        Tuple[str, List[URIRef], List[URIRef], List[URIRef]]:
    """Parses sample file"""
    L.info('Preparing ranking for sample file `%s`', sample_file)

    if not isfile(sample_file):
        L.error('File `%s` do not exists, aborting!', sample_file)
        raise SyntaxError

    try:
        with open(sample_file, 'r', encoding='utf8') as f:
            sample_data = safe_load(f)
    except (UnicodeDecodeError, YAMLError) as e:
        L.error('Error loading sample file `%s`: %s', sample_file, e)
        raise SyntaxError

    if not isinstance(sample_data, dict):
        L.error('Sample data must be dictionary!')
        raise SyntaxError

    for required_key in ['topic', 'relevant', 'not_relevant']:
        if required_key not in sample_data.keys():
            L.error('`%s` key not found in sample data', required_key)
            raise SyntaxError

    # convert strings to URIRefs and prepare data
    relevant = list(map(URIRef, sample_data['relevant']))
    not_relevant = list(map(URIRef, sample_data['not_relevant']))

    if len(relevant) == 0:
        L.error('No relevant entities specified in the sample data')
        raise SyntaxError

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
            'There is only %d relevant entities in sample data `%s`, trimming amount of examples', len(relevant), sample_file)

    # select random examples from relevant entities
    if random_examples:
        shuffle(relevant)

    # prepare entities
    examples = relevant[:examples_amount]
    relevant = relevant[examples_amount:]
    entities_to_rank = relevant[:] + not_relevant[:]

    return sample_data['topic'], examples, entities_to_rank, relevant


def statistical_stats(retrived: List[bool]) -> Dict[str, D]:
    """Compute various evaluation measures."""
    # A measure of the ability of a system to present only relevant items
    r_precision = D(sum(retrived)) / len(retrived)
    avg_prec = D(0)

    if len(retrived) != 0:
        relevant_so_far = D(0)
        for i, is_relevant in enumerate(retrived, 1):
            if is_relevant:
                relevant_so_far += 1
                avg_prec += relevant_so_far / i
        avg_prec /= len(retrived)

    return {'R-Precision': r_precision, 'AvgPrec': avg_prec}


if __name__ == '__main__':
    L.setLevel('DEBUG')
    L.info('Running utils.py tests')

    # remote
    data_urls_to_test = [SPARQL_ENDPOINT]

    # one file
    local_files = glob('./pp_data/*.nq')
    if local_files:
        data_urls_to_test.append(local_files[0])

    # all files in a directory
    data_urls_to_test.append('./pp_data/')

    test_ppgraph(data_urls_to_test)
    L.info('Passed')
