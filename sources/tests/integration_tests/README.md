Note: Container must be locally running.

Either from the local build or the actual build on ECR (either in localstack or in real AWS ECR)
Example of running locally from already existing AWS ECR image:
docker run -it -p 8080:8080 546106488772.dkr.ecr.eu-west-1.amazonaws.com/stg-chicago-taxi:latest
from local image:
docker run -it -p 8080:8080 chicago-taxi:latest

Or you can also run docker-compose up from this integration_tests directory.

Them you can run integration tests from the sources directory (so that modules can be found correctly)
Also, pytest only adds to sys.path directories where test files are, so you need to add the sources directory with:

export PYTHONPATH=.
pytest ./tests/integration_tests

The tests needs these env vars
LOCAL_IMAGE_NAME="chicago-taxi:latest"
LOCAL_MODEL_LOCATION="./tests/model"

Also, you can run, from the sources directory ./tests/integration_tests/run.sh that takes care of everything
