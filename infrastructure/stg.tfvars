# Use with terraform plan -var-file="./stg.tfvars"
# Resource names will be appended with the name of the project
# s3_bucket_name_suffix will avoid conflicts with existing bucket names
s3_bucket_name =  "stg"
s3_bucket_name_suffix = "mmjd"
lambda_function_local_path = "../sources/production/chicago_taxi_prediction.py"
docker_image_local_path = "../sources/production/Dockerfile"
ecr_repo_name = "stg"
lambda_function_name = "stg"
api_gateway_name = "stg"

# Model
# We will use a dummy model. Real models will be updated in CI/CD workflow
model_location = ""
experiment_id = ""
run_id = ""
