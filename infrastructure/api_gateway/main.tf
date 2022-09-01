resource "aws_apigatewayv2_api" "api_gateway_lambda" {
  name          = var.api_gateway_name
  protocol_type = "HTTP"
}

resource "aws_cloudwatch_log_group" "api_gateway_lambda" {

  name = "/aws/api_gw/${aws_apigatewayv2_api.api_gateway_lambda.name}"
  retention_in_days = 30

}

resource "aws_apigatewayv2_stage" "api_gateway_lambda_stage" {

  api_id = aws_apigatewayv2_api.api_gateway_lambda.id

  name        = var.api_gateway_stage_name
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_lambda.arn

    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
      }
    )
  }
}

resource "aws_apigatewayv2_integration" "api_gateway_lambda_integration" {

  api_id = aws_apigatewayv2_api.api_gateway_lambda.id
  integration_uri    = var.lambda_function_invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "lambda_hello" {

  api_id = aws_apigatewayv2_api.api_gateway_lambda.id
  route_key = "POST /hello"
  target    = "integrations/${aws_apigatewayv2_integration.api_gateway_lambda_integration.id}"
}

# The "/*/*" portion grants access from any method on any resource
# within the API Gateway REST API.
output "api_gateway_execution_arn" {
  description = "Execution arn to be used by lambda iam"
  value       = "${aws_apigatewayv2_api.api_gateway_lambda.execution_arn}/*/*"
}

output "api_gateway_base_url" {
  description = "Base URL for API Gateway stage."
  value = aws_apigatewayv2_stage.api_gateway_lambda_stage.invoke_url
}




