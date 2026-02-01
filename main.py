import calendar
import uuid

import pandas as pd
import streamlit as st
from streamlit_extras.badges import badge

# --- Custom Modules ---
from analysis import (
    compute_album_leaderboard,
    compute_artist_stats,
    compute_lifetime_top_albums,
    compute_lifetime_top_tracks,
    compute_top_albums,
    compute_top_artists,
    compute_top_podcasts,
    compute_top_tracks,
    compute_tracks_leaderboard,
    compute_yearly_artist_stats,
    get_artist_data,
    get_artist_rank,
    get_yearly_artist_rank,
)
from charts import (
    build_heatmap,
    create_minutes_played_by_month_chart,
    create_top_albums_chart,
    create_top_artists_chart,
    create_top_podcasts_chart,
    create_top_tracks_chart,
)
from data_processing import get_example_data, load_and_process_data
from utils import format_minutes_human

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
    "episode_name": "podcastName",
    "episode_show_name": "podcastShowName",
}

# --- Streamlit Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="Spotify History",
    page_icon="🎧",
)


# --- Helper Functions ---
def reset_data():
    st.cache_data.clear()
    st.session_state["use_example_data"] = False
    st.session_state["uploader_key"] = f"history_files_{uuid.uuid4()}"


def render_top_section(
    df_music,
    df_podcasts,
    top_artists,
    top_albums,
    top_tracks,
    top_podcasts,
    title_suffix="",
    top_n=50,
):
    """
    Renders Top Artists + Top Tracks section for a given dataframe.
    Assumes df already represents the desired time slice (lifetime, year, etc.).
    """
    top_artists = top_artists.copy().head(top_n)
    top_albums = top_albums.copy().head(top_n)
    top_tracks = top_tracks.copy().head(top_n)
    top_podcasts = top_podcasts.copy().head(top_n)

    # === UI: Global Metrics Section ===
    min_year, max_year = df_music["year"].min(), df_music["year"].max()
    min_date, max_date = df_music["date"].min(), df_music["date"].max()

    col1, _ = st.columns([2, 7])
    col1.metric(
        "Timespan",
        f"{min_year} - {max_year}",
    )
    col1.caption(f"{min_date} - {max_date}")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 5])
    col1.subheader("Music")
    col2.metric("Artists", df_music["artistName"].nunique())
    col3.metric(
        "Tracks",
        df_music.groupby(["artistName", "trackName"]).size().reset_index().shape[0],
    )
    col4.metric(
        "Listening Time",
        format_minutes_human(df_music["minutesPlayed"].sum()),
    )

    if not df_podcasts.empty:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 5])
        col1.subheader("Podcasts")
        col2.metric("Show", df_podcasts["podcastShowName"].nunique())
        col3.metric(
            "Tracks",
            df_podcasts.groupby(["podcastShowName", "podcastName"])
            .size()
            .reset_index()
            .shape[0],
        )
        col4.metric(
            "Listening Time",
            format_minutes_human(df_podcasts["minutesPlayed"].sum()),
        )

    # --- Top Artists ---
    st.subheader(f"Top {top_n} Artists{title_suffix}")

    minutes_played_chart = create_top_artists_chart(
        top_artists,
        CORNER_RADIUS,
    )

    st.altair_chart(minutes_played_chart, use_container_width=True)

    with st.expander("Top Artists Raw Data"):
        st.write(top_artists["hours"])

    # --- Top Albums ---
    st.subheader(f"Top {top_n} Albums{title_suffix}")

    top_albums_chart = create_top_albums_chart(
        top_albums,
        CORNER_RADIUS,
    )

    st.altair_chart(top_albums_chart, use_container_width=True)

    with st.expander("Top Albums Raw Data"):
        st.write(top_albums)

    # --- Top Tracks ---
    st.subheader(f"Top {top_n} Tracks{title_suffix}")

    top_tracks_chart = create_top_tracks_chart(
        top_tracks,
        CORNER_RADIUS,
    )
    st.altair_chart(top_tracks_chart, use_container_width=True)

    with st.expander("Top Tracks Raw Data"):
        st.write(top_tracks)

    # --- Top Podcasts ---
    if not top_podcasts.empty:
        st.subheader(f"Top {top_n} Podcasts{title_suffix}")

        top_podcasts_chart = create_top_podcasts_chart(
            top_podcasts,
            CORNER_RADIUS,
        )

        st.altair_chart(top_podcasts_chart, use_container_width=True)

        with st.expander("Top Podcasts Raw Data"):
            st.write(top_podcasts)


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

    history_files = st.file_uploader(
        "Upload your Spotify listening history",
        type="json",
        accept_multiple_files=True,
        key=st.session_state.get("uploader_key", "history_files_0"),
    )
    st.info("👆 Upload your Spotify listening history to get started.")

    if not history_files:
        st.caption("Don’t have your exports yet?")
        if st.button("Show example"):
            st.session_state["use_example_data"] = True

    df_music_all = pd.DataFrame()
    df_podcasts_all = pd.DataFrame()

    if history_files:
        df_music_all = load_and_process_data(history_files, CHANGE_COLS)
        df_podcasts_all = load_and_process_data(
            history_files, CHANGE_COLS, content_type="podcast"
        )

    elif st.session_state.get("use_example_data"):
        df_music_all = get_example_data("example_data", CHANGE_COLS)

    if df_music_all.empty:
        renderFooter()
        st.stop()

    st.button("Clear data", on_click=reset_data)

    if st.session_state.get("use_example_data") and not history_files:
        st.caption(
            "👇 Showing example data — upload your own files anytime to replace it."
        )

    st.header("Top Overview")

    # --- Data Calculations for Metrics and Charts ---
    # Calculate top artists for ordering and display

    current_year = max(df_music_all["year"].max(), df_podcasts_all["year"].max())
    df_music_year = df_music_all[df_music_all["year"] == current_year]
    df_podcasts_year = df_podcasts_all[df_podcasts_all["year"] == current_year]

    top_n = 50

    top_artists = compute_top_artists(df_music_all)
    top_albums = compute_top_albums(df_music_all)
    top_tracks = compute_top_tracks(df_music_all)
    top_podcasts = compute_top_podcasts(df_podcasts_all)

    tab_lifetime, tab_year = st.tabs(["Lifetime", f"{current_year}"])

    with tab_lifetime:
        render_top_section(
            df_music_all,
            df_podcasts_all,
            top_artists,
            top_albums,
            top_tracks,
            top_podcasts,
            top_n=top_n,
        )

    with tab_year:
        render_top_section(
            df_music_year,
            df_podcasts_year,
            compute_top_artists(df_music_year),
            compute_top_albums(df_music_year),
            compute_top_tracks(df_music_year),
            compute_top_podcasts(df_podcasts_year),
            title_suffix=f" – {current_year}",
            top_n=top_n,
        )

    # === UI: Artist Analysis Section ===
    st.markdown("---")
    top_artist_order_select = top_artists["artistName"].tolist()

    heatmap_artist = st.selectbox(
        "Select Artist", ["All Artists"] + top_artist_order_select
    )
    st.header(f"Analysis for {heatmap_artist}")
    st.write("Dig a bit deeper into your favorite artists")

    artists = get_artist_data(df_music_all, heatmap_artist)
    artist_stats = compute_artist_stats(artists)

    col0, col1, col2, col3 = st.columns([2, 3, 2, 2])
    rank = get_artist_rank(df_music_all, heatmap_artist)
    col0.metric("Rank", "-" if rank is None else rank)
    col1.metric(
        "Listening Time",
        format_minutes_human(artist_stats["hours"] * 60),
    )
    col2.metric("Total Unique Tracks", artist_stats["unique_tracks"])
    col3.metric("Most Listened Year", artist_stats["most_listened_year"])

    bar_chart = create_minutes_played_by_month_chart(artists, heatmap_artist)
    st.altair_chart(bar_chart, use_container_width=True)

    st.subheader(f"Lifetime Top Albums by {heatmap_artist}")

    lifetime_top_albums = compute_lifetime_top_albums(artists)

    display_lifetime_top_albums = lifetime_top_albums.copy()
    display_lifetime_top_albums["Listening Time"] = display_lifetime_top_albums[
        "Total_Minutes"
    ].apply(format_minutes_human)

    st.dataframe(
        display_lifetime_top_albums.drop(columns=["Total_Minutes"]),
        use_container_width=True,
    )

    st.subheader(f"Lifetime Top Tracks by {heatmap_artist}")

    lifetime_top_tracks = compute_lifetime_top_tracks(artists)

    display_lifetime_top_tracks = lifetime_top_tracks.copy()
    display_lifetime_top_tracks["Listening Time"] = display_lifetime_top_tracks[
        "Total_Minutes"
    ].apply(format_minutes_human)

    st.dataframe(
        display_lifetime_top_tracks.drop(columns=["Total_Minutes"]),
        use_container_width=True,
    )

    # === UI: Yearly Analysis Section ===
    st.markdown("---")
    sorted_years_reversed = sorted(artists["year"].unique(), reverse=True)

    year_select = st.selectbox(
        "Select year for deeper analysis",
        sorted_years_reversed,
        # sorted_years_reversed.index(most_listened_year),
    )

    st.header(f"{heatmap_artist} in {year_select}")
    st.subheader("Stats")

    col1_yearly, col2_yearly, col3_yearly = st.columns(3)

    yearly_rank = get_yearly_artist_rank(
        df_music_all,
        heatmap_artist,
        year_select,
    )

    yearly_stats = compute_yearly_artist_stats(
        df_music_all,
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
    st.altair_chart(artist_heat, use_container_width=True)

    month_options = ["All months"] + [calendar.month_name[m] for m in range(1, 13)]

    month_select = st.selectbox("Filter by month", month_options)

    month = (
        None
        if month_select == "All months"
        else list(calendar.month_name).index(month_select)
    )

    month_label = "" if month is None else f" {calendar.month_name[month]}"

    st.subheader(f"Album Leaderboard for {year_select}{month_label}")

    yearly_album_leaderboard = compute_album_leaderboard(
        heatmap_data_yearly, year_select, month
    )

    display_yearly_album_leaderboard = yearly_album_leaderboard.copy()
    display_yearly_album_leaderboard["Listening Time"] = (
        display_yearly_album_leaderboard["Total_Minutes"].apply(format_minutes_human)
    )

    st.dataframe(
        display_yearly_album_leaderboard.drop(columns=["Total_Minutes"]),
        use_container_width=True,
    )

    st.subheader(f"Track Leaderboard for {year_select}{month_label}")

    yearly_track_leaderboard = compute_tracks_leaderboard(
        heatmap_data_yearly, year_select, month
    )

    display_yearly_track_leaderboard = yearly_track_leaderboard.copy()
    display_yearly_track_leaderboard["Listening Time"] = (
        display_yearly_track_leaderboard["Total_Minutes"].apply(format_minutes_human)
    )

    st.dataframe(
        display_yearly_track_leaderboard.drop(columns=["Total_Minutes"]),
        use_container_width=True,
    )

    renderFooter()


if __name__ == "__main__":
    main()
