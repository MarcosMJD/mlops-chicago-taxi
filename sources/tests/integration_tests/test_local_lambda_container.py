import sys
from deepdiff import DeepDiff
import json
import requests
from pathlib import Path

FEATURES = {
    'id': 'abcd',
    'pickup_community_area': 8.0,
    'dropoff_community_area': 32.0
}

# Note: Container must be locally running.
# Either from the local build or the actual build on ECR (either in localstack or in real AWS ECR)
# Example of running locally from already existing AWS ECR image:
# docker run -it -p 8080:8080 546106488772.dkr.ecr.eu-west-1.amazonaws.com/stg-chicago-taxi:latest
# from local image:
# docker run -it -p 8080:8080 chicago-taxi:latest

URL = "http://localhost:8080/2015-03-31/functions/function/invocations"

# Note that aws lambda requires the result in the body of the http response
# to be encoded as json string, so that the actual result will be the following
# constant as a string, so we need all decimals to check
EXPECTED_PREDICTION = {
    'id': 'abcd',
    'prediction': 23.872523122771923
}

def read_text(file):
    test_directory = Path(__file__).parent

    with open(test_directory / file, 'rt', encoding='utf-8') as f_in:
        return f_in.read().strip()

def test_local_lambda_container(expected_result=EXPECTED_PREDICTION):

    test_directory = Path(__file__).parent
    event = json.loads(read_text(test_directory / '../test_data/http_request.json'))

    expected_result = {
       'statusCode': 200,
        'body': json.dumps(EXPECTED_PREDICTION),
        'event': event,
        "isBase64Encoded": False
    }

    response = requests.post(URL, json=event)
    # Currently actual_prediction is of type requests.models.Response, so get the json dict
    actual_prediction = response.json()

    diff = DeepDiff(actual_prediction, expected_result, significant_digits=0)

    assert 'type_changes' not in diff
    assert 'values_changed' not in diff

    print(actual_prediction)

    return actual_prediction

if __name__ == "__main__":

    actual_prediction = test_local_lambda_container()

    print(actual_prediction)
