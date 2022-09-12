import os
import json
from time import sleep
from datetime import datetime

import requests
import pyarrow.parquet as pq
from pymongo import MongoClient

TEST_DATA = "reference_data/Taxi_Trips_2022_04.parquet"
MONGODB_ADDRESS = os.getenv("MONGODB_ADDRESS", "mongodb://127.0.0.1:27018")


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

    gateway_url = os.getenv(
        "API_GATEWAY_BASE_URL",
        "https://b0csjriwce.execute-api.eu-west-1.amazonaws.com/api_gateway_stage-chicago-taxi",
    )
    url = f"{gateway_url}/predict"

    mongo_client = MongoClient(MONGODB_ADDRESS)
    db = mongo_client.get_database("prediction_service")
    collection = db.get_collection("data")

    table = pq.read_table(TEST_DATA)
    data = table.to_pylist()

    with open("target_values.csv", 'w') as f_target:
        for record in data:
            print(record)
            record['id'] = record['trip_id']
            duration = record['trip_seconds'] / 60
            f_target.write(f"{record['id']},{duration}\n")
            print(json.dumps(record, cls=DateTimeEncoder))
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(record, cls=DateTimeEncoder),
            ).json()
            print(response)
            print(f"prediction: {response['prediction']}")
            response['pickup_community_area'] = record['pickup_community_area']
            response['dropoff_community_area'] = record['dropoff_community_area']
            save_to_db(collection, response)
            sleep(1)
