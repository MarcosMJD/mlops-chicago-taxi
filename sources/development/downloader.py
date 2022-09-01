"""
This module downloads datasets from data.cityofchicago.org API and stores them as csv files

Functions:

  download_file(url:str, output_filename:str)
  download_dataset(start_date:datetime, end_date:datetime, output_filename:str):

"""

from datetime import datetime
import requests
from prefect import task

def download_file(url:str, output_filename:str):
    if output_filename == None:
        output_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    return output_filename

@task
def download_dataset(start_date:datetime, end_date:datetime, output_filename:str):
    
    # the path of the output_filename path must exist

    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')
    
    uri = f"https://data.cityofchicago.org/api/views/wrvz-psew/rows.csv?" + \
    "query=select%20*%20where%20%60trip_start_timestamp%60%20%3E%3D%20%27" + \
    f"{start_date}%27%20AND%20%60trip_start_timestamp%60%20%3C%20%27" + \
    f"{end_date}%27&read_from_nbe=true&version=2.1&accessType=DOWNLOAD"

    output_filename = download_file(uri, output_filename)

    return output_filename