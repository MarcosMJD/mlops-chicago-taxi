#!/usr/bin/env bash

# Use: ./setup_dev_linux.sh
# Note that there is no need for source ./setup_dev_linux.sh.
# Because we export the vars in this shell
# and then launch the venv shell with those vars.
# So when we exit the venv, this script will end
# and the vars will not be there.

# If we use source ./setup_dev_linux.sh, the vars will be
# created in the same shell (no new shell is started when using source)
# so when we exit the venv, the vars will be there.

cd ./infrastructure/deployment
terraform init
eval $(python export_output.py terraform)
cd ../..
cd sources

CURRENT_PATH="."
if [ -d $CURRENT_PATH ] && [[ ":$PYTHONPATH:" != *":$CURRENT_PATH:"* ]]; then
    export PYTHONPATH="${PYTHONPATH:+"$PYTHONPATH:"}$CURRENT_PATH"
fi

# At this point, we do not have prefect. After pipenv shell, yes we have it
pipenv shell prefect config set PREFECT_API_URL="http://$PREFECT_EXTERNAL_IP:8080/api"
