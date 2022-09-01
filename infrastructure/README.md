
Module development
- Create EC2 instance for development
  - Use script to install everything needed
  - Also may be used as Prefect agent

Module Prefect
- Create EC2 instance for Prefect (install docker (script when launching the instance) and run the image)
- Or create ECR image and use ECS

Module mlflow
- S3 bucket to store artifacts during experiment tracking (mlflow) and model deployment (to get the model when registry is not used)
- Create EC2 micro instance for mlflow server
- Create Postgres SQL database for logging experiments, params and metrics
- Note: The models will be stored in the S3 bucket. And final model in the model registry

Module deployment 
- Create ECR image from source when source files are changes or Dockerfile? (optional)
- Launch EC2 instance by ECS from ECR image?
- Or launch EC2 (install docker (script when launching the instance) and run the image)?
- Note: This image will pick up the model from S3 or model registry

Module Monitoring
- Use AWS Cloudformation to setup EC2 instance from yaml file (Evidently, Prometheus and Graphana)

Workflow
IAC Terraform (Base infrastructure) -> Development (model training) -> Application workflow (Deployment: CI/CD - Docker image (pick model) - ECR)
