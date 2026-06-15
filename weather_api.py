"""
Fetch WeatherAPI data for Boston Marathon dates.
"""

import os
import time

import dotenv
import pandas as pd
import requests

from race_dates import RACE_DATES

dotenv.load_dotenv()

BASE_URL = "http://api.weatherapi.com/v1/history.json"
RACE_HOURS = [10, 11, 12, 13, 14]
WEATHER_PATH = "data/weather.csv"


def get_weather_data():
    """
    Fetch historical weather data for Boston Marathon race dates.

    Returns:
        pd.DataFrame: Weather data for selected race-day hours.
    """
    api_key = os.environ.get("WEATHER_API_KEY")

    if not api_key:
        print("Missing WEATHER_API_KEY")
        return pd.DataFrame()

    records = []

    for year, race_date in RACE_DATES.items():
        print(f"Fetching weather for {year}: {race_date}")

        params = {
            "key": api_key,
            "q": "Boston",
            "dt": race_date
        }

        response = requests.get(BASE_URL, params=params)

        if response.status_code != 200:
            print(f"Failed for {year}: {response.status_code}")
            continue

        data = response.json()
        records.extend(convert_to_dataframe(data, year, race_date))

        time.sleep(1)

    return pd.DataFrame(records)


def convert_to_dataframe(data, year, race_date):
    """
    Convert WeatherAPI JSON into hourly weather rows.
    """
    records = []

    forecast_day = data["forecast"]["forecastday"][0]
    day_summary = forecast_day["day"]
    hourly_data = forecast_day["hour"]

    for hour in hourly_data:
        timestamp = pd.to_datetime(hour["time"])

        if timestamp.hour in RACE_HOURS:
            records.append({
                "year": year,
                "race_date": race_date,
                "datetime": hour["time"],
                "hour": timestamp.hour,
                "temp_f": hour.get("temp_f"),
                "feelslike_f": hour.get("feelslike_f"),
                "wind_mph": hour.get("wind_mph"),
                "wind_degree": hour.get("wind_degree"),
                "wind_dir": hour.get("wind_dir"),
                "humidity": hour.get("humidity"),
                "precip_in": hour.get("precip_in"),
                "condition": hour.get("condition", {}).get("text"),
                "daily_maxtemp_f": day_summary.get("maxtemp_f"),
                "daily_mintemp_f": day_summary.get("mintemp_f"),
                "daily_avgtemp_f": day_summary.get("avgtemp_f"),
                "daily_maxwind_mph": day_summary.get("maxwind_mph"),
                "daily_totalprecip_in": day_summary.get("totalprecip_in"),
                "daily_avghumidity": day_summary.get("avghumidity"),
            })

    return records


def clean_weather_data(df):
    """
    Clean weather data.
    """
    if df.empty:
        return df

    df = df.drop_duplicates()
    required_columns = [
        "year",
        "race_date",
        "datetime",
        "hour",
        "temp_f",
        "feelslike_f",
        "wind_mph",
        "wind_dir",
        "humidity",
        "precip_in",
    ]

    df = df.dropna(subset=required_columns)

    df["year"] = df["year"].astype(int)
    df["race_date"] = pd.to_datetime(df["race_date"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour"] = df["hour"].astype(int)

    return df


def main():
    weather_df = get_weather_data()
    weather_df = clean_weather_data(weather_df)

    os.makedirs("data", exist_ok=True)
    weather_df.to_csv(WEATHER_PATH, index=False)

    print(weather_df.head())
    print(weather_df.shape)
    print(f"Saved weather data to {WEATHER_PATH}")

if __name__ == "__main__":
    main()