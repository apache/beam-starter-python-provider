# Apache Beam starter for Python Providers

This provides an example of how to write a catalog of transforms via a provider
in Python that can be used from Beam YAML.

If you want to clone this repository to start your own project,
you can choose the license you prefer and feel free to delete anything
related to the license you are dropping.

## Before you begin

Make sure you have a [Python 3](https://www.python.org/) development environment ready.
If you don't, you can download and install it from the
[Python downloads page](https://www.python.org/downloads/).

This project uses poetry to manage its dependencies, however it can be used
with in any virtual environment where its dependencies (as listed in
pyproject.toml) are installed.

Simple steps to set up your environment using [Poetry](https://python-poetry.org/):

```shell
# Install Poetry if you haven't already
pip install poetry

# Install project dependencies into a virtual environment
poetry install

# Build the Python package containing your PTransforms
# This creates a distributable tarball (e.g., dist/beam_starter_python_provider-*.tar.gz)
# which Beam YAML needs to find your custom transforms.
poetry build

# Activate the virtual environment managed by Poetry
# Alternatively, you can prefix commands with `poetry run`
eval $(poetry env activate)
```

## Overview

Beam YAML transforms can be ordinary Python transforms that are simply
enumerated in a YAML file that indicates where to find them and how
to instantiate them.  This allows one to author arbitrarily complex
transforms in Python and offer them for easy use from within a Beam
YAML pipeline. The main steps that are involved are:

1. Author your PTransforms which accept and produce [schema'd PCollections](https://beam.apache.org/documentation/programming-guide/#schemas).
In practice, this means that the elements are named tuples or `beam.Row` objects.

2. Publish these transforms as a standard Python package.  For local development
   this can be a simple tarball, for production use these can be published
   to pypi or otherwise hosted anywhere else that is accessible to its users.

3. Write a simple yaml file enumerating these transforms, providing both their
   qualified names and the package(s) in which they live.  This file can then
   be referenced from a Beam YAML pipeline  which can then use these transforms.

## This repository

This repository is a complete working example of the above steps.

### PTransform definitions

Several transforms are defined in [my_provider.py](./my_provider.py).
Ordinary unit tests can be found in
[my_provider_test_.py](./my_provider_test.py)
that can be run with pytest.
A real-world example would probably have a more structured format than
putting all transforms in a single top-level python module, but this
is a python package structuring question and would not change anything
essential here.

### Publishing the package

Run `poetry build` to build the package.
This will create the file `dist/beam_starter_python_provider-0.1.0.tar.gz`
which is referenced elsewhere.

### Write the provider listing file

The next step is to write a file that tells Beam YAML how and where to find the
transforms that were defined above.
An example of how to do this is given in
[examples/provider_listing.yaml](examples/provider_listing.yaml).
These listings can also be specified inline with the pipeline definition
as done in [examples/simple.yaml](examples/simple.yaml).

### Use the transforms

The [examples](./examples/) directory contains several examples of how to invoke the provided transforms from Beam YAML.
The script at [examples/run_all.sh](./examples/run_all.sh) shows how they can be run locally.

**Running Locally:**

Make sure you have activated your virtual environment.

```shell
cd examples./simple.yaml
```

**Running with Dataflow:**

You will need a Google Cloud project and a GCS bucket for staging.

* **Using `gcloud`:** (Requires gcloud CLI installed and configured)

    Replace `<YOUR_PROJECT_ID>` and `<YOUR_REGION>` with your details.

```shell
cd examples
gcloud dataflow yaml run my-yaml-job \
  --yaml-pipeline-file=./simple.yaml \
  --project=<YOUR_PROJECT_ID> \
  --region=<YOUR_REGION>
```

* **Using `python -m apache_beam.yaml.main`:**

    Replace `<YOUR_PROJECT_ID>`, `<YOUR_REGION>`, and `<YOUR_GCS_BUCKET>` with your details.

```shell
cd examples
python -m apache_beam.yaml.main \
  --yaml_pipeline_file=./simple.yaml \
  --runner=DataflowRunner \
  --project=<YOUR_PROJECT_ID> \
  --region=<YOUR_REGION> \
  --temp_location=gs://<YOUR_GCS_BUCKET>/temp \
  --staging_location=gs://<YOUR_GCS_BUCKET>/staging
```
