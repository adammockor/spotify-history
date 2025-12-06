# Spotify History Analyzer

## Project Overview

This project is an interactive Streamlit application designed to visualize and analyze Spotify listening history. It allows users to upload their personal Spotify data (JSON files) and explore their listening habits through various charts and metrics. The application runs locally, ensuring data privacy.

**Key Features:**
*   **Global Analysis:** Overview of top artists and top songs by play count and duration.
*   **Artist Deep Dive:** Detailed stats for specific artists, including lifetime hours, unique tracks, and monthly listening trends.
*   **Temporal Analysis:** Heatmaps showing listening habits by day of the week and week of the year.
*   **Interactive Filtering:** Drill down by artist and year.

## Architecture & Technologies

*   **Language:** Python
*   **Framework:** [Streamlit](https://streamlit.io/)
*   **Data Processing:** [Pandas](https://pandas.pydata.org/)
*   **Visualization:** [Altair](https://altair-viz.github.io/)
*   **Data Source:** User-uploaded JSON files (standard Spotify privacy export format, e.g., `StreamingHistory#.json`).

## Building and Running

### Prerequisites

Ensure you have Python installed. It is recommended to use a virtual environment.

### Installation

Install the required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### Running the Application

Launch the Streamlit dashboard:

```bash
streamlit run spotify_history.py
```

This will open the application in your default web browser (usually at `http://localhost:8501`).

## Data Handling

The application expects Spotify streaming history JSON files.
1.  **Upload:** Use the file uploader in the sidebar/main area to select your JSON files.
2.  **Processing:** The app concatenates multiple files, cleans the data (renaming columns, converting timestamps), and filters out short plays (less than ~10 seconds).
3.  **Privacy:** All processing happens in memory during the session; no data is sent to external servers.

## Key Files

*   `spotify_history.py`: The main application script containing all UI logic, data processing, and visualization code.
*   `requirements.txt`: List of Python dependencies.
*   `.streamlit/config.toml`: Streamlit configuration file (e.g., theme settings).
*   `example_data_2/`: Directory containing sample data files for testing purposes.
