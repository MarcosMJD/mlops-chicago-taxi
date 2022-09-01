variable "lambda_function_name" {
  description = "Name of the lambda function"  
}

variable "image_uri" {
  description = "URI of the image for the lambda function"
}

variable "lambda_iam_role_name" {
  description = "Name of the lambda iam role"
}

variable "lambda_iam_cloudwatch_role_policy_name" {
  description = "Name of the policy for loggin in cloudwatch"
}

variable "lambda_iam_s3_role_policy_name" {
  description = "Name of the policy for accessing s3 bucket"
}

variable "lambda_s3_bucket_name" {
  description = "Name of the bucket"
}

variable "source_arn_api_gateway" {
  description = "arn of the source that invokes lambda"
}
