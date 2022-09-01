# mlops-taxi-prediction

prefect config set PREFECT_API_URL="http://<external-ip>:8080/api" Maybe can be done programmatically?
export MLFLOW_TRACKING_URI="http://54.74.157.93:8080"

ToDo

- Use pipelines or save dv as an artifact
- Manage passwords (e.g. database) in aws
  - mlflo https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/setup-credentials.html
- Make user_data persistent, so that after reboot the ec2, it still works
- Check lib versions in pipfiles
- Use logging in prefect
- Use S3 to store datasets
- Check no cache when using pipenv in Dockerfile
- In dev system... maybe script: 
  - Set mlflow env var for the server
  - Set prefect to use prefect server api
  - 

Bugs
- Terraform state file not created in S3 backend.

Continue
- Deployment of model
- Check TErrafor output not working
- ignore files in prefect
- Check mlflow folder in S3
- Modify model and preprocessor to use pipeline or model

Notes

To create programmatically an storage block in prefect:
from prefect.filesystems import S3
block = S3(bucket_path="chicago-taxi-fc4rdz8d")
block.save("example-block")

Then to build a deployment
prefect deployment build trainning_pipeline.py:main_flow --name test --tag test --storage-block s3/example-block -q test
This will upload the .py files to S3 bucket

Or with object:

To create the deployment and queue (in prefect orion server), and also upload to S3 the yaml file:
prefect deployment apply .\main_flow-deployment.yaml

To start an agent
prefect agent start -q 'test'

To run a flow
prefect deployment run <FLOW_NAME>/<DEPLOYMENT_NAME>



