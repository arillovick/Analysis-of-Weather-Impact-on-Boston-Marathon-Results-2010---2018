"""
Fetch OpenAQ data for Boston Marathon dates
"""

import pandas as pd
import pytest
import dotenv
import requests
import os
from unittest.mock import patch

# OpenAQ API Key from Lecture 4
dotenv.load_dotenv()
AIR_QUALITY_PATH = "data/air_quality.csv"

MY_DF = pd.DataFrame([
    {'sensor': "co"},
    {'sensor': "co"}
])

def get_air_quality_data():
    """
    Get air quality data from the OpenAQ API-
     we are going to get PM2.5 data by day
     from a sensor in Boston (sensor ID 521)

    Returns:
        dataframe with only
    """
    api_key = os.environ.get("OPENAQ_KEY")
    headers = {'X-API-Key': api_key} if api_key else None
    url = "https://api.openaq.org/v3/sensors/688/measurements/daily"
    hardcoded_fields = {"neighborhood": "Roxbury",
                        "sensor": "pm25",
                        "units": "cubic microns"}
    #make the request
    response = requests.get(url, params={}, headers=headers)

    # if error, send out an empty dataframe
    if response.status_code != 200:
        return pd.DataFrame()

    ### data in dictionary
    data_dct = response.json()

    df = convert_to_dataframe(data_dct, hardcoded_fields)
    return df

def convert_to_dataframe(data, hardcoded_fields):
    """
    Convert API response to pandas DataFrame
    Args:
        data (dict): JSON response from OpenAQ API

    Returns:
        pd.DataFrame: DataFrame with measurement data
    """
    records = []
    for measurement in data['results']:
        entry = {
        # extract relevant data!
            "date":  measurement["date"]["utc"],
             "value": measurement["value"],
        }
        entry.update(hardcoded_fields)
        records.append(entry)

    df = pd.DataFrame(records)
    return df