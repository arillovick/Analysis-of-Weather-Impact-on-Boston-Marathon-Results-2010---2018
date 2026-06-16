"""
Panel dashboard for Boston Marathon weather analysis.
"""

import pandas as pd
import panel as pn
import plotly.express as px

pn.extension("plotly")

DATA_PATH = "data/merged_clean.csv"


def load_data():
    """Load cleaned merged marathon dataset."""
    df = pd.read_csv(DATA_PATH)
    df["race_date"] = pd.to_datetime(df["race_date"])
    return df


def filter_data(df, gender, year_range):
    """Filter data by gender and year range."""
    filtered = df[
        (df["year"] >= year_range[0]) &
        (df["year"] <= year_range[1])
    ]

    if gender != "All":
        filtered = filtered[filtered["gender"] == gender]

    return filtered


def make_metrics(df):
    """Create numeric metric cards."""
    avg_finish = df["seconds"].mean() / 60
    avg_temp = df["avg_temp_f"].mean()
    avg_wind = df["avg_wind_mph"].mean()
    runner_count = len(df)

    return pn.Row(
        pn.indicators.Number(
            name="Avg Finish Time (min)",
            value=round(avg_finish, 1),
            format="{value}"
        ),
        pn.indicators.Number(
            name="Avg Temp (°F)",
            value=round(avg_temp, 1),
            format="{value}"
        ),
        pn.indicators.Number(
            name="Avg Wind (mph)",
            value=round(avg_wind, 1),
            format="{value}"
        ),
        pn.indicators.Number(
            name="Runner Count",
            value=runner_count,
            format="{value}"
        ),
    )


def overview_chart(df):
    """High-level overview: average finish time by year."""
    yearly = (
        df.groupby("year", as_index=False)["seconds"]
        .mean()
    )
    yearly["avg_finish_minutes"] = yearly["seconds"] / 60

    fig = px.line(
        yearly,
        x="year",
        y="avg_finish_minutes",
        markers=True,
        title="Average Finish Time by Year",
        labels={
            "year": "Year",
            "avg_finish_minutes": "Average Finish Time (minutes)"
        }
    )

    return fig


def weather_scatter(df, weather_var):
    """Plotly scatter: weather variable vs finish time."""
    plot_df = df.copy()
    plot_df["finish_minutes"] = plot_df["seconds"] / 60
    plot_df = plot_df[
        (plot_df["finish_minutes"] >= 120) &
        (plot_df["finish_minutes"] <= 220)
        ]

    friendly_names = {
        "avg_temp_f": "Average Temperature (°F)",
        "avg_feelslike_f": "Average Feels Like Temperature (°F)",
        "avg_wind_mph": "Average Wind Speed (mph)",
        "avg_humidity": "Average Humidity (%)",
        "total_precip_in": "Total Precipitation (inches)"
    }

    fig = px.scatter(
        plot_df,
        x=weather_var,
        y="finish_minutes",
        color="gender",
        hover_data=["display_name", "year", "finish_time"],
        title=f"{friendly_names[weather_var]} vs Finish Time",
        labels={
            weather_var: friendly_names[weather_var],
            "finish_minutes": "Finish Time (minutes)"
        }
    )

    return fig


def air_quality_chart(df, aq_var):
    """Show selected air quality metric and finish-time distributions."""
    aq_df = df.dropna(subset=[aq_var]).copy()

    if aq_df.empty:
        return pn.pane.Markdown("No air quality data available.")

    aq_df["finish_minutes"] = aq_df["seconds"] / 60

    yearly_aq = (
        aq_df.groupby("year", as_index=False)
        .agg(
            aq_value=(aq_var, "mean"),
            avg_finish_minutes=("finish_minutes", "mean"),
        )
    )

    metric_names = {
        "avg_pm25": "PM2.5",
        "avg_o3": "Ozone",
        "avg_no2": "NO2"
    }

    aq_bar = px.bar(
        yearly_aq,
        x="year",
        y="aq_value",
        title=f"Average {metric_names[aq_var]} by Year",
        labels={
            "year": "Year",
            "aq_value": metric_names[aq_var],
        },
    )

    aq_bar.update_xaxes(
        tickmode="array",
        tickvals=yearly_aq["year"].tolist()
    )

    finish_box = px.box(
        aq_df,
        x="year",
        y="finish_minutes",
        color="gender",
        points="outliers",
        title="Finish Time Distributions for Years with Air Quality Data",
        labels={
            "year": "Year",
            "finish_minutes": "Finish Time (minutes)",
        },
    )

    return pn.Column(
        pn.pane.Plotly(aq_bar),
        pn.pane.Plotly(finish_box),
    )


def drilldown_table(df, selected_year):
    """Detailed drill-down table for selected year."""
    year_df = df[df["year"] == selected_year]

    cols = [
        "display_name",
        "gender",
        "age",
        "finish_time",
        "overall",
        "gender_result",
        "avg_temp_f",
        "avg_wind_mph",
        "avg_humidity",
    ]

    existing_cols = [col for col in cols if col in year_df.columns]
    return year_df[existing_cols].sort_values(["gender", "gender_result"])


