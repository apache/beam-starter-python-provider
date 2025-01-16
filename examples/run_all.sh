#!/bin/bash

set -e

# Create the package that we reference as a dependency.
(cd .. && poetry build)

# Run the pipelines one by one.

python -m apache_beam.yaml.main --yaml_pipeline_file=./simple.yaml

python -m apache_beam.yaml.main --yaml_pipeline_file=./error_handling.yaml

python -m apache_beam.yaml.main --yaml_pipeline_file=./with_config.yaml

python -m apache_beam.yaml.main --yaml_pipeline_file=./multi_input_output.yaml

echo "All pipelines ran successfully."
