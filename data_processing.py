import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import datetime as dt
import calendar
import os
import json # Added for handling JSON data

# Helper function
def get_month_weeks(year: int) -> list[int]:
    month_weeks = []
    for month in range(1, 13):
        if month == 12:
            first_day = dt.date(year, month, 15)
        else:
            first_day = dt.date(year, month, 3)
        first_day_week = first_day.isocalendar()[1]
        month_weeks.append(first_day_week)
    return month_weeks

# Helper function
def build_date_from_pieces(row: pd.Series) -> dt.date:
    return datetime.strptime(f"{row['year']}-{row['week']}-{row['day_of_week_str']}", "%Y-%W-%A").date()

@st.cache_data()
def load_and_process_data(
    uploaded_files: list, change_cols: dict, min_ms_played: int = 10000, min_minutes_played_artist: int = 5
) -> pd.DataFrame:
    if not uploaded_files:
        st.info("Upload your Spotify listening history to see your matches")
        st.stop()

    listening_history = []
    for file in uploaded_files:
        try:
            # Decode bytes to string and then load with json.loads
            file_content = file.read().decode('utf-8')
            listening_history.append(pd.DataFrame(json.loads(file_content)))
        except Exception as e:
            st.error(f"There was an error reading the file {file.name}: {e}. Please remove the file and try again.")
            st.stop()

    all_data = pd.concat(listening_history).reset_index(drop=True)

    # Rename columns
    all_data = all_data.rename(columns={i: change_cols[i] for i in change_cols if i in all_data.columns})

    # Add features
    all_data["endTime"] = pd.to_datetime(all_data["endTime"])
    all_data["endTime"] = pd.Series([(i + timedelta(hours=16)) for i in all_data.endTime]) # This seems arbitrary, might need review
    all_data["date"] = [i.date() for i in all_data["endTime"]]
    all_data["dow"] = [i.weekday() for i in all_data["endTime"]]
    all_data["day_of_week_str"] = all_data["dow"].apply(lambda x: calendar.day_name[x])
    all_data["time"] = [i.hour for i in all_data["endTime"]]
    all_data["week"] = all_data["endTime"].dt.isocalendar().week
    all_data["year"] = all_data["endTime"].dt.isocalendar().year.astype(int)
    all_data["minutesPlayed"] = all_data["msPlayed"] / 60000

    # Filter for minimum msPlayed
    all_data = all_data[all_data["msPlayed"] > min_ms_played]

    # Filter for minimum minutes played grouped by artist
    all_data = all_data.groupby("artistName").filter(lambda x: x["minutesPlayed"].sum() > min_minutes_played_artist)

    return all_data

# Function to get example data for local development/testing
def get_example_data(example_data_path: str, change_cols: dict) -> pd.DataFrame:
    example_data_files = []
    for root, _, files in os.walk(example_data_path):
        for file_name in files:
            if file_name.endswith(".json"):
                file_path = os.path.join(root, file_name)
                try:
                    example_data_files.append(pd.read_json(file_path))
                except Exception as e:
                    st.error(f"Error reading example file {file_name}: {e}")
                    st.stop()
    if example_data_files:
        all_data = pd.concat(example_data_files).reset_index(drop=True)
        all_data = all_data.rename(columns={i: change_cols[i] for i in change_cols if i in all_data.columns})
        
        # Apply the same feature engineering as for uploaded data
        all_data["endTime"] = pd.to_datetime(all_data["endTime"])
        all_data["endTime"] = pd.Series([(i + timedelta(hours=16)) for i in all_data.endTime])
        all_data["date"] = [i.date() for i in all_data["endTime"]]
        all_data["dow"] = [i.weekday() for i in all_data["endTime"]]
        all_data["day_of_week_str"] = all_data["dow"].apply(lambda x: calendar.day_name[x])
        all_data["time"] = [i.hour for i in all_data["endTime"]]
        all_data["week"] = all_data["endTime"].dt.isocalendar().week
        all_data["year"] = all_data["endTime"].dt.isocalendar().year.astype(int)
        all_data["minutesPlayed"] = all_data["msPlayed"] / 60000
        all_data = all_data[all_data["msPlayed"] > 10000]
        all_data = all_data.groupby("artistName").filter(lambda x: x["minutesPlayed"].sum() > 5)
        
        return all_data
    return pd.DataFrame()
