resource "aws_lambda_function" "lambda" {
  function_name = var.lambda_function_name
  # Image can also be any base image to bootstrap the lambda config, unrelated to your Inference service on ECR
  # which would be anyway updated regularly via a CI/CD pipeline. Here we use our generated image when creating ECR
  image_uri     = var.image_uri
  package_type  = "Image"
  role          = aws_iam_role.lambda_iam_role.arn
  memory_size   = 256


  tracing_config {
    mode = "Active"
  }

  environment {
    variables = var.lambda_env_vars
  }

  timeout = 180
}

resource "aws_cloudwatch_log_group" "lambda" {

  name = "/aws/lambda/${aws_lambda_function.lambda.function_name}"
  retention_in_days = 30

}

output "lambda_function_name" {
  description = "Name of the Lambda function."
  value = aws_lambda_function.lambda.function_name
}

output "lambda_function_invoke_arn" {
  description = "value"
  value = aws_lambda_function.lambda.invoke_arn
}
