# Analysis of Weather Impact on Boston Marathon Results from 2010 to 2018

How do weather conditions like temperature, wind speed, wind direction, and air quality influence Boston Marathon performances?

This project analyzes the relationship between environmental conditions and marathon performance using data from the Boston Athletic Association (BAA), WeatherAPI, and OpenAQ. We examine the top 100 male and female finishers per year across available race years.

Full Analysis: BAA and weather from 2010 - 2018 (9 years), ~1800 runners
Sub-Analysis: BAA and air quality from 2017 - 2018 (2 years, limited by sensor availability near the finish line)

## Setup
1. Install packages: pandas, time, etc.
2. Configure API keys in .env file
3. Run the pipeline

## Key Files
- baa.py: Loads the top 100 male and female finishers per year from a public GitHub repository of BAA results CSVs. Standardizes column names across years and filters by gender. Coverage is 2006–2018.
- weather_api.py: Fetches hourly weather data (temperature, wind, humidity, precipitation) for each race date during the 10am–2pm race window. Aggregates to one row per year for merging.
- openaq.py: Fetches hourly PM2.5, O3, and NO2 readings from verified AirNow sensors near the Boston finish line. Race-day data is available from 2017 onward.
- merge.py: Left-joins BAA results with aggregated weather and air quality data on year. Produces data/merged.csv with 43 columns and 1 row per runner.

## Data Cleaning (clean_merged.py)

After merging, a separate cleaning step produces data/merged_clean.csv:

- Scoped to 2010–2018 — years with complete weather data
- Column selection — trimmed to 23 relevant columns (runner identity, performance, environmental conditions), dropping split times, bib numbers, and citizenship fields
- Type enforcement — year as int, `race_date` as datetime, all numeric columns coerced with errors="coerce" so bad values become NaN rather than errors
- Row filtering — drops rows missing any of: display_name, gender, finish_time, seconds, or core weather columns (avg_temp_f, avg_wind_mph, avg_humidity)
- Missing residence — filled with "Unknown" rather than dropped since it's not critical to the analysis
- String standardization — display_name title-cased, gender uppercased for consistency across years
- Sorted by year → gender → gender_result (placement within gender)
