from typing import List

import mlflow


class DummyModel:
    def __init__(self, version: str = '1.0'):
        self.version = version

    def predict(self, features: dict):

        prediction = (
            features['pickup_community_area'] + features['dropoff_community_area']
        )
        return [float(prediction)]


class ModelService:
    # Class that manages the model and processes prediction requests

    def __init__(self, model, callbacks: List = None):

        self.model = model
        self.callbacks = callbacks or []

    def preprocess_features(self, data: dict):

        # The data in dataset already has 'id' unique
        # If not the data is may be added with:
        # data['id'] = data.apply(lambda x: str(uuid.uuid4()), axis = 1).
        return data

    def predict(self, features: dict):

        pred = self.model.predict(features)
        for callback in self.callbacks:
            callback(pred)
        return pred[0]

    def set_model(self, model):
        self.model = model

    def lambda_handler(self, input_data: dict):

        prediction = self.predict(input_data)
        return {'id': input_data['id'], 'prediction': prediction}


def get_model_s3(
    s3_bucket_name: str, s3_bucket_folder: str, experiment_id: str, run_id: str
):

    model_location = (
        f"s3://{s3_bucket_name}/{s3_bucket_folder}/"
        f"{experiment_id}/{run_id}/artifacts/model"
    )

    model = mlflow.pyfunc.load_model(model_location)

    return model


def load_model(model):
    return ModelService(model)


def init_model_s3(
    s3_bucket_name: str, s3_bucket_folder: str, experiment_id: str, run_id: str
):

    model = get_model_s3(s3_bucket_name, s3_bucket_folder, experiment_id, run_id)
    return load_model(model)


def init_model_local(model_location: str):

    model = mlflow.pyfunc.load_model(model_location)
    return load_model(model)


def init_dummy_model():
    return load_model(DummyModel())
