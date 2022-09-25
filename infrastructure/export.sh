#!/usr/bin/env bash

# Use: source export.sh
eval $(python.exe export_output.py)
prefect config set PREFECT_API_URL="http://${PREFECT_EXTERNAL_IP}:8080/api"
