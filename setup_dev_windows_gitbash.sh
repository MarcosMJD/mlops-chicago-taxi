#!/usr/bin/env bash

# Use python.exe and not python. Otherwise error "stdout is not a tty" will raise
cd ./infrastructure/deployment
eval $(python.exe export_output.py terraform.exe)
prefect config set PREFECT_API_URL="http://$PREFECT_EXTERNAL_IP:8080/api"
cd ../..
cd sources

CURRENT_PATH="."
if [ -d $CURRENT_PATH ] && [[ ":$PYTHONPATH:" != *":$CURRENT_PATH:"* ]]; then
    PYTHONPATH="${PYTHONPATH:+"$PYTHONPATH:"}$CURRENT_PATH"
fi

pipenv shell
cd ..
