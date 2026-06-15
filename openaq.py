"""
Fetch OpenAQ air quality data for Boston Marathon dates
"""

import os
import datetime as dt

import dotenv
import pandas as pd
import requests

from race_dates import RACE_DATES

dotenv.load_dotenv()

BASE_URL = "https://api.openaq.org/v3/sensors/{sensor_id}/hours"
EASTERN_OFFSET = -4
AIR_QUALITY_PATH = "data/air_quality.csv"

# Verified AirNow sensors near the Boston finish line
# pm25 must NOT be 688 (empty on race days); 786 is the verified PM2.5 sensor
# O3 (779) and NO2 (778) have race-day data 2017-2026
SENSORS = {
    "pm25": 786,
    "o3": 779,
    "no2": 778,}

UNITS = {
    "pm25": "ug/m3",
    "o3": "ppm",
    "no2": "ppm",}


def get_air_quality_data():
    """
    Fetch race-day hourly air quality for every Boston Marathon date

    Returns:
        pd.DataFrame: hourly pollutant rows across all race years with data
    """
    api_key = os.environ.get("OPENAQ_KEY")

    if not api_key:
        print("Missing OPENAQ_KEY")
        return pd.DataFrame()

    headers = {"X-API-Key": api_key}
    records = []

    for year, race_date in RACE_DATES.items():
        if race_date is None:
            print(f"Skipping {year}: no race")
            continue

        dt_from, dt_to = race_window_utc(race_date)

        for pollutant, sensor_id in SENSORS.items():
            print(f"Fetching {pollutant} for {year}: {race_date}")

            url = BASE_URL.format(sensor_id=sensor_id)
            params = {"datetime_from": dt_from, "datetime_to": dt_to, "limit": 100}

            response = requests.get(url, params=params, headers=headers)

            if response.status_code != 200:
                print(f"  Failed {pollutant} {year}: {response.status_code}")
                continue

            records.extend(
                convert_to_dataframe(response.json(), year, race_date, pollutant, UNITS[pollutant]))

    return pd.DataFrame(records)


def race_window_utc(race_date):
    """
    Return ISO-UTC strings for the 10:00-14:00 local race window
    """
    d = pd.to_datetime(race_date).date()
    eastern = dt.timezone(dt.timedelta(hours=EASTERN_OFFSET))
    start = dt.datetime(d.year, d.month, d.day, 10, 0, tzinfo=eastern)
    end = dt.datetime(d.year, d.month, d.day, 14, 0, tzinfo=eastern)
    fmt = "%Y-%m-%dT%H:%M:%SZ"

    return (
        start.astimezone(dt.timezone.utc).strftime(fmt),
        end.astimezone(dt.timezone.utc).strftime(fmt),)


def convert_to_dataframe(data, year, race_date, pollutant, units):
    """
    Convert one OpenAQ /hours response into hourly rows
    """
    records = []

    for measurement in data.get("results", []):
        period = measurement.get("period", {})
        start = period.get("datetimeFrom", {})

        records.append({
            "year": year,
            "race_date": race_date,
            "datetime_utc": start.get("utc"),
            "datetime_local": start.get("local"),
            "pollutant": pollutant,
            "value": measurement.get("value"),
            "units": units,})

    return records


def clean_air_quality_data(df):
    """
    Clean air quality data.
    """
    if df.empty:
        return df

    df = df.drop_duplicates()

    required_columns = [
        "year",
        "race_date",
        "datetime_utc",
        "pollutant",
        "value",]

    df = df.dropna(subset=required_columns)

    df["year"] = df["year"].astype(int)
    df["race_date"] = pd.to_datetime(df["race_date"])
    df["value"] = df["value"].astype(float)

    return df


def main():
    air_quality_df = get_air_quality_data()
    air_quality_df = clean_air_quality_data(air_quality_df)

    os.makedirs("data", exist_ok=True)
    air_quality_df.to_csv(AIR_QUALITY_PATH, index=False)

    print(air_quality_df.head())
    print(air_quality_df.shape)
    print(f"Saved air quality data to {AIR_QUALITY_PATH}")


if __name__ == "__main__":
    main()