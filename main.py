import pandas as pd
import streamlit as st
from streamlit_extras.badges import badge

# --- Custom Modules ---
from analysis import (
    compute_artist_stats,
    compute_lifetime_top_albums,
    compute_lifetime_top_tracks,
    compute_top_albums,
    compute_top_artists,
    compute_top_tracks,
    compute_yearly_album_leaderboard,
    compute_yearly_artist_stats,
    compute_yearly_tracks_leaderboard,
    get_artist_data,
    get_artist_rank,
    get_yearly_artist_rank,
)
from data_processing import load_and_process_data
from charts import (
    create_top_albums_chart,
    create_top_artists_chart,
    create_top_tracks_chart,
    create_minutes_played_by_month_chart,
    build_heatmap,
)
from utils import format_minutes_human, get_album_art

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
    "master_metadata_album_album_name": "albumName",
    "ts": "endTime",
    "ms_played": "msPlayed",
}

# --- Streamlit Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="Spotify History",
    page_icon="🎧",
)


# --- Helper Functions ---
def clear_data():
    st.cache_data.clear()
    if "history_files" in st.session_state:
        del st.session_state["history_files"]


def renderFooter():
    st.markdown("---")

    st.caption(
        "Originally inspired by "
        "[Tyler Simons](https://share.streamlit.io/user/tyler-simons)"
    )

    badge(
        type="github",
        name="adammockor/spotify-history",
        url="https://github.com/adammockor/spotify-history",
    )


