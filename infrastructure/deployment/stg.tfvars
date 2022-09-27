# Use with terraform plan -var-file="./stg.tfvars"
# Resource names will be appended with the name of the project. E.g. lambda_function_name="stg-chicago-taxi"
# s3_bucket_name_suffix will avoid conflicts with existing bucket names
s3_bucket_name =  "stg"
s3_bucket_name_suffix = "mmjd"
# Image will be build and push to ECR on every change in the following files
lambda_function_local_path = "../../sources/production/chicago_taxi_prediction.py"
model_service_local_path = "../../sources/production/model_service.py"
docker_image_local_path = "../../sources/production/Dockerfile"

ecr_repo_name = "stg"
lambda_function_name = "stg"
api_gateway_name = "stg"

# Model
# We will use a dummy model. Real models will be updated in CI/CD workflow
# mlflow_model_location = ""

# test
mlflow_model_location = "mlflow"
mlflow_model_stage = "Staging"
