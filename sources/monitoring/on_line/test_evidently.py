import os

import requests

if __name__ == "__main__":

    evidently_url = os.getenv(
        "EVIDENTLY_URL",
        "http://localhost:8085",
    )
    URL = f"{evidently_url}/iterate/taxi"
    data = {
        "trip_id": "2b0bbf69fcaa3815ea9280360c01be4e9642f805",
        "pickup_community_area": "8",
        "dropoff_community_area": "32",
        "prediction": "23",
    }

    # .post serializes json parameter (must be JSON serializable) and send it into the body of the request.
    #  data parameter (not used here), is similar, but not serializes in JSON format).
    request = requests.post(URL, json=data)
    print(request)
    # .json deserializes the response
    body = request.json()
    print(body)