def main():
    # === UI: Header Section ===
    st.markdown(
        """
    <h1 style="margin-bottom: 0;">
        🎧 <span style="color:#1DB954;">Spotify</span> History
    </h1>
    """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "Explore your personal Spotify listening history — top artists, albums, tracks, and listening patterns over time."
    )

    col1, col2 = st.columns(2)
    with col1:
        col1.markdown(
            """
            ## About
            - No login required  
            - Your data is processed temporarily and never stored  
            - Open source — all processing is visible in the code
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
        renderFooter()
        st.stop()

    # --- Data Calculations for Metrics and Charts ---
    # Calculate top artists for ordering and display

    current_year = all_data["year"].max()
    year_df = all_data[all_data["year"] == current_year]

    top_artists = compute_top_artists(all_data)
    top_albums = compute_top_albums(all_data)

    def render_top_section(
        df,
        top_artists,
        top_albums,
        title_suffix="",
        top_song_n=50,
    ):
        """
        Renders Top Artists + Top Songs section for a given dataframe.
        Assumes df already represents the desired time slice (lifetime, year, etc.).
        """

        # === UI: Global Metrics Section ===
        min_year, max_year = df["year"].min(), df["year"].max()
        min_date, max_date = df["date"].min(), df["date"].max()

        col1, col2, col3, col4 = st.columns([2, 2, 2, 5])
        col1.metric("Timespan", f"{min_year} - {max_year}")
        col1.caption(f"{min_date} - {max_date}")
        col2.metric("Artists", df["artistName"].nunique())
        col3.metric(
            "Tracks",
            df.groupby(["artistName", "trackName"]).size().reset_index().shape[0],
        )

        col4.metric(
            "Listening Time",
            format_minutes_human(df["minutesPlayed"].sum()),
        )

        # --- Top Artists ---
        st.subheader(f"Top Artists{title_suffix}")

        minutes_played_chart = create_top_artists_chart(
            top_artists["hours"].reset_index(),
            top_artists["order"],
            CORNER_RADIUS,
        )

        st.altair_chart(minutes_played_chart, width="stretch")

        with st.expander("Top Artists Raw Data"):
            st.write(top_artists["hours"])

        # --- Top Albums ---
        st.subheader(f"Top Albums{title_suffix}")

        top_albums_chart = create_top_albums_chart(
            top_albums["df"],
            top_albums["order"],
            CORNER_RADIUS,
        )

        st.altair_chart(top_albums_chart, width="stretch")

        with st.expander("Top Albums Raw Data"):
            st.write(top_albums["df"])

        # --- Top Songs ---
        st.subheader(f"Top {top_song_n} Songs{title_suffix}")

        top_tracks = compute_top_tracks(df, top_song_n)

        top_tracks_chart = create_top_tracks_chart(
            top_tracks["df"],
            top_tracks["order"],
            top_artists["order"],
            CORNER_RADIUS,
            top_song_n,
        )
        st.altair_chart(top_tracks_chart, width="stretch")

        with st.expander("Top Song Raw Data"):
            st.write(top_tracks["df"])

    st.header("Top Overview")

    tab_lifetime, tab_year = st.tabs(["Lifetime", f"{current_year}"])

    with tab_lifetime:
        render_top_section(all_data, top_artists, top_albums)

    with tab_year:
        render_top_section(
            year_df,
            compute_top_artists(year_df),
            compute_top_albums(year_df),
            title_suffix=f" – {current_year}",
        )

    # === UI: Artist Analysis Section ===
    st.markdown("---")
    top_artist_order_select = top_artists["order"]

    heatmap_artist = st.selectbox(
        "Select Artist", ["All Artists"] + top_artist_order_select
    )
    st.header(f"Analysis for {heatmap_artist}")
    st.write("Dig a bit deeper into your favorite artists")

    artists = get_artist_data(all_data, heatmap_artist)
    artist_stats = compute_artist_stats(artists)

    col0, col1, col2, col3 = st.columns([2, 3, 2, 2])
    rank = get_artist_rank(all_data, heatmap_artist)
    col0.metric("Rank", "-" if rank is None else rank)
    col1.metric(
        f"Listening Time",
        format_minutes_human(artist_stats["hours"] * 60),
    )
    col2.metric("Total Unique Tracks", artist_stats["unique_tracks"])
    col3.metric("Most Listened Year", artist_stats["most_listened_year"])

    bar_chart = create_minutes_played_by_month_chart(artists, heatmap_artist)
    st.altair_chart(bar_chart, width="stretch")

    st.subheader(f"Lifetime Top Albums by {heatmap_artist}")

    lifetime_top_albums = compute_lifetime_top_albums(artists)

    display_lifetime_top_albums = lifetime_top_albums.copy()
    display_lifetime_top_albums["Listening Time"] = display_lifetime_top_albums[
        "Total_Minutes"
    ].apply(format_minutes_human)

    st.dataframe(
        display_lifetime_top_albums.drop(columns=["Total_Minutes"]),
        width="stretch",
    )

    st.subheader(f"Lifetime Top Songs by {heatmap_artist}")

    lifetime_top_tracks = compute_lifetime_top_tracks(artists)

    display_lifetime_top_tracks = lifetime_top_tracks.copy()
    display_lifetime_top_tracks["Listening Time"] = display_lifetime_top_tracks[
        "Total_Minutes"
    ].apply(format_minutes_human)

    st.dataframe(
        display_lifetime_top_tracks.drop(columns=["Total_Minutes"]),
        width="stretch",
    )

    # === UI: Yearly Analysis Section ===
    st.markdown("---")
    sorted_years_reversed = sorted(artists["year"].unique(), reverse=True)

    year_select = st.selectbox(
        f"Select year for deeper analysis",
        sorted_years_reversed,
        # sorted_years_reversed.index(most_listened_year),
    )

    st.header(f"{heatmap_artist} in {year_select}")
    st.subheader("Stats")

    col1_yearly, col2_yearly, col3_yearly = st.columns(3)

    yearly_rank = get_yearly_artist_rank(
        all_data,
        heatmap_artist,
        year_select,
    )

    yearly_stats = compute_yearly_artist_stats(
        all_data,
        heatmap_artist,
        year_select,
    )

    heatmap_data_yearly = artists[artists["year"] == year_select]

    col1_yearly.metric(
        f"Artist Rank in {year_select}",
        "-" if yearly_rank is None else yearly_rank,
    )

    col2_yearly.metric(
        f"Listening Time in {year_select}",
        format_minutes_human(yearly_stats["hours"] * 60),
    )

    col3_yearly.metric(
        f"Unique Tracks Played in {year_select}",
        yearly_stats["unique_tracks"],
    )

    artist_heat = build_heatmap(
        heatmap_data_yearly, DAYS_OF_WEEK, CORNER_RADIUS, heatmap_artist, year_select
    )
    st.altair_chart(artist_heat, width="stretch")

    st.subheader(f"Album Leaderboard for {year_select}")

    yearly_album_leaderboard = compute_yearly_album_leaderboard(heatmap_data_yearly)

    display_yearly_album_leaderboard = yearly_album_leaderboard.copy()
    display_yearly_album_leaderboard["Listening Time"] = (
        display_yearly_album_leaderboard["Total_Minutes"].apply(format_minutes_human)
    )

    st.dataframe(
        display_yearly_album_leaderboard.drop(columns=["Total_Minutes"]),
        width="stretch",
    )

    st.subheader(f"Track Leaderboard for {year_select}")

    yearly_track_leaderboard = compute_yearly_tracks_leaderboard(heatmap_data_yearly)

    display_yearly_track_leaderboard = yearly_track_leaderboard.copy()
    display_yearly_track_leaderboard["Listening Time"] = (
        display_yearly_track_leaderboard["Total_Minutes"].apply(format_minutes_human)
    )

    st.dataframe(
        display_yearly_track_leaderboard.drop(columns=["Total_Minutes"]),
        width="stretch",
    )

    renderFooter()


if __name__ == "__main__":
    main()
