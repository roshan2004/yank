#!/bin/bash

# Print each line, exit on error
set -ev

# Install the built package
conda create --yes -n docenv python=$CONDA_PY
source activate docenv
conda install -yq --use-local yank-dev sphinx==1.5.6

# We don't use conda for these:
pip install -I sphinx==1.5.6 sphinx_rtd_theme==0.2.4 msmb_theme==1.2.0

# Install doc requirements
conda install -yq --file docs/requirements.txt

# Make docs
cd docs && make html && cd -

# Move the docs into a versioned subdirectory
python devtools/travis-ci/set_doc_version.py

# Prepare versions.json
python devtools/travis-ci/update_versions_json.py