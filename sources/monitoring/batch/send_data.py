import os
import json
from time import sleep
from pathlib import Path
from datetime import datetime

import requests
from pymongo import MongoClient

from development.downloader import download_dataset
from development.preprocessor import Preprocessor


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


def save_to_db(collection, record):
    # rec = record.copy()
    # rec['prediction'] = prediction
    collection.insert_one(record)


if __name__ == "__main__":

    GATEWAY_URL = os.getenv(
        "API_GATEWAY_BASE_URL",
        "https://b0csjriwce.execute-api.eu-west-1.amazonaws.com/api_gateway_stage-chicago-taxi",
    )

    url = f"{GATEWAY_URL}/predict"

    MONGODB_ADDRESS = os.getenv("MONGODB_ADDRESS", "mongodb://127.0.0.1:27018")
    mongo_client = MongoClient(MONGODB_ADDRESS)
    db = mongo_client.get_database("prediction_service")
    collection = db.get_collection("data")

    TEST_YEAR = 2022
    TEST_MONTH = 4
    TEST_DAYS = 2
    TEST_SET_NAME = f"Taxi_Trips_2022_{TEST_MONTH:02d}.csv"
    TEST_TARGET_SET_NAME = "test_target_values.csv"
    current_path = Path(__file__).parent
    TEST_PATH = current_path / "reference_data"
    TEST_SET_PATH = f"{TEST_PATH}/{TEST_SET_NAME}"
    TEST_TARGET_SET_PATH = f"{TEST_PATH}/{TEST_TARGET_SET_NAME}"
    DATE_FIELDS = ["Trip Start Timestamp", "Trip End Timestamp"]
    DTYPE = {"Pickup Community Area": str, "Dropoff Community Area": str}
    CATEGORICAL_FEATURES = [
        "pickup_community_area",
        "dropoff_community_area",
        "trip_id",
    ]
    TARGET = "trip_seconds"

    if not os.path.exists(TEST_PATH):
        os.makedirs(TEST_PATH)

    # Download dataset
    if not os.path.exists(TEST_SET_PATH):
        print(f"Downloading test set: {TEST_SET_PATH}")
        download_dataset(TEST_YEAR, TEST_MONTH, TEST_DAYS, TEST_SET_PATH)
    else:
        print("Test set already exists. Skipping download")

    preprocessor = Preprocessor(False, False)

    test_set_path_parquet = preprocessor.read_dataframe_csv(
        TEST_SET_PATH, DATE_FIELDS, DTYPE
    )
    dataset = preprocessor.read_dataframe_parquet(test_set_path_parquet)

    dataset, target = preprocessor.preprocess_data(dataset, CATEGORICAL_FEATURES, [])
    # to_dict outputs a list of dicts
    dataset = dataset.to_dict("records")

    with open(TEST_TARGET_SET_PATH, "w") as f_target:
        for i, record in enumerate(dataset):

            # This should not happend, since preprocessor has filled NaNs with '-1'
            if (
                record["pickup_community_area"] is None
                or record["dropoff_community_area"] is None
            ):
                continue
            # Write to file the target values (converted to minutes as we did in the trainning)
            # Preprocessor has created duration field already
            # target is a np array of shape n_samples, 1
            f_target.write(f"{record['trip_id']},{target[i,0]}\n")

            # Request the prediction to prediction service
            data = json.dumps(record, cls=DateTimeEncoder)
            print(f"sending features to prediction service: {data}")
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=data,
            ).json()
            if isinstance(response, list):
                if len(response) == 1:
                    prediction = response[0]
            print(f"prediction: {prediction}")
            record['prediction'] = prediction
            save_to_db(collection, record)
            sleep(1)
