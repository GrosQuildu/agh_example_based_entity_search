#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='example based entity search',
    version='1.0',
    packages=find_packages(),
    description='Implementation of "Example Based Entity Search in the Web of Data"',
    url='https://github.com/GrosQuildu/example_based_entity_search',
    author='Paweł Płatek',
    author_email='e2.8a.95@gmail.com',
    install_requires=['PyYAML', 'requests', 'rdflib'],
    extras_require={
        'dev': ['isort', 'mypy', 'pyflakes', 'autopep8']
    },
    entry_points={
        'console_scripts': [
            'ebes-data = example_based_entity_search.dump_data:main',
            'ebes-rank = example_based_entity_search.entity_search_tool:main'
        ]
    }
)