# testing merging
"""
Tests for clean_merged.py
"""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from clean_merged import clean_merged_data, KEEP_COLUMNS


# ---- fixtures ----

@pytest.fixture
def base_row():
    """Minimal valid merged row with all required fields"""
    return {
        "year": 2015,
        "race_date": "2015-04-20",
        "display_name": "john doe",
        "age": 30,
        "gender": "m",
        "residence": "Boston, MA",
        "finish_time": "3:45:00",
        "seconds": 13500,
        "overall": 500,
        "gender_result": 400,
        "division_result": 50,
        "pace": "8:35",
        "avg_temp_f": 55.0,
        "avg_feelslike_f": 53.0,
        "avg_wind_mph": 10.0,
        "avg_humidity": 70.0,
        "total_precip_in": 0.0,
        "daily_maxtemp_f": 62.0,
        "daily_mintemp_f": 48.0,
        "daily_totalprecip_in": 0.0,
        "avg_no2": 0.01,
        "avg_o3": 0.04,
        "avg_pm25": 8.5,
    }


@pytest.fixture
def valid_df(base_row):
    """DataFrame with a few valid rows across different years"""
    rows = [
        {**base_row, "year": 2010, "race_date": "2010-04-19"},
        {**base_row, "year": 2015, "race_date": "2015-04-20"},
        {**base_row, "year": 2018, "race_date": "2018-04-16"},
    ]
    return pd.DataFrame(rows)


# ---- tests ----

def test_year_filter_removes_out_of_range(base_row):
    """Rows outside 2010-2018 should be dropped"""
    rows = [
        {**base_row, "year": 2009},
        {**base_row, "year": 2015},
        {**base_row, "year": 2019},
    ]
    df = pd.DataFrame(rows)
    result = clean_merged_data(df)
    assert set(result["year"].unique()) == {2015}


def test_keeps_only_valid_columns(valid_df):
    """Output should only contain columns from KEEP_COLUMNS that exist in input"""
    extra_col_df = valid_df.copy()
    extra_col_df["extra_column"] = "junk"
    result = clean_merged_data(extra_col_df)
    for col in result.columns:
        assert col in KEEP_COLUMNS


def test_drops_rows_missing_required_fields(base_row):
    """Rows missing name, gender, finish_time, or seconds should be dropped"""
    rows = [
        {**base_row},                                  # valid
        {**base_row, "display_name": None},            # missing name
        {**base_row, "seconds": None},                 # missing seconds
        {**base_row, "finish_time": None},             # missing finish_time
        {**base_row, "gender": None},                  # missing gender
    ]
    df = pd.DataFrame(rows)
    result = clean_merged_data(df)
    assert len(result) == 1


def test_drops_rows_missing_weather(base_row):
    """Rows missing avg_temp_f, avg_wind_mph, or avg_humidity should be dropped."""
    rows = [
        {**base_row},                                  # valid
        {**base_row, "avg_temp_f": None},              # missing temp
        {**base_row, "avg_wind_mph": None},            # missing wind
        {**base_row, "avg_humidity": None},            # missing humidity
    ]
    df = pd.DataFrame(rows)
    result = clean_merged_data(df)
    assert len(result) == 1


def test_name_and_gender_formatting(base_row):
    """display_name should be title case, gender should be uppercase."""
    df = pd.DataFrame([{**base_row, "display_name": "jane doe", "gender": "f"}])
    result = clean_merged_data(df)
    assert result["display_name"].iloc[0] == "Jane Doe"
    assert result["gender"].iloc[0] == "F"


def test_residence_filled_when_missing(base_row):
    """Null residence should be filled with 'Unknown'"""
    df = pd.DataFrame([{**base_row, "residence": None}])
    result = clean_merged_data(df)
    assert result["residence"].iloc[0] == "Unknown"


def test_sorted_by_year_gender_gender_result(base_row):
    """Output should be sorted by year, then gender, then gender_result"""
    rows = [
        {**base_row, "year": 2015, "gender": "M", "gender_result": 300},
        {**base_row, "year": 2015, "gender": "F", "gender_result": 1},
        {**base_row, "year": 2010, "gender": "M", "gender_result": 100},
    ]
    df = pd.DataFrame(rows)
    result = clean_merged_data(df)
    years = result["year"].tolist()
    assert years == sorted(years)
    assert result.iloc[0]["year"] == 2010


def test_mock_read_csv_and_save(valid_df, tmp_path):
    """Mock pd.read_csv and to_csv to verify main() reads and writes correctly."""
    output_path = tmp_path / "merged_clean.csv"

    with patch("clean_merged.pd.read_csv", return_value=valid_df) as mock_read, \
         patch("clean_merged.OUTPUT_PATH", str(output_path)), \
         patch("clean_merged.INPUT_PATH", "data/merged.csv"):

        from clean_merged import main
        main()

        mock_read.assert_called_once_with("data/merged.csv")
        assert output_path.exists()
        saved = pd.read_csv(output_path)
        assert len(saved) == 3
        assert "display_name" in saved.columns

def test_api_mock_returns_dataframe(base_row):
    """Mock requests.get to verify get_air_quality_data() handles a fake API response."""
    from aq_api import get_air_quality_data

    fake_response = {
        "results": [{
            "date": {
                "utc": "2015-04-20T14:00:00Z",
                "local": "2015-04-20T10:00:00-04:00"
            },
            "value": 8.5
        }]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_response

    with patch("aq_api.requests.get", return_value=mock_resp), \
         patch.dict("os.environ", {"OPENAQ_KEY": "fake_key"}):
        df = get_air_quality_data()
        assert not df.empty
        assert "value" in df.columns
        assert df["value"].iloc[0] == 8.5


def test_data_validation_value_ranges(base_row):
    """Cleaned data should not contain nulls in key numeric columns."""
    df = pd.DataFrame([base_row])
    result = clean_merged_data(df)
    assert result["seconds"].notna().all()
    assert result["avg_temp_f"].notna().all()
    assert result["avg_humidity"].notna().all()