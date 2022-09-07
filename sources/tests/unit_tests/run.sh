#!/usr/bin/env bash

# Get this script file path
# and set working directory to ../../, so if the script is run from
# sources directory, and the packages are loaded correctly
# In the case of github actions, dirname will return the root of the repo,
# so in the yml config file for the ghithub action, we set the working directory to sources
# and there is no need to change it here.

if [[ -z "${GITHUB_ACTIONS}" ]]; then
  cd "$(dirname "$0")"
  cd ../..
fi

# pytest only adds to sys.path directories where test files are
# so we add the sources directory
export PYTHONPATH=.

pipenv run pytest ./tests/unit_tests -s
