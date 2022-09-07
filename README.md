# mlops-taxi-prediction

## Requirements in the developer machine

- Python 3.9 (recommend to install Anaconda)
- Docker
- Git Bash
- Ggithub account with aws secrets set-up in the repository
- docker-compose

- AWS account and tools

  - AWS account with permissions to create infrastructure
  - AWS access key (id and secret)
  - AWS cli: Download and install AWS cli
    - https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
    - Windows
      ```
      msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
      aws --version
      aws-cli/2.4.24 Python/3.8.8 Windows/10 exe/AMD64 prompt/off
      ```
  - Terraform
    - Download Terraform executable: https://www.terraform.io/downloads
    - Save it to ./infrastructure directory

## Setup

  - AWS cli
      ````bash
      aws configure
      AWS Access Key ID [None]: [your aws key id]
      AWS Secret Access Key [None]: [your asw secret access key]
      Default region name [None]: eu-west-1
      Default output format [None]:
      aws sts get-caller-identity
      ```

  - Create terraform backend bucket to keep Terraform state
    Note: bucket names shall be unique. Choose your location accordingly.
    Note: bucket is private, objects  but anyone with appropriate permissions can grant public access to objects.
    ```bash
    aws s3api create-bucket --bucket [your bucket name] --create-bucket-configuration LocationConstraint=eu-west-1
    ```

### Fork and clone repo

Go to:
- https://github.com/MarcosMJD/mlops-chicago-taxi

And fork the repo
Then clone the forked repo

### Infrastructure

Build staging infrastructure

Edit main.tf file in infrastructure directory and modify
  backend "s3" {
    bucket  = "chicago-taxi-tfstate-mmjd" <- Use your own bucket name
to use that created previously

Required: Use Big Bash in this step

cd infrastructure
./terraform.exe init
terraform plan --var-file=stg.tfvars
terraform apply
yes

### Dependencies

Go to sources directory and run:

pip install --upgrade pip
pip install pipenv
pipenv install --dev
pipenv shell

### Pre-commit hooks
Go to the root directory of the repo and run

pre-commit install
git add .pre-commit-config.yaml

This last step is needed because .git folder is not cloned and pre-commits live there

## Access to servers

From the Terraform output, get the ips of the servers and run:

prefect config set PREFECT_API_URL="http://<external-ip>:8080/api"
export MLFLOW_TRACKING_URI="http://<external-ip>:8080"

## ML project cifecycle

### Developing
Use jupyter notebook to evaluate models
Trainning
Experiment tracking
Model registry

### ML pipeline
Run trainning_pipeline.py to evaluate models
Trainning
Experiment tracking
Model registry

### Deployment
Use CI/CD to deploy new model. E.g. changing the run_id

### Monitoring

## Continue
Set env vars to lambda so that CI/CD is used


Use mlflow model registry to get stg model
If no model, then use dummy model
Or... ff no experiment/run_id in mlflow, then create and use a dummy model

## ToDo

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
- Check why aws config initialization fails when github actions if profile default is set in main.tf
- Deployment en Makefile?
- In dev system... maybe script:
  - Set mlflow env var for the server
  - Set prefect to use prefect server api
  - Modify model and preprocessor to use pipeline or model
  - ignore files in prefect
  - Unit test lambda is loading S3 model actually. Find a way to avoid this.

Bugs

Continue

- Quality checks
- Test localstack aws gateway + ECR + lambda + S3
- CD
- ?



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

Create a default precommit hook:
  pre-commit sample-config > .pre-commit-config.yaml
  pre-commit install
  git add .pre-commit-config.yaml

Pytest only adds to sys.path directories where test files are, so you need to add the sources directory with:
export PYTHONPATH=. fro sources directory

You alternatively can run (not checked)
python -m pytest

## Docker-compose
Stop services only
docker-compose stop

Stop and remove containers, networks..
docker-compose down

Down and remove volumes
docker-compose down --volumes

Down and remove images
docker-compose down --rmi <all|local>
