"""
Loads and cleans Boston Marathon data
from 2006 - 2026 for the top 100 male and female
finishers per year.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup

from race_dates import RACE_DATES

# Pull from GitHub repo
github_url = "https://raw.githubusercontent.com/adrian3/Boston-Marathon-Data-Project/master/results{year}.csv"
# this GitHub only provides our data from 2006 - 2018
github_years = list(range(2006, 2019))

def load_github_year(year):
    """Load one year from the GitHub repo csv and standardize the columns"""
    url = github_url.format(year=year)
    df = pd.read_csv(url)
    df["year"] = year
    df["race_date"] = pd.to_datetime(RACE_DATES[year])

    # Normalize column for gender
    gender_col = next(
        (c for c in df.columns if c.strip().upper() in (
        "M/F", "GENDER", "SEX"
    )), None)
    if gender_col:
        df = df.rename(columns={gender_col: "gender"})

    # Normalize column for finishing time
    finish_col = next(
        (c for c in df.columns if "finish" in c.lower() or "official" in c.lower()),
        None
    )
    if finish_col:
        df = df.rename(columns={finish_col: "finish_time"})

    return df

def load_github_years():
    """Load and concat all GitHub years"""
    frames = []
    for year in github_years:
        try:
            frames.append(load_github_year(year))
            print(f" loaded {year}")
        except Exception as e:
            print(f" failed to load {year}: {e}")
    return pd.concat(frames, ignore_index=True)

##############################################################
# Scrape data for BAA marathon data for years 2019, 2021-2026
##############################################################

baa_url = "https://registration.baa.org/{year}/cf/Public/iframe_ResultsSearch.cfm"
scrape_years = [2019, 2021, 2022, 2023, 2024, 2025, 2026] # 2020 marathon was cancelled

def load_scrape_years():
    """Scrape 2019, 2021-2026 for both genders.
    Not working at the moment, placeholder"""
    print("Scraping not yet implemented")
    return pd.DataFrame()
    #frames = []
    #for year in scrape_years:
        #for gender in ["M", "F"]:
            #print(f"Scraping {year}, {gender}. ")
            #df = scrape_baa_year(year, gender=gender)
            #if not df.empty:
                #frames.append(df)
    #return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# Clean and combine data
critical_cols = ["year", "race_date", "gender", "finish_time", "age"]

def clean_baa(df):
    """Normalize columns, drop null values, filter to top 100 finishers per gender per year"""
    if df.empty:
        return df

    # normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("/", "_")

    # drop duplicates
    df = df.drop_duplicates()

    # drop rows missing critical fields
    existing_critical = [c for c in critical_cols if c in df.columns]
    df = df.dropna(subset=existing_critical)

    # filter top 100 finishers per gender per year
    df = df.sort_values(["year", "gender", "finish_time"])
    df = df.groupby(["year", "gender"]).head(100).reset_index(drop=True)

    return df

def load_all_baa_data():
    """Load all years, clean data, and return combined DataFrame"""
    github_df = load_github_years()

    scrape_df = load_scrape_years()

    frames = [df for df in [github_df, scrape_df] if not df.empty]

    combined = pd.concat(frames, ignore_index=True)
    combined = clean_baa(combined)

    print(f"For years: {sorted(combined['year'].unique())}")
    return combined

def main():
    df = load_all_baa_data()
    df.to_csv("data/baa_results.csv", index=False)
    print(df.head())

if __name__ == "__main__":
    main()