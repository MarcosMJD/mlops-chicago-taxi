import requests
import json

"""
curl -X POST -H "Content-Type: application/json" \
    -d '{"name": "marcos"}' \
    https://8bi0bzeja8.execute-api.eu-west-1.amazonaws.com/api_gateway_stage-chicago-taxi/hello
"""

if __name__ == "__main__":

    URL = "https://b0csjriwce.execute-api.eu-west-1.amazonaws.com/api_gateway_stage-chicago-taxi/hello"
    data = {
        'id': 33,
        'pickup_community_area': 8.0,
        'dropoff_community_area': 32.0
    }

    # .post serializes data
    request = requests.post(URL, json=data)
    # .json deserializes the response
    body = request.json()
    print(body)
