from typing import List, Union

from mlflow import set_tracking_uri
from mlflow.pyfunc import load_model
import numpy as np
import pandas as pd


class DummyModel:
    def __init__(self, version: str = "1.0"):
        self.version = version

    def predict(self, features: dict):

        if (
            features["pickup_community_area"] is not None
            and features["dropoff_community_area"] is not None
        ):

            prediction = int(features["pickup_community_area"]) + int(
                features["dropoff_community_area"]
            )

        else:
            prediction = 0

        return float(prediction)


class ModelService:
    # Class that manages the model and processes prediction requests

    def __init__(self, model, callbacks: List = None):

        self.model = model
        self.callbacks = callbacks or []

    def preprocess_features(self, data: dict):

        # The data in dataset already has 'trip_id' unique
        # If not, id may be added with:
        # data['trip_id'] = data.apply(lambda x: str(uuid.uuid4()), axis = 1).

        # Fill Nans with -1
        return data

    def predict(self, features: pd.DataFrame):

        pred = self.model.predict(features)
        for callback in self.callbacks:
            callback(pred)
        return pred

    def set_model(self, model):
        self.model = model

    def lambda_handler(self, input_data: Union[List[dict], dict]) -> dict:
        print(input_data)
        print(type(input_data))
        prediction = input_data.copy()
        if isinstance(prediction, List):
            pred_value = self.predict(pd.DataFrame(input_data))
        else:
            pred_value = self.predict(pd.DataFrame([input_data])).ravel()
        # print(pred_value, ' ' , type(pred_value))
        if isinstance(pred_value, np.ndarray):
            prediction = pred_value.tolist()
        else:
            prediction["prediction"] = pred_value
        return prediction


def get_model_s3(
    s3_bucket_name: str, s3_bucket_folder: str, experiment_id: str, run_id: str
):

    model_location = (
        f"s3://{s3_bucket_name}/{s3_bucket_folder}/"
        f"{experiment_id}/{run_id}/artifacts/model"
    )

    model = load_model(model_location)

    return model


def init_model_s3(
    s3_bucket_name: str, s3_bucket_folder: str, experiment_id: str, run_id: str
):

    model = get_model_s3(s3_bucket_name, s3_bucket_folder, experiment_id, run_id)
    return ModelService(model)


def init_model_local(model_location: str):

    model = load_model(model_location)
    return ModelService(model)


def init_dummy_model():

    return ModelService(DummyModel())


def init_model_mlflow(tracking_uri: str, name: str, stage: str = "Staging"):

    set_tracking_uri(tracking_uri)
    model = load_model(f"models:/{name}/{stage}", False)
    return ModelService(model)
