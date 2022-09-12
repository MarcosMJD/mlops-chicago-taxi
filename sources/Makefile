# LOCAL_TAG:=$(shell date +"%Y-%m-%d-%H-%M")
LOCAL_TAG:=latest
LOCAL_IMAGE_NAME:="chicago-taxi:${LOCAL_TAG}"

unit_tests: setup
	bash ./tests/unit_tests/run.sh

quality_checks:
	black .
	isort .
	pylint --recursive=y ../.

build: quality_checks unit_tests setup
	docker build -t ${LOCAL_IMAGE_NAME} ./production

integration_tests: setup build
	LOCAL_IMAGE_NAME=${LOCAL_IMAGE_NAME} bash ./tests/integration_tests/run.sh

# The run.sh scripts use pipenv run, so there is no need to activate environment
setup:
	pipenv install --dev
	pipenv run pre-commit install
