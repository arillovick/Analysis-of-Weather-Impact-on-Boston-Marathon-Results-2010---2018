"""
Clean merged Boston Marathon dataset.
"""

import pandas as pd


INPUT_PATH = "data/merged.csv"
OUTPUT_PATH = "data/merged_clean.csv"


KEEP_COLUMNS = [
    "year",
    "race_date",
    "display_name",
    "age",
    "gender",
    "residence",
    "finish_time",
    "seconds",
    "overall",
    "gender_result",
    "division_result",
    "pace",
    "avg_temp_f",
    "avg_feelslike_f",
    "avg_wind_mph",
    "avg_humidity",
    "total_precip_in",
    "daily_maxtemp_f",
    "daily_mintemp_f",
    "daily_totalprecip_in",
    "avg_no2",
    "avg_o3",
    "avg_pm25",
]


def clean_merged_data(df):
    """Clean merged marathon, weather, and air quality data."""
    df = df.copy()

    df = df[(df["year"] >= 2010) & (df["year"] <= 2018)]

    columns_to_keep = [col for col in KEEP_COLUMNS if col in df.columns]
    df = df[columns_to_keep]

    df["year"] = df["year"].astype(int)
    df["race_date"] = pd.to_datetime(df["race_date"])
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["seconds"] = pd.to_numeric(df["seconds"], errors="coerce")

    numeric_columns = [
        "overall",
        "gender_result",
        "division_result",
        "avg_temp_f",
        "avg_feelslike_f",
        "avg_wind_mph",
        "avg_humidity",
        "total_precip_in",
        "daily_maxtemp_f",
        "daily_mintemp_f",
        "daily_totalprecip_in",
        "avg_no2",
        "avg_o3",
        "avg_pm25",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=[
            "year",
            "race_date",
            "display_name",
            "gender",
            "finish_time",
            "seconds",
        ]
    )

    weather_columns = ["avg_temp_f", "avg_wind_mph", "avg_humidity"]

    existing_weather_columns = [
        col for col in weather_columns if col in df.columns
    ]

    df = df.dropna(subset=existing_weather_columns)

    df["display_name"] = df["display_name"].str.title()
    df["gender"] = df["gender"].str.upper()

    if "residence" in df.columns:
        df["residence"] = df["residence"].fillna("Unknown")

    df = df.sort_values(["year", "gender", "gender_result"])

    return df


def main():
    """Load, clean, and save merged dataset."""
    df = pd.read_csv(INPUT_PATH)
    clean_df = clean_merged_data(df)

    clean_df.to_csv(OUTPUT_PATH, index=False)

    print(clean_df.head())
    print(clean_df.shape)
    print(f"Saved cleaned merged data to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()