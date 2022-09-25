"""
This module downloads datasets from data.cityofchicago.org API and stores them as csv files

Functions:

  download_file(url:str, output_filename:str)
  download_dataset(year: integer, month: integer, days: integer = 0, output_filename: str):

  Downloads a dataset from the chicago taxi api, according to the specified parameters.
  If days = 0, it will download the enrtire month

"""

from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta


def download_file(url: str, output_filename: str):
    if output_filename is None:
        output_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return output_filename


def download_dataset(year: int, month: int, days: int, output_filename: str):

    # the path of the output_filename path must exist

    start_date = datetime(year, month, 1)
    if days == 0:
        end_date = start_date + relativedelta(months=1, days=-1)
    else:
        end_date = datetime(year, month, days)

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    uri = (
        "https://data.cityofchicago.org/api/views/wrvz-psew/rows.csv?"
        + "query=select%20*%20where%20%60trip_start_timestamp%60%20%3E%3D%20%27"
        + f"{start_date}%27%20AND%20%60trip_start_timestamp%60%20%3C%20%27"
        + f"{end_date}%27&read_from_nbe=true&version=2.1&accessType=DOWNLOAD"
    )

    output_filename = download_file(uri, output_filename)

    return output_filename


if __name__ == "__main__":

    download_dataset(2022, 2, 0, "./data/test.csv")
