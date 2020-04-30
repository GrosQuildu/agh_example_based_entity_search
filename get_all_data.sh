#!/bin/bash

for sampel_file in pp_data/*.yml; do
    data_file=${sampel_file/.yml/.nq}
    if [ -f $data_file ]; then
        echo "File $data_file already exists, skipping"
    else
        python ./example_based_entity_search/dump_data.py -v $data_file $sampel_file relevant
        python ./example_based_entity_search/dump_data.py -v $data_file $sampel_file not_relevant
    fi
done