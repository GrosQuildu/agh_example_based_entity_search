#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
~Paweł Płatek
'''

import logging
from decimal import Decimal as D

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

# extensions to look for when loading triples from dir
TRIPLE_FILE_EXTENSIONS = ['nq', 'rdf']
URI_PREFIX = 'http://dbpedia.org/resource/'  # prepend that in interactive shell
SPARQL_ENDPOINT = 'http://dbpedia.org/sparql'  # default endpoint
LANGS = ['en', 'pl', None, '']  # languages for text representation of tripples
D_PREC = D('0.00000')  # precision of floats in logging
EXAMPLES_AMOUNT = 4  # how many relevant entities use as the examples

logging.basicConfig(format='%(message)s')
L = logging.getLogger()
