#!/usr/bin/env bash

# Get this script file path
# and set working directory to ../../, so if the script is run from
# sources directory, and the packages are loaded correctly
# In the case of github actions, dirname will return the root of the repo,
# so in the yml config file for the ghithub action, we set the working directory to sources
# and there is no need to change it here.
if [[ -z "${GITHUB_ACTIONS}" ]]; then
  cd "$(dirname "$0")"
  cd ../../
fi

# pytest only adds to sys.path directories where test files are
# so we add the sources directory
export PYTHONPATH=.

if [ "${LOCAL_IMAGE_NAME}" == "" ]; then
  #LOCAL_TAG=`date +"%Y-%m-%d-%H-%M"`
  LOCAL_TAG="latest"
  export LOCAL_IMAGE_NAME="chicago-taxi:${LOCAL_TAG}"
  echo "LOCAL_IMAGE_NAME is not set, building a new image with tag ${LOCAL_IMAGE_NAME}"
  docker build -t ${LOCAL_IMAGE_NAME} ./production
else
  echo "no need to build image ${LOCAL_IMAGE_NAME}"
fi

export LOCAL_MODEL_LOCATION="./tests/model"

docker-compose --project-directory ./tests/integration_tests up -d

sleep 1

pipenv run pytest ./tests/integration_tests -s

ERROR_CODE=$?

if [ ${ERROR_CODE} != 0 ]; then
    docker-compose --project-directory ./tests/integration_tests logs
    docker-compose --project-directory ./tests/integration_tests down --volumes
    exit ${ERROR_CODE}
fi

docker-compose --project-directory ./tests/integration_tests down --volumes

# Run test lambda + ECR
#  Create local ecr + lambda + image in ecr
# Run test_api_gateway?
