from typing import List
import mlflow

class ModelService:

    def __init__(self, model:str, callbacks:List=None):

        self.model = model
        self.callbacks = callbacks or []

    def preprocess_features(self, data: dict):

        # The data in dataset already has 'id' unique.
        # If not the data is may be added with:
        # data['id'] = data.apply(lambda x: str(uuid.uuid4()), axis = 1)
        return data

    def predict(self, features: dict):

        pred = self.model.predict(features)
        for callback in self.callbacks:
            callback(pred)
        return (pred[0])

    def lambda_handler(self, input_data: dict):

        prediction = self.predict(input_data)
        return {'prediction': prediction}


def load_model(s3_bucket_name: str, s3_bucket_folder: str, experiment_id: str, run_id: str):

    model_location = f"s3://{s3_bucket_name}/{s3_bucket_folder}/{experiment_id}/{run_id}/artifacts/model"

    model = mlflow.pyfunc.load_model(model_location)

    return model

def init_model(s3_bucket_name: str, s3_bucket_folder: str, experiment_id: str, run_id: str):

    model = load_model(s3_bucket_name, s3_bucket_folder, experiment_id, run_id)
    return ModelService(model)
