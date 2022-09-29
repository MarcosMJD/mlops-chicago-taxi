#!/usr/bin/env bash

cd ./infrastructure/deployment
terraform init
eval $(python export_output.py terraform)
prefect config set PREFECT_API_URL="http://$PREFECT_EXTERNAL_IP:8080/api"
cd ../..
cd sources

CURRENT_PATH="."
if [ -d $CURRENT_PATH ] && [[ ":$PYTHONPATH:" != *":$CURRENT_PATH:"* ]]; then
    PYTHONPATH="${PYTHONPATH:+"$PYTHONPATH:"}$CURRENT_PATH"
fi

pipenv shell
cd ..
