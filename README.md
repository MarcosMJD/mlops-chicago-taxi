# mlops-taxi-prediction

prefect config set PREFECT_API_URL="http://<external-ip>:8080/api" Maybe can be done programmatically?
export MLFLOW_TRACKING_URI="http://54.74.157.93:8080"

Note:
After git clone
...After pipenv install --dev... (also pipenv shell?)
... we must run pre-commit install, because .git folder is not cloned


ToDo

- Use pipelines or save dv as an artifact
- Manage passwords (e.g. database) in aws
  - mlflo https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/setup-credentials.html
- Make user_data persistent, so that after reboot the ec2, it still works
- Check lib versions in pipfiles
- Use logging in prefect
- Use S3 to store datasets
- Check no cache when using pipenv in Dockerfile
- Improve paths in the tests. Use current python script file to import other modules,
  Similar to .sh files.
- In dev system... maybe script:
  - Set mlflow env var for the server
  - Set prefect to use prefect server api
  - Modify model and preprocessor to use pipeline or model
  - ignore files in prefect
  - Unit test lambda is loading S3 model actually. Find a way to avoid this.

Bugs
- Terraform state file not created in S3 backend.
- Terraform output not working


Continue

- Quality checks
- Test localstack aws gateway + ECR + lambda + S3
- git-hooks pre-commit
- Terraform. Set env vars to be used in lambda images
- CI
- CD
- Deployment en Makefile?

Notes

T

## Usefull commands and snippets

### Shell script

Header of a sh script
"#!/usr/bin/env bash"

Returns the directory where the Bash script file is saved
"$(dirname "$0")"

Get last error code
ERROR_CODE=$?

### Prefect
o create programmatically an storage block in prefect:
from prefect.filesystems import S3
block = S3(bucket_path="chicago-taxi-fc4rdz8d")
block.save("example-block")

Then to build a deployment
prefect deployment build trainning_pipeline.py:main_flow --name test --tag test --storage-block s3/example-block -q test
This will upload the .py files to S3 bucket

Or with object:

To create the deployment and queue (in prefect orion server), and also upload to S3 the yaml file:
prefect deployment apply .\main_flow-deployment.yaml

To start an agent
prefect agent start -q 'test'

To run a flow
prefect deployment run <FLOW_NAME>/<DEPLOYMENT_NAME>

## aws cli and aws-api

Download object from aws s3
aws s3api get-object --bucket stg-chicago-taxi-fc4rdz8d --key mlflow/2/e4ff37b7254a408c86826fb2a25573a9/artifacts/model/conda.yaml ./conda.yaml

Download folder from aws s3
aws s3 cp s3://stg-chicago-taxi-fc4rdz8d/mlflow/2/e4ff37b7254a408c86826fb2a25573a9/artifacts/model ./model --recursive

Get latest RUN_ID from latest S3 partition. In practice, this is generally picked up from a tool like MLflow or a DB

export RUN_ID=$(aws s3api list-objects-v2 --bucket ${MODEL_BUCKET_DEV} \
--query 'sort_by(Contents, &LastModified)[-1].Key' --output=text | cut -f2 -d/)

Copy between buckets
aws s3 sync s3://${MODEL_BUCKET_DEV} s3://${MODEL_BUCKET_PROD}

Update lambda env vars
https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
aws lambda update-function-configuration --function-name ${LAMBDA_FUNCTION} --environment "Variables=${variables}"


## Pre-commit

Create a default precommit hoock:
  pre-commit sample-config > .pre-commit-config.yaml
  pre-commit install