def animated_chart(df, selected_year):
    """Animated chart controlled by Panel year player."""
    year_df = df[df["year"] == selected_year].copy()
    year_df["finish_minutes"] = year_df["seconds"] / 60

    yearly_weather = year_df[
        ["avg_temp_f", "avg_wind_mph", "avg_humidity", "total_precip_in"]
    ].mean()

    grouped = (
        year_df.groupby("gender", as_index=False)
        .agg(avg_finish_minutes=("finish_minutes", "mean"))
    )

    fig = px.bar(
        grouped,
        x="gender",
        y="avg_finish_minutes",
        color="gender",
        title=(
            f"Average Finish Time by Gender in {selected_year}<br>"
            f"Temp: {yearly_weather['avg_temp_f']:.1f}°F | "
            f"Wind: {yearly_weather['avg_wind_mph']:.1f} mph | "
            f"Humidity: {yearly_weather['avg_humidity']:.1f}%"
        ),
        labels={
            "gender": "Gender",
            "avg_finish_minutes": "Average Finish Time (minutes)",
        },
        range_y=[120, 200],
    )

    return fig


def create_dashboard():
    """Create the Panel dashboard."""
    df = load_data()

    gender_widget = pn.widgets.Select(
        name="Gender",
        options=["All", "M", "F"],
        value="All"
    )

    year_widget = pn.widgets.IntRangeSlider(
        name="Year Range",
        start=int(df["year"].min()),
        end=int(df["year"].max()),
        value=(int(df["year"].min()), int(df["year"].max())),
        step=1
    )

    weather_widget = pn.widgets.Select(
        name="Weather Variable",
        options={
            "Average Temperature (°F)": "avg_temp_f",
            "Feels Like Temperature (°F)": "avg_feelslike_f",
            "Wind Speed (mph)": "avg_wind_mph",
            "Humidity (%)": "avg_humidity",
            "Precipitation (inches)": "total_precip_in",
        },
        value="avg_temp_f"
    )

    animation_year_widget = pn.widgets.Player(
        name="Animation Year",
        start=int(df["year"].min()),
        end=int(df["year"].max()),
        value=int(df["year"].min()),
        step=1,
        interval=1000,
        loop_policy="loop"
    )

    aq_widget = pn.widgets.Select(
        name="Air Quality Metric",
        options={
            "PM2.5": "avg_pm25",
            "Ozone": "avg_o3",
            "NO2": "avg_no2",
        },
        value="avg_pm25"
    )

    selected_year_widget = pn.widgets.IntSlider(
        name="Drill-down Year",
        start=int(df["year"].min()),
        end=int(df["year"].max()),
        value=int(df["year"].min()),
        step=1
    )

    @pn.depends(gender_widget, year_widget)
    def metrics_view(gender, year_range):
        filtered = filter_data(df, gender, year_range)
        return make_metrics(filtered)

    @pn.depends(gender_widget, year_widget)
    def overview_view(gender, year_range):
        filtered = filter_data(df, gender, year_range)
        return overview_chart(filtered)

    @pn.depends(gender_widget, year_widget, weather_widget)
    def scatter_view(gender, year_range, weather_var):
        filtered = filter_data(df, gender, year_range)
        return weather_scatter(filtered, weather_var)

    @pn.depends(animation_year_widget)
    def animated_view(selected_year):
        return animated_chart(df, selected_year)

    @pn.depends(selected_year_widget)
    def table_view(selected_year):
        return drilldown_table(df, selected_year)

    @pn.depends(gender_widget, year_widget, aq_widget)
    def air_quality_view(gender, year_range, aq_var):
        filtered = filter_data(df, gender, year_range)
        return air_quality_chart(filtered, aq_var)

    dashboard = pn.template.FastListTemplate(
        title="Boston Marathon Weather Impact Dashboard",
        sidebar=[
            "## Filters",
            gender_widget,
            year_widget,
            weather_widget,
            aq_widget,
            selected_year_widget,
        ],
        main=[
            "## Overview",
            metrics_view,
            pn.pane.Plotly(overview_view),
            "## Weather Conditions and Runner Performance",
            "Explore whether race-day weather conditions are associated with runner finish times. Use the Weather Variable dropdown to compare temperature, wind, humidity, and precipitation.",
            pn.pane.Plotly(scatter_view),
            "## Air Quality Case Study",
            "Air quality data are only available for 2017–2018. Use the Air Quality Metric dropdown to compare PM2.5, ozone, and NO2 levels by year, then compare the finish-time distributions below.",
            air_quality_view,
            "## Animated Year-by-Year View",
            "Press play to move through each marathon year and compare average finish times with race-day weather conditions.",
            animation_year_widget,
            pn.pane.Plotly(animated_view),
            "## Drill-down Runner Table",
            pn.widgets.Tabulator(table_view, pagination="remote", page_size=15),
        ],
    )

    return dashboard


dashboard = create_dashboard()
dashboard.servable()