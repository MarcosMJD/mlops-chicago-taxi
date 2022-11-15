# Backend will be at an s3 bucket, that shall be created previously
# E.g. aws s3api create-bucket --bucket [your bucket name] --create-bucket-configuration LocationConstraint=eu-west-1
# Note: bucket names shall be unique. Choose your location accordingly.
# Note: bucket is private, objects but anyone with appropriate permissions can grant public access to objects.

terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket  = "chicago-taxi-tfstate-mmjd"
    key     = "chicago-taxi-stg.tfstate"
    region  = "eu-west-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
  # github actions will fail if profile = "default" is set
  # profile = "default"
}

data "aws_caller_identity" "current_identity" {}

locals {
  account_id      = data.aws_caller_identity.current_identity.account_id
}

data "aws_vpc" "default" {
  default = true
}

data "http" "myip" {
  url = "http://ipv4.icanhazip.com"
}

module "sg_ssh" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "sg_ssh-${var.project_id}"
  description = "Security group for ec2 ssh"
  vpc_id      = data.aws_vpc.default.id

  ingress_cidr_blocks = ["${chomp(data.http.myip.body)}/32"]
  ingress_rules       = ["ssh-tcp"]
}

module "sg_web" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "sg_web-${var.project_id}"
  description = "Security group for ec2_web"
  vpc_id      = data.aws_vpc.default.id

  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["http-80-tcp","http-8080-tcp", "https-443-tcp", "all-icmp"]
  egress_rules        = ["all-all"]
}

module "sg_db" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "sg_db-${var.project_id}"
  description = "Security group for db"
  vpc_id      = data.aws_vpc.default.id

  ingress_with_source_security_group_id = [
    {
      description              = "postgres db access"
      rule                     = "postgresql-tcp"
      source_security_group_id = module.sg_web.security_group_id
    }
  ]
  egress_rules = ["all-all"]
}

# resource "random_string" "suffix" {
#   length  = 8
#   special = false
#   lower   = true
#   upper   = false
# }

# Project bucket
# ${random_string.suffix.result}"

locals {
    s3_bucket_name  = "${var.s3_bucket_name}-${var.project_id_hyphens}-${var.s3_bucket_name_suffix}"
}

module "bucket" {
  source = "./s3"
  s3_bucket_name = local.s3_bucket_name
}

# Postgres Database
# Security credentials shall be managed with a secure storage solution in a real production environment

module "database" {
  source = "./rds"
  rds_indentifier = "postgres-${var.project_id_hyphens}"
  postgres_db_name = var.postgres_db_name
  postgres_db_username = var.postgres_db_username
  postgres_db_password = var.postgres_db_password
  postgres_db_vpc_security_group_ids = [module.sg_db.security_group_id]
}

# MLFlow server
# set -e: exit on error. set -x shows debug... show the command and the output
locals{
  user_data_mlflow_server = trimspace(
<<EOF
#!/bin/bash
set -ex
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo curl -L https://github.com/docker/compose/releases/download/v2.9.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
# Add your staff here. E.g.
# docker run --name some-nginx -p 8080:80 -v ~:/usr/share/nginx/html:ro -d nginx
pip3 install mlflow boto3 psycopg2-binary
mlflow server -h 0.0.0.0 -p 8080  --default-artifact-root s3://${local.s3_bucket_name}/mlflow --backend-store-uri postgresql://${var.postgres_db_username}:${var.postgres_db_password}@${module.database.endpoint}/${var.postgres_db_name}
EOF
)
}
module "ec2_mlflow" {
  source = "./ec2_mlflow"
  user_data = local.user_data_mlflow_server
  key_name = "ec2_key_name_mlflow-${var.project_id}"
  ssh_key_filename = "ec2_ssh_key_mlflow-${var.project_id}.pem"
  security_groups = [
    module.sg_web.security_group_id,
    module.sg_ssh.security_group_id
  ]
  tags = {
    Name = "ec2_server_mlflow-${var.project_id}"
    Project = var.project_id
  }
  ec2_iam_role_name = "ec2_iam_role-${var.project_id}"
  ec2_instance_profile_name = "ec2_instance_profile-${var.project_id}"
  s3_iam_role_policy_name = "s3_iam_role_policy-${var.project_id}"
  s3_bucket_name = local.s3_bucket_name
  postgres_endpoint = module.database.endpoint
  postgres_db_name = var.postgres_db_name
  postgres_db_username = var.postgres_db_username
  postgres_db_password = var.postgres_db_password
}

locals {
  mlflow_tracking_uri = "http://${module.ec2_mlflow.external_ip}:8080"
}

# Prefect Server
# Run prefect in Docker since installation requires sqlite version which is not included in AWS instance
# To analyse, use Postgres instead of sqlite
# Because of an issue wirh CORS when running Prefect in a Docker contanier on AWS EC2, it is needed to
# pass the external api uri to prefect. So we use ec2-metadata to get the value.

locals{
  user_data_prefect_server = trimspace(
<<-EOF
#!/bin/bash
set -ex
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
export PUBLIC_IP=$(ec2-metadata | sed -n "s/^public-ipv4: //p")
docker  run --env PREFECT_ORION_UI_API_URL=http://$PUBLIC_IP:8080/api -p 8080:4200 prefecthq/prefect:2.2-python3.8 prefect orion start --host=0.0.0.0
EOF
)
}

module "ec2_prefect" {
  source = "./ec2_prefect"
  user_data = local.user_data_prefect_server
  key_name = "ec2_key_name_prefect-${var.project_id}"
  ssh_key_filename = "ec2_ssh_key_prefect-${var.project_id}.pem"
  security_groups = [
    module.sg_web.security_group_id,
    module.sg_ssh.security_group_id
  ]
  tags = {
    Name = "ec2_server_prefect-${var.project_id}"
    Project = var.project_id
  }
}

# Development server
# Note: user_data script is executed as root.
# sudo -i -u ubuntu does not work
# $USER, $HOME and cd seems to not work. So Use cd ~

locals{
  user_data_dev_server = trimspace(
<<-EOF
#!/bin/bash

echo "Starting user_data execution"

cd ~

# https://linuxcommand.org/lc3_man_pages/seth.html
# -a: all vars are marked at exportable
# -e Exit immediately if a command exits with a non-zero status.
# -x  Print commands and their arguments as they are executed.

set -ax

# echo -e enables interpretation of escape characters

if ! [ -d ./bin ];
then
    echo -e '\nCreating ~/bin directory\n'
    mkdir -p bin
fi

if ! [  -d ./bin/anaconda3 ]; then
    cd bin
    echo -e '\nInstalling anaconda3...\n'
    echo -e "Downloading anaconda3..."
    wget https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-x86_64.sh -O ./Anaconda3-2022.05-Linux-x86_64.sh
    echo -e "Running anaconda3 script..."
    # -b run install in batch mode (without manual intervention), it is expected the license terms are agreed upon
    # -p install prefix, defaults to $PREFIX, must not contain spaces.
    bash ./Anaconda3-2022.05-Linux-x86_64.sh -b -p ~/bin/anaconda3

    echo -e "Removing anaconda installation script..."
    rm ./Anaconda3-2022.05-Linux-x86_64.sh

    #activate conda
    eval "$(~/bin/anaconda3/bin/conda shell.bash hook)"

    echo -e "Running conda init..."
    conda init
    # Using -y flag to auto-approve
    echo -e "Running conda update..."
    conda update -y conda

    cd ~
else
    echo -e "anaconda already installed."
fi

echo "\nRunning sudo apt-get update...\n"
sudo apt-get update

echo -e "\nInstalling Docker...\n"
sudo apt-get -y install docker.io

echo -e "\nInstalling docker-compose...\n"
cd ~
cd bin
wget https://github.com/docker/compose/releases/download/v2.3.3/docker-compose-linux-x86_64 -O docker-compose
sudo chmod +x docker-compose

echo -e "\nInstalling Terraform...\n"
wget https://releases.hashicorp.com/terraform/1.3.0/terraform_1.3.0_linux_amd64.zip
sudo apt-get install unzip
unzip terraform_1.3.0_linux_amd64.zip
rm terraform_1.3.0_linux_amd64.zip

cd ~

echo -e "\nSetup .bashrc...\n"

echo -e '' >> ~/.bashrc
echo -e "export PATH=~/bin:$PATH" >> ~/.bashrc
echo -e '' >> ~/.bashrc
echo -e 'export PYTHONPATH=".:$PYTHONPATH"' >> ~/.bashrc

echo -e "\nSetting up Docker without sudo setup...\n"
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Specific stuff for the project

echo -e "\nCloning repo\n"
git clone ${var.repo}

cd mlops-chicago-taxi

echo -e "\nPreparing environment\n"
pip install --upgrade pip
pip install pipenv

cd sources
pipenv install --dev

EOF
)
}

