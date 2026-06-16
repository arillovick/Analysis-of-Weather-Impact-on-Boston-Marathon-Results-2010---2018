"""
Merges BAA marathon results data
with weather and air quality data
on race year.
"""

import pandas as pd
from baa import load_all_baa_data

WEATHER_PATH = "data/weather.csv"
AQ_PATH = "data/air_quality.csv"
OUTPUT_PATH = "data/merged.csv"

def load_weather():
    """Load weather data and aggregate hourly
    rows to one row per year"""
    try:
        df = pd.read_csv(WEATHER_PATH)
    except FileNotFoundError:
        print("weather.csv not found")
        return pd.DataFrame()

    if df.empty:
        print("weather.csv is empty")
        return pd.DataFrame()

    agg = df.groupby("year").agg(
        avg_temp_f = ("temp_f", "mean"),
        avg_feelslike_f = ("feelslike_f", "mean"),
        avg_wind_mph = ("wind_mph", "mean"),
        avg_humidity = ("humidity", "mean"),
        total_precip_in = ("precip_in", "sum"),
        daily_maxtemp_f = ("daily_maxtemp_f", "first"),
        daily_mintemp_f = ("daily_mintemp_f", "first"),
        daily_totalprecip_in = ("daily_totalprecip_in", "first")
    ).reset_index()

    return agg

def load_air_quality():
    """Load air quality and aggregate to one row per year
    with one col per pollutant"""
    try:
        df = pd.read_csv(AQ_PATH)
    except FileNotFoundError:
        print("air_quality.csv not found")
        return pd.DataFrame()

    if df.empty:
        print("air_quality.csv is empty")
        return pd.DataFrame()

    df["race_date"] = pd.to_datetime(df["race_date"])

    # change pollutants to columns and average across each hour of the race
    agg = df.groupby(["year", "pollutant"])["value"].mean().unstack("pollutant").reset_index()

    # flatten column names
    agg.columns.name = None
    agg = agg.rename(columns={"pm25": "avg_pm25", "o3": "avg_o3",
                              "no2": "avg_no2"})

    return agg

def merge_all():
    """Merge BAA, weather, and air quality into one DataFrame"""
    baa = load_all_baa_data()
    weather = load_weather()
    aq = load_air_quality()

    merged = baa.copy()

    # left join to preserve all BAA rows even if weather/AQ are missing
    if not weather.empty:
        merged = merged.merge(weather, on="year", how="left")

    if not aq.empty:
        merged = merged.merge(aq, on="year", how="left")

    # print stats
    print(f"Merged shape: {merged.shape}")
    print(f"Years in merge: {sorted(merged['year'].unique())}")
    print(f"Columns: {merged.columns.tolist()}")

    return merged

def main():
    df = merge_all()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()