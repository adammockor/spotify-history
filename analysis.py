import pandas as pd


def get_artist_order(df: pd.DataFrame) -> list[str]:
    return (
        df.groupby("artistName")["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
        .index.to_list()
    )


def get_artist_data(df: pd.DataFrame, artist: str) -> pd.DataFrame:
    if artist == "All Artists":
        return df
    return df[df["artistName"] == artist]


def compute_lifetime_artist_stats(df: pd.DataFrame) -> dict:
    return {
        "hours": df["minutesPlayed"].sum() / 60,
        "unique_tracks": df["trackName"].nunique(),
        "most_listened_year": (
            df.groupby("year")["minutesPlayed"].sum(numeric_only=True).idxmax()
        ),
    }


def get_artist_rank(df: pd.DataFrame, artist: str) -> int | None:
    """
    Returns 1-based rank of artist by total minutes played.
    Returns None for 'All Artists' or if artist not found.
    """
    if artist == "All Artists":
        return None

    order = get_artist_order(df)

    if artist not in order:
        return None

    return order.index(artist) + 1


def get_yearly_artist_rank(
    df: pd.DataFrame,
    artist: str,
    year: int,
) -> int | None:
    """
    Returns 1-based rank of artist by minutes played in a given year.
    Returns None for 'All Artists' or if artist not found.
    """
    if artist == "All Artists":
        return None

    yearly = (
        df[df["year"] == year]
        .groupby("artistName")["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
    )

    if artist not in yearly.index:
        return None

    return yearly.index.get_loc(artist) + 1


def compute_yearly_artist_stats(
    df: pd.DataFrame,
    artist: str,
    year: int,
) -> dict:
    """
    Returns yearly stats for an artist (or all artists):
    - hours
    - unique_tracks
    """
    if artist == "All Artists":
        yearly = df[df["year"] == year]
    else:
        yearly = df[(df["year"] == year) & (df["artistName"] == artist)]

    return {
        "hours": yearly["minutesPlayed"].sum() / 60,
        "unique_tracks": yearly["trackName"].nunique(),
    }


def compute_lifetime_top_tracks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns lifetime top tracks table for a given artist dataframe.
    Columns:
        - Track (index)
        - Listens
        - Total Minutes
    """
    tracks = (
        df.groupby(["trackName", "artistName"], as_index=False)
        .agg(
            Listens=("date", "count"),
            Total_Minutes=("minutesPlayed", "sum"),
        )
        .sort_values("Listens", ascending=False)
        .drop(columns="artistName")
        .set_index("trackName")
    )

    return tracks


def compute_top_artists(df: pd.DataFrame) -> dict:
    """
    Computes all data needed for the 'Top Artists' section.
    Returns plain data structures only.
    """

    artist_minutes = (
        df.groupby("artistName")["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
    )

    artist_hours = (artist_minutes / 60).rename("Hours")

    artist_order = artist_hours.index.tolist()

    top_artists_df = df.merge(
        artist_hours.reset_index(),
        on="artistName",
        how="left",
    ).assign(rank=lambda d: d["Hours"].rank(ascending=False))

    return {
        "hours": artist_hours,
        "order": artist_order,
        "df": top_artists_df,
    }


def compute_top_songs(df: pd.DataFrame, top_n: int = 50) -> dict:
    top_songs_df = (
        df.groupby(["artistName", "trackName"], as_index=False)
        .agg(Listens=("msPlayed", "count"))
        .sort_values("Listens", ascending=False)
    )

    top_songs_df["rank"] = top_songs_df["Listens"].rank(method="first", ascending=False)

    top_songs_order = top_songs_df.sort_values("rank").head(top_n)["trackName"].tolist()

    return {
        "df": top_songs_df,
        "order": top_songs_order,
        "top_n": top_n,
    }


def compute_yearly_track_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns yearly track leaderboard dataframe.
    Columns:
        - Track (index)
        - Listens
        - Total Minutes
    """
    leaderboard = (
        df.groupby(["trackName", "artistName"], as_index=False)
        .agg(
            Listens=("endTime", "count"),
            Total_Minutes=("minutesPlayed", "sum"),
        )
        .sort_values(
            ["Total_Minutes", "Listens"],
            ascending=False,
        )
        .drop(columns="artistName")
        .set_index("trackName")
    )

    return leaderboard
