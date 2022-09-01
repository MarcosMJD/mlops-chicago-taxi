# Use with terraform plan -var-file="./stg.tfvars"
# Resource names will be appended with the name of the project and also with a random number (when needed)
s3_bucket_name =  "stg"
lambda_function_local_path = "../sources/production/chicago_taxi_prediction.py"
docker_image_local_path = "../sources/production/Dockerfile"
ecr_repo_name = "stg"
lambda_function_name = "stg"
api_gateway_name = "stg"