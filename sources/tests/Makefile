# LOCAL_TAG:=$(shell date +"%Y-%m-%d-%H-%M")
LOCAL_TAG:=latest
LOCAL_IMAGE_NAME:="chicago-taxi:${LOCAL_TAG}"

unit_tests: setup
	bash ./unit_tests/run.sh

quality_checks: 

build: quality_checks unit_tests setup
	docker build -t ${LOCAL_IMAGE_NAME} ../production

integration_tests: setup build
	LOCAL_IMAGE_NAME=${LOCAL_IMAGE_NAME} bash ./integration_tests/run.sh

setup:
	pipenv install --dev
