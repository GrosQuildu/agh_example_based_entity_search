#!/bin/bash

for sample_file in pp_data/*.yml; do
    data_file=${sample_file/.yml/.nq}
    if [ -f $data_file ]; then
        echo "File $data_file already exists, skipping"
    else
        echo "Getting data for $sample_file, saving in $data_file"
        python ./example_based_entity_search/dump_data.py $data_file $sample_file relevant
        python ./example_based_entity_search/dump_data.py $data_file $sample_file not_relevant
    fi
done