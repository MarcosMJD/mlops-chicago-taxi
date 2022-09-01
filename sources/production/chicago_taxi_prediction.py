import model_service
import json
import os

EXPERIMENT_ID = os.getenv("MLFLOW_EXPERIMENT_ID", "2")
RUN_ID = os.getenv("MLFLOW_RUN_ID","e4ff37b7254a408c86826fb2a25573a9")
S3_BUCKET_NAME = os.getenv("MLFLOW_BUCKET_NAME", "stg-chicago-taxi-fc4rdz8d")
S3_BUCKET_FOLDER = os.getenv("MLFLOW_BUCKET_FOLDER", "mlflow")

model = model_service.init_model(S3_BUCKET_NAME, S3_BUCKET_FOLDER, EXPERIMENT_ID, RUN_ID)

def lambda_handler(event, context):

    # When using AWS_PROXY integration, the full http request is received as the event
    input_data = json.loads(event['body'])
   
    prediction = model.lambda_handler(input_data)

    return {
        'statusCode': 200,
        'body': json.dumps(prediction),
        'event': event,
        "isBase64Encoded": False
    }
