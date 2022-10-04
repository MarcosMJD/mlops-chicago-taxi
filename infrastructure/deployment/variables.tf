variable "aws_region" {
  description = "AWS region to create resources"
  default     = "eu-west-1"
}

variable "project_id" {
  description = "project_id"
  default     = "chicago_taxi"
}

variable "project_id_hyphens" {
  description = "project id with hyphens"
  default   = "chicago-taxi"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for the project"
}

variable "s3_bucket_name_suffix" {
  description = "Suffix to be added to the bucket to avoid conflicts"
}

variable "rds_indentifier" {
  description = "Name of the rds instance"
  default     = "postgres"
}

variable "postgres_db_name" {
  description = "Name of db in rds instance"
  default     = "db_postgres"
}

variable "postgres_db_username" {
  description = "User name of rds db"
  default     = "db_user"
}

variable "postgres_db_password" {
  description = "Password of rds db"
  default     = "db_password"
}

variable "ecr_repo_name" {
    type        = string
    description = "ECR repo name"
}

variable "ecr_image_tag" {
    type        = string
    description = "Tag of the image"
    default = "latest"
}

variable "lambda_function_local_path" {
    type        = string
    description = "Local path to lambda function / python file"
}

variable "model_service_local_path" {
    type        = string
    description = "Local path to model_service / python file"
}

variable "docker_image_local_path" {
    type        = string
    description = "Local path to Dockerfile"
}

variable "lambda_function_name" {
  description = "Name of the lambda function"
}

variable "api_gateway_name" {
  description = "Name of the api gateway"
}

# Model loading in Lambda
variable "mlflow_model_location" {
  description = "Define where the model is located. '' means a dummy model, a path means a local path, 's3' means s3, in this case run_id and experiment_id shall be provided"
  default     = ""
}

# Option S3
variable "mlflow_experiment_id" {
  description = "Experiment used in the path of s3 bucket to find the model"
  default     = ""
}

variable "mlflow_run_id" {
  description = "Run id used in the path of s3 bucket to find the model"
  default     = ""
}

# Option mlflow registry

variable "mlflow_model_stage" {
  description = "Model stage when loading from mlflow registry server"
  default     = ""
}

variable "repo" {
  description = "Url of the repo to clone into the developement vm"
  default     = ""
}
