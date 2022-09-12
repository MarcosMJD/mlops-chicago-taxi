# Currently not implemented. Do not run this script
# Use with terraform plan -var-file="./prod.tfvars"
# Resource names will be appended with the name of the project
# s3_bucket_name_suffix will avoid conflicts with existing bucket names
s3_bucket_name =  "prod"
s3_bucket_name_suffix = "mmjd"
lambda_function_local_path = "../sources/production/chicago_taxi_prediction.py"
docker_image_local_path = "../sources/production/Dockerfile"
ecr_repo_name = "prod"
lambda_function_name = "prod"
api_gateway_name = "prod"
