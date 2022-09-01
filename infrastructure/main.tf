# Backend will be at an s3 bucket, that shall be created previously
# E.g. aws s3api create-bucket --bucket [your bucket name] --create-bucket-configuration LocationConstraint=eu-west-1
# Note: bucket names shall be unique. Choose your location accordingly.
# Note: bucket is private, objects but anyone with appropriate permissions can grant public access to objects.

terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket  = "chicago-taxi-tfstate-mmjd"
    key     = "chicago-taxi.tfstate"
    region  = "eu-west-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
  profile = "default"
}

data "aws_caller_identity" "current_identity" {}

locals {
  account_id      = data.aws_caller_identity.current_identity.account_id
}

data "aws_vpc" "default" {
  default = true
}

module "sg_ssh" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "sg_ssh-${var.project_id}"
  description = "Security group for ec2 ssh"
  vpc_id      = data.aws_vpc.default.id

  ingress_cidr_blocks = ["92.187.240.146/32"]
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

resource "random_string" "suffix" {
  length  = 8
  special = false
  lower   = true
  upper   = false
}

# Project bucket
locals {
    s3_bucket_name  = "${var.s3_bucket_name}-${var.project_id_hyphens}-${random_string.suffix.result}"
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
  user_data_mlflow_server = <<-EOF
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

# Prefect Server
# Run prefect in Docker since installation requires sqlite version which is not included in AWS instance
# To analyse, use Postgres instead of sqlite
# Because of an issue wirh CORS when running Prefect in a Docker contanier on AWS EC2, it is needed to 
# pass the external api uri to prefect. So we use ec2-metadata to get the value.

locals{
  user_data_prefect_server = <<-EOF
    #!/bin/bash
    set -ex
    sudo yum update -y
    sudo amazon-linux-extras install docker -y
    sudo service docker start
    sudo usermod -a -G docker ec2-user
    export PUBLIC_IP=$(ec2-metadata | sed -n "s/^public-ipv4: //p")
    docker  run --env PREFECT_ORION_UI_API_URL=http://$PUBLIC_IP:8080/api -p 8080:4200 prefecthq/prefect:2.2-python3.8 prefect orion start --host=0.0.0.0
  EOF
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

module "ecr" {
  source = "./ecr"
  ecr_repo_name = "${var.ecr_repo_name}-${var.project_id_hyphens}"
  ecr_image_tag = var.ecr_image_tag
  lambda_function_local_path = var.lambda_function_local_path
  docker_image_local_path = var.docker_image_local_path
  region = var.aws_region
  account_id = local.account_id
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
}

module "api_gateway" {
  source = "./api_gateway"
  api_gateway_name = "${var.api_gateway_name}-${var.project_id_hyphens}"
  api_gateway_stage_name = "api_gateway_stage-${var.project_id_hyphens}"
  lambda_function_invoke_arn = module.lambda.lambda_function_invoke_arn
}

