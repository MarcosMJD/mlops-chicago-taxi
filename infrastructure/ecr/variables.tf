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

variable "docker_image_local_path" {
    type        = string
    description = "Local path to Dockerfile"
}

variable "region" {
    type        = string
    description = "Region for Docker authentication into ECR"
    default = "eu-west-1"
}

variable "account_id" {
  description = "Id of the account"
}