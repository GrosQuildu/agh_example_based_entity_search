#!/bin/bash

target='./example_based_entity_search'

echo 'isort fix imports'
isort --recursive --atomic "$target"
echo '-----------------------'

echo 'pyflake errors'
pyflakes "$target"
echo '-----------------------'

echo 'mypy checks'
mypy "$target"
echo '-----------------------'

echo 'autopep8 magic'
autopep8 -r -i "$target"
echo '-----------------------'