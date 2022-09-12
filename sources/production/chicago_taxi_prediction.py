import os
import json
import logging

import requests

from production.model_service import init_model_s3, init_dummy_model, init_model_local

# Run from test folder if local model is in use, so that default model location is found
# Otherwise, set env var accordingly.

EXPERIMENT_ID = os.getenv("MLFLOW_EXPERIMENT_ID", "2")
RUN_ID = os.getenv("MLFLOW_RUN_ID", "e4ff37b7254a408c86826fb2a25573a9")
S3_BUCKET_NAME = os.getenv("MLFLOW_BUCKET_NAME", "stg-chicago-taxi-fc4rdz8d")
S3_BUCKET_FOLDER = os.getenv("MLFLOW_BUCKET_FOLDER", "mlflow")
EVIDENTLY_SERVICE_ADDRESS = os.getenv(
    "EVIDENTLY_SERVICE_ADDRESS", "http://127.0.0.1:8085"
)
MODEL_LOCATION = os.getenv("MLFLOW_MODEL_LOCATION", '')

# Todo: get model location from mlflow's model registry server
if MODEL_LOCATION == "s3":
    model = init_model_s3(S3_BUCKET_NAME, S3_BUCKET_FOLDER, EXPERIMENT_ID, RUN_ID)
elif MODEL_LOCATION == "":
    model = init_dummy_model()
else:
    model = init_model_local(MODEL_LOCATION)


def send_to_evidently_service(record, prediction):
    rec = record.copy()
    logging.info(rec)
    rec['prediction'] = prediction
    logging.info([rec])
    return requests.post(f"{EVIDENTLY_SERVICE_ADDRESS}/iterate/taxi", json=[rec])


def lambda_handler(event, context):
    # pylint: disable=unused-argument
    # When using AWS_PROXY integration, the full http request is received as the event
    input_data = json.loads(event['body'])
    # print(event)
    prediction = model.lambda_handler(input_data)
    # This is under development. Not ready yet
    # send_to_evidently_service(input_data, prediction['prediction'])
    return {
        'statusCode': 200,
        'body': json.dumps(prediction),
        'event': event,
        "isBase64Encoded": False,
    }
