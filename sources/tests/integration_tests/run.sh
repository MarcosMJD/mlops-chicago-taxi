#!/usr/bin/env bash

# Get this script file path
# so if the script is run from parent, we change to the subdirectory
cd "$(dirname "$0")"

if [ "${LOCAL_IMAGE_NAME}" == "" ]; then
  #LOCAL_TAG=`date +"%Y-%m-%d-%H-%M"`
  LOCAL_TAG="latest"
  export LOCAL_IMAGE_NAME="chicago-taxi:${LOCAL_TAG}"
  echo "LOCAL_IMAGE_NAME is not set, building a new image with tag ${LOCAL_IMAGE_NAME}"
  docker build -t ${LOCAL_IMAGE_NAME} ../../production
else
  echo "no need to build image ${LOCAL_IMAGE_NAME}" 
fi

export LOCAL_MODEL_LOCATION="../model"

docker-compose up -d

sleep 1

pipenv run pytest ./test_local_lambda_container.py

ERROR_CODE=$?

if [ ${ERROR_CODE} != 0 ]; then
    docker-compose logs
    docker-compose down
    exit ${ERROR_CODE}
fi

docker-compose down

# Run test lambda + ECR
#  Create local ecr + lambda + image in ecr
# Run test_api_gateway?
