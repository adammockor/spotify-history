import pandas as pd
import streamlit as st
import calendar
from streamlit_extras.badges import badge

# --- Custom Modules ---
from data_processing import load_and_process_data
from charts import (
    create_top_artists_chart,
    create_top_songs_chart,
    create_minutes_played_by_month_chart,
    build_heatmap,
)

pd.set_option("mode.chained_assignment", None)

# --- Constants ---
CORNER_RADIUS = 4
DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

CHANGE_COLS = {
    "master_metadata_track_name": "trackName",
    "master_metadata_album_artist_name": "artistName",
    "ts": "endTime",
    "ms_played": "msPlayed",
}

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="My Spotify History")


# --- Helper Functions ---
def clear_data():
    st.cache_data.clear()
    if "history_files" in st.session_state:
        del st.session_state["history_files"]


def main():
    # === UI: Header Section ===
    st.title("🎁 Spotify History 🎶")
    st.markdown("Deep dive into your all-time listening data.")

    col1, col2 = st.columns(2)
    col1.markdown(
        """
        ## About
        This app helps you dig into your listening history to help you learn about yourself. It shows you your top songs and artists and visualizes your listening history. We **do not** save your data and all the code is __open source__. I hope you enjoy it!
        """
    )
    with col2:
        col2.markdown(
            """
        ## How to use
        1. Download your Spotify listening history from [here](https://www.spotify.com/us/account/privacy/). Note that this takes about 5 days for the last year or 30 days for your entire listening history
        2. Unzip the file and attach all of the files like `StreamingHistory#.json` or `endsong_#.json` into the app
        3. Run the app and visualize your music history!
        """
        )
        badge("twitter", "TYLERSlMONS", "https://twitter.com/TYLERSlMONS")

    # === Data Loading Section ===
    history_files = st.file_uploader(
        "Upload your Spotify listening history",
        type="json",
        accept_multiple_files=True,
        key="history_files",
    )

    all_data = pd.DataFrame()
    if history_files:
        try:
            all_data = load_and_process_data(history_files, CHANGE_COLS)
            st.button("Clear data", on_click=clear_data)
        except Exception as e:
            st.error(
                f"Error processing uploaded files: {e}. Please ensure you've uploaded valid Spotify JSON files."
            )
            st.stop()
    else:
        st.info("👆 Upload your Spotify listening history to get started!")
        st.stop()

    all_data_full_songs = all_data.copy()

    # --- Data Calculations for Metrics and Charts ---
    # Calculate top artists for ordering and display
    grouped_artist_total = (
        all_data.groupby(["artistName"])["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
    )
    top_artist = grouped_artist_total.index[0]
    top_artists_total_hours = (grouped_artist_total / 60).rename("Hours")

    # Merge to get rank and order
    all_data_with_rank = all_data.merge(
        top_artists_total_hours.reset_index(), on="artistName", how="left"
    )
    all_data_with_rank["rank"] = all_data_with_rank["Hours"].rank(ascending=False)
    top_artists_order = (
        all_data_with_rank.sort_values("rank")["artistName"].unique().tolist()
    )

    min_year, max_year = all_data["year"].min(), all_data["year"].max()

    # === UI: Global Metrics Section ===
    col1, col2, col3, col4 = st.columns([4, 2, 3, 2])
    col1.metric("Timespan", f"{min_year} - {max_year}")
    col2.metric("Artists", all_data["artistName"].nunique())
    col3.metric(
        "Tracks",
        all_data.groupby(["artistName", "trackName"]).size().reset_index().shape[0],
    )
    col4.metric("Hours", int(all_data["minutesPlayed"].sum() / 60))

    # === UI: Top Artists Section ===
    st.markdown("---")
    st.subheader("Top Artists")
    minutes_played_chart = create_top_artists_chart(
        top_artists_total_hours.reset_index(), top_artists_order, CORNER_RADIUS
    )
    st.altair_chart(minutes_played_chart, use_container_width=True)
    with st.expander("Top Artists Raw Data"):
        st.write(top_artists_total_hours)

    # === UI: Top Songs Section ===
    TOP_SONG_N = 50
    top_songs_df = all_data_full_songs.groupby(
        ["artistName", "trackName"], as_index=False
    ).agg(Listens=("msPlayed", "count"))
    top_songs_df = top_songs_df.sort_values("Listens", ascending=False)
    top_songs_df["rank"] = top_songs_df["Listens"].rank(method="first", ascending=False)
    top_songs_order = (
        top_songs_df.sort_values("rank").head(TOP_SONG_N)["trackName"].tolist()
    )

    st.markdown("---")
    st.subheader("Top 40 Songs")
    day_chart = create_top_songs_chart(
        top_songs_df, top_songs_order, top_artists_order, CORNER_RADIUS, TOP_SONG_N
    )
    st.altair_chart(day_chart, use_container_width=True)
    with st.expander("Top Song Raw Data"):
        st.write(top_songs_df)

    # === UI: Artist Analysis Section ===
    st.markdown("---")
    top_artist_order_select = (
        all_data.groupby("artistName")["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
        .index.to_list()
    )

    heatmap_artist = st.selectbox(
        "Select Artist", ["All Artists"] + top_artist_order_select
    )
    st.title(f"Analysis for {heatmap_artist}")
    st.write("Dig a bit deeper into your favorite artists")

    if heatmap_artist == "All Artists":
        heatmap_data = all_data
        all_artist_raw = all_data
    else:
        heatmap_data = all_data[all_data["artistName"] == heatmap_artist]
        all_artist_raw = all_data.query(f"artistName == '{heatmap_artist}'")

    total_lifetime_hours = heatmap_data["minutesPlayed"].sum() / 60
    total_unique_tracks = heatmap_data["trackName"].nunique()
    most_listened_year = (
        heatmap_data.groupby("year")["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
        .index[0]
    )

    col0, col1, col2, col3 = st.columns(4)
    if heatmap_artist == "All Artists":
        col0.metric(f"Rank", "-")
    else:
        col0.metric(f"Rank", f"{top_artist_order_select.index(heatmap_artist) + 1}")
    col1.metric("Total Hours", f"{total_lifetime_hours:.2f}")
    col2.metric("Total Unique Tracks", total_unique_tracks)
    col3.metric("Most Listened Year", most_listened_year)

    bar_chart = create_minutes_played_by_month_chart(all_artist_raw, heatmap_artist)
    st.altair_chart(bar_chart, use_container_width=True)

    top_songs_artist = all_artist_raw.groupby(
        ["trackName", "artistName"], as_index=False
    ).agg(minutesPlayed=("minutesPlayed", "sum"), date=("date", "count"))
    top_songs_artist = top_songs_artist.rename(
        columns={
            "date": "Listens",
            "minutesPlayed": "Total Minutes",
            "artistName": "Artist",
            "trackName": "Track",
        }
    )
    top_songs_artist = top_songs_artist.sort_values(by="Listens", ascending=False)
    top_songs_artist = top_songs_artist.drop("Artist", axis=1)
    top_songs_artist = top_songs_artist.set_index("Track")
    top_songs_artist = top_songs_artist.style.format({"Total Minutes": "{:.1f}"})
    st.subheader(f"Lifetime Top Songs by {heatmap_artist}")
    st.dataframe(top_songs_artist, use_container_width=True)

    # === UI: Yearly Analysis Section ===
    st.markdown("---")
    sorted_years_reversed = sorted(all_artist_raw["year"].unique(), reverse=True)
    top_year_index = sorted_years_reversed.index(most_listened_year)

    year_select = st.selectbox(
        f"Select year for deeper analysis", sorted_years_reversed, top_year_index
    )
    heatmap_data_yearly = all_artist_raw[all_artist_raw["year"] == year_select]

    st.title(f"{heatmap_artist} in {year_select}")

    total_listened_hours_yearly = heatmap_data_yearly["minutesPlayed"].sum() / 60

    st.subheader("Stats")

    col1_yearly, col2_yearly, col3_yearly = st.columns(3)

    yearly_rank = (
        all_data_with_rank[all_data_with_rank["year"] == year_select]
        .groupby(["artistName"])
        .sum(numeric_only=True)
        .sort_values("minutesPlayed", ascending=False)
        .reset_index()
    )
    yearly_rank["rank"] = yearly_rank["minutesPlayed"].rank(ascending=False)
    yearly_rank = yearly_rank[yearly_rank["artistName"] == heatmap_artist]

    if heatmap_artist == "All Artists":
        col1_yearly.metric(f"Artist Rank in {year_select}", "-")
    else:
        col1_yearly.metric(
            f"Artist Rank in {year_select}", f"{yearly_rank['rank'].values[0]:.0f}"
        )
    col2_yearly.metric(
        f"Hours Played in {year_select}", f"{total_listened_hours_yearly:.0f}"
    )
    col3_yearly.metric(
        f"Unique Tracks Played in {year_select}",
        f"{len(heatmap_data_yearly['trackName'].unique()):.0f}",
    )

    artist_heat = build_heatmap(
        heatmap_data_yearly, DAYS_OF_WEEK, CORNER_RADIUS, heatmap_artist, year_select
    )
    st.altair_chart(artist_heat, use_container_width=True)

    st.subheader(f"Track Leaderboard for {year_select}")

    track_leaderboard_yearly = heatmap_data_yearly.groupby(
        ["trackName", "artistName"]
    ).agg(minutesPlayed=("minutesPlayed", "sum"), endTime=("endTime", "count"))
    track_leaderboard_yearly = track_leaderboard_yearly.reset_index()
    track_leaderboard_yearly = track_leaderboard_yearly.rename(
        columns={
            "endTime": "Listens",
            "minutesPlayed": "Total Minutes",
            "artistName": "Artist",
            "trackName": "Track",
        }
    )
    track_leaderboard_yearly = track_leaderboard_yearly.sort_values(
        "Total Minutes", ascending=False
    )
    track_leaderboard_yearly = track_leaderboard_yearly.set_index("Track")
    track_leaderboard_yearly = track_leaderboard_yearly.sort_values(
        "Listens", ascending=False
    )
    track_leaderboard_yearly = track_leaderboard_yearly.style.format(
        {"Total Minutes": "{:.1f}"}
    )
    st.dataframe(track_leaderboard_yearly, use_container_width=True)


if __name__ == "__main__":
    main()
