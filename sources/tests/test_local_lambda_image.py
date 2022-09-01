# Firstly, run:
# docker run -it -p 8080:8080 546106488772.dkr.ecr.eu-west-1.amazonaws.com/stg-chicago-taxi:latest

import requests

if __name__ == "__main__":

    URL = "http://localhost:8080/2015-03-31/functions/function/invocations"
    r = requests.get(URL, json="Marcos")
    print(r.json())
