import sys
from pathlib import Path
from deepdiff import DeepDiff

from production.model_service import ModelService

FEATURES = {
    'id': 'abcd',
    'pickup_community_area': 8.0,
    'dropoff_community_area': 32.0
}

EXPECTED_RESULT = {
    'id': 'abcd',
    'prediction': 40.0
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

def test_model_service(features=FEATURES, expected_result=EXPECTED_RESULT):

    model = DummyModel()
    model_service = ModelService(model, None)
    actual_prediction = model_service.lambda_handler(features)

    diff = DeepDiff(actual_prediction, expected_result, significant_digits=1)

    assert 'type_changes' not in diff
    assert 'values_changed' not in diff

    # print(diff)
    # print(actual_prediction)
    return actual_prediction

if __name__ == "__main__":

    actual_prediction = test_model_service(FEATURES)

    print(actual_prediction)
