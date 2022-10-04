#!/usr/bin/env bash

# Use with ./setup_dev_windows_gitbash.sh
# Note that this script exports the env var from Terraform with the eval command
# and then executes pipenv, so these env vars are still in the virtual environment.
# After the environment exits these vars will not exist. If you need them to persist,
# use source ./setup_dev_windows_gitbash.sh

# Use python.exe and not python. Otherwise error "stdout is not a tty" will raise
cd ./infrastructure/deployment
./terraform.exe init
eval $(python.exe export_output.py terraform.exe)
cd ../..
cd sources

CURRENT_PATH="."
if [ -d $CURRENT_PATH ] && [[ ":$PYTHONPATH:" != *":$CURRENT_PATH:"* ]]; then
    PYTHONPATH="${PYTHONPATH:+"$PYTHONPATH:"}$CURRENT_PATH"
fi

prefect.exe config set PREFECT_API_URL="http://$PREFECT_EXTERNAL_IP:8080/api"
pipenv shell
