import sys
from pathlib import Path
from deepdiff import DeepDiff
import json
import os

from production.chicago_taxi_prediction import lambda_handler
from production.model_service import ModelService

FEATURES = {
    'id': 'abcd',
    'pickup_community_area': 8.0,
    'dropoff_community_area': 32.0
}

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

class DummyModel:

    def __init__(self, version: str = '1.0'):
        self.version = version

    def predict(self, features: dict):

        prediction = features['pickup_community_area'] + features['dropoff_community_area']
        return [prediction]

def test_lambda_handler(expected_result=EXPECTED_PREDICTION):
    # Ensure we read from the right path, since this script may run from different path
    # specially with github actions
    test_directory = Path(__file__).parent
    event = json.loads(read_text(test_directory / '../test_data/http_request.json'))

    expected_result = {
       'statusCode': 200,
        'body': json.dumps(EXPECTED_PREDICTION),
        'event': event,
        "isBase64Encoded": False
    }
    actual_prediction = lambda_handler(event, context=None)

    diff = DeepDiff(actual_prediction, expected_result, significant_digits=0)

    assert 'type_changes' not in diff
    assert 'values_changed' not in diff

    return actual_prediction

if __name__ == "__main__":

    model = DummyModel()

    actual_prediction = test_lambda_handler()

    #print(actual_prediction)
