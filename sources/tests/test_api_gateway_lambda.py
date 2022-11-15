import os

import requests

"""
This script does the same as the following command:

curl -X POST -H "Content-Type: application/json" \
    -d "{'trip_id': 33, 'pickup_community_area': '8', 'dropoff_community_area': '32'}" \
    https://8bi0bzeja8.execute-api.eu-west-1.amazonaws.com/api_gateway_stage-chicago-taxi/hello
"""

if __name__ == "__main__":

    gateway_url = os.getenv(
        "API_GATEWAY_BASE_URL",
        "https://6hd2cram5f.execute-api.eu-west-1.amazonaws.com/api_gateway_stage-chicago-taxi",
    )
    URL = f"{gateway_url}/predict"
    data = {
        "trip_id": "2b0bbf69fcaa3815ea9280360c01be4e9642f805",
        "pickup_community_area": "8",
        "dropoff_community_area": "32",
    }

    # .post serializes json parameter (must be JSON serializable) and send it into the body of the request.
    #  data parameter (not used here), is similar, but not serializes in JSON format).
    request = requests.post(URL, json=data)
    # .json deserializes the response
    body = request.json()
    print(body)
