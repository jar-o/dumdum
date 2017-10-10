#!/usr/bin/env bash

# Simple build and upload script for PyPI

head -n 2 bin/dumdum > bin/dumdum.t && \
    cat dumdum.py >> bin/dumdum.t && \
    mv bin/dumdum.t bin/dumdum

rm -fr dist

# NOTE these require that you're already setup on PyPI, with ~/.pypirc etc
python setup.py sdist
twine upload "dist/`ls dist`"