module "ec2_dev" {
  source = "./ec2_dev"
  instance_type = "t3.xlarge"
  volume_size = 32
  user_data = local.user_data_dev_server
  key_name = "ec2_key_name_dev-${var.project_id}"
  ssh_key_filename = "ec2_ssh_key_dev-${var.project_id}.pem"
  security_groups = [
    module.sg_web.security_group_id,
    module.sg_ssh.security_group_id
  ]
  tags = {
    Name = "ec2_server_dev-${var.project_id}"
    Project = var.project_id
  }
  ec2_iam_role_name = "ec2_iam_role_dev-${var.project_id}"
  ec2_instance_profile_name = "ec2_instance_profile_dev-${var.project_id}"
  s3_iam_role_policy_name = "s3_iam_role_policy_dev-${var.project_id}"
  s3_bucket_name = local.s3_bucket_name
}


module "ecr" {
  source = "./ecr"
  ecr_repo_name = "${var.ecr_repo_name}-${var.project_id_hyphens}"
  ecr_image_tag = var.ecr_image_tag
  lambda_function_local_path = var.lambda_function_local_path
  model_service_local_path = var.model_service_local_path
  docker_image_local_path = var.docker_image_local_path
  region = var.aws_region
  account_id = local.account_id
}

locals {
  lambda_env_vars = {
    MLFLOW_MODEL_LOCATION = var.mlflow_model_location,
    MLFLOW_BUCKET_NAME = local.s3_bucket_name,
    MLFLOW_BUCKET_FOLDER = "mlflow",
    MLFLOW_EXPERIMENT_ID = var.mlflow_experiment_id,
    MLFLOW_RUN_ID = var.mlflow_run_id,
    MLFLOW_TRACKING_URI = local.mlflow_tracking_uri,
    MLFLOW_MODEL_NAME = var.project_id,
    MLFLOW_MODEL_STAGE = var.mlflow_model_stage
  }
}

module "lambda" {
  source = "./lambda"
  lambda_function_name = "${var.lambda_function_name}-${var.project_id_hyphens}"
  image_uri     = module.ecr.image_uri
  lambda_iam_role_name  = "lambda_iam_role-${var.project_id}"
  lambda_iam_cloudwatch_role_policy_name = "lambda_cloudwatch_iam_policy-${var.project_id}"
  lambda_iam_s3_role_policy_name = "lambda_s3_iam_policy-${var.project_id}"
  lambda_s3_bucket_name = local.s3_bucket_name
  source_arn_api_gateway = module.api_gateway.api_gateway_execution_arn
  lambda_env_vars = local.lambda_env_vars
}

module "api_gateway" {
  source = "./api_gateway"
  api_gateway_name = "${var.api_gateway_name}-${var.project_id_hyphens}"
  api_gateway_stage_name = "api_gateway_stage-${var.project_id_hyphens}"
  lambda_function_invoke_arn = module.lambda.lambda_function_invoke_arn
}

# Output vars for development and CI/CD

output "lambda_function_name" {
  value = "${var.lambda_function_name}-${var.project_id_hyphens}"
}

output "bucket_name" {
  value = module.bucket.name
}

output "api_gateway_base_url" {
  description = "Base URL for API Gateway stage."
  value = module.api_gateway.api_gateway_base_url
}

output "mlflow_external_ip" {
  value = module.ec2_mlflow.external_ip
}

output "prefect_external_ip" {
  value = module.ec2_prefect.external_ip
}

output "ecr_repo_name" {
  value = "${var.ecr_repo_name}-${var.project_id_hyphens}"
}

output "ecr_image_uri" {
  value = module.ecr.image_uri
}

output "project_id_hyphens" {
  value = var.project_id_hyphens
}

output "project_id" {
  value = var.project_id
}

output "mlflow_model_name" {
  value = var.project_id
}

output "mlflow_tracking_uri" {
  value = local.mlflow_tracking_uri
}
