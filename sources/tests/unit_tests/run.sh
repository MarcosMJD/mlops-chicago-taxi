#!/usr/bin/env bash

# Get this script file path
# so if the script is run from parent, we change to the subdirectory

cd "$(dirname "$0")"
cd ..
pipenv run pytest unit_tests 



