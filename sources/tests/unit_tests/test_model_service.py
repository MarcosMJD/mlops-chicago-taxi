from pathlib import Path

from deepdiff import DeepDiff

from production.model_service import ModelService

FEATURES = {
    "trip_id": "2b0bbf69fcaa3815ea9280360c01be4e9642f805",
    "pickup_community_area": "8",
    "dropoff_community_area": "32",
}

EXPECTED_RESULT = {
    "trip_id": "2b0bbf69fcaa3815ea9280360c01be4e9642f805",
    "pickup_community_area": "8",
    "dropoff_community_area": "32",
    "prediction": 40.0,
}


def read_text(file):
    test_directory = Path(__file__).parent

    with open(test_directory / file, "rt", encoding="utf-8") as f_in:
        return f_in.read().strip()


class DummyModel:
    def __init__(self, version: str = "1.0"):
        self.version = version

    def predict(self, features: dict):

        prediction = int(features["pickup_community_area"]) + int(
            features["dropoff_community_area"]
        )
        return float(prediction)


def test_model_service(features=FEATURES, expected_result=EXPECTED_RESULT):

    model = DummyModel()
    model_service = ModelService(model, None)
    actual_prediction = model_service.lambda_handler(features)

    diff = DeepDiff(actual_prediction, expected_result, significant_digits=1)

    assert "type_changes" not in diff
    assert "values_changed" not in diff

    # print(diff)
    # print(actual_prediction)
    return actual_prediction


if __name__ == "__main__":

    actual_prediction = test_model_service(FEATURES)

    print(actual_prediction)
