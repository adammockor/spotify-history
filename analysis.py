import pandas as pd


def aggregate_artist_minutes(df: pd.DataFrame) -> pd.Series:
    """
    Returns minutes played per artist, sorted descending.
    Index: artistName
    """
    return (
        df.groupby("artistName")["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
    )


def get_artist_order(df: pd.DataFrame) -> list[str]:
    return aggregate_artist_minutes(df).index.tolist()


def get_artist_data(df: pd.DataFrame, artist: str) -> pd.DataFrame:
    if artist == "All Artists":
        return df
    return df[df["artistName"] == artist]


def get_artist_rank(df: pd.DataFrame, artist: str) -> int | None:
    if artist == "All Artists":
        return None

    minutes = aggregate_artist_minutes(df)

    if artist not in minutes.index:
        return None

    return minutes.index.get_loc(artist) + 1


def get_yearly_artist_rank(
    df: pd.DataFrame,
    artist: str,
    year: int,
) -> int | None:
    if artist == "All Artists":
        return None

    yearly_df = df[df["year"] == year]
    return get_artist_rank(yearly_df, artist)


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

    artist_hours = (artist_minutes / 60).rename("hours")

    artist_order = artist_hours.index.tolist()

    top_artists_df = df.merge(
        artist_hours.reset_index(),
        on="artistName",
        how="left",
    ).assign(rank=lambda d: d["hours"].rank(ascending=False))

    return {
        "hours": artist_hours,
        "order": artist_order,
        "df": top_artists_df,
    }


def compute_artist_stats(df: pd.DataFrame) -> dict:
    """
    Generic artist stats for the given dataframe slice.
    """
    return {
        "hours": df["minutesPlayed"].sum() / 60,
        "unique_tracks": df["trackName"].nunique(),
        "most_listened_year": (
            df.groupby("year")["minutesPlayed"].sum(numeric_only=True).idxmax()
            if "year" in df.columns and not df.empty
            else None
        ),
    }


def compute_yearly_artist_stats(
    df: pd.DataFrame,
    artist: str,
    year: int,
) -> dict:
    if artist == "All Artists":
        subset = df[df["year"] == year]
    else:
        subset = df[(df["year"] == year) & (df["artistName"] == artist)]

    return compute_artist_stats(subset)


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


def aggregate_album_minutes(df: pd.DataFrame) -> pd.Series:
    """
    Returns minutes played per album (by artist), sorted descending.
    Index: MultiIndex (artistName, albumName)
    """
    return (
        df.groupby(["artistName", "albumName"])["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
    )


def get_album_order(df: pd.DataFrame) -> list[str]:
    """
    Returns display labels in descending listening order.
    """
    minutes = aggregate_album_minutes(df)
    idx = minutes.index  # MultiIndex (artistName, albumName)
    return [f"{album} — {artist}" for artist, album in idx]


def get_album_rank(df: pd.DataFrame, artist: str, album: str) -> int | None:
    """
    Returns 1-based rank for a specific (artist, album).
    """
    minutes = aggregate_album_minutes(df)
    key = (artist, album)
    if key not in minutes.index:
        return None
    return minutes.index.get_loc(key) + 1


def get_yearly_album_rank(
    df: pd.DataFrame,
    artist: str,
    album: str,
    year: int,
) -> int | None:
    yearly_df = df[df["year"] == year]
    return get_album_rank(yearly_df, artist, album)


def compute_top_albums(df: pd.DataFrame) -> dict:
    """
    Returns one row per (artist, album), ordered by hours desc.
    Columns:
        - artistName
        - albumName
        - hours
        - rank
        - album_display
    """
    minutes = aggregate_album_minutes(df)
    hours = (minutes / 60).rename("hours")

    albums_df = hours.reset_index().assign(
        rank=lambda d: range(1, len(d) + 1),
        album_display=lambda d: d["albumName"] + " — " + d["artistName"],
    )

    return {
        "df": albums_df,
        "order": albums_df["album_display"].tolist(),
    }


def compute_lifetime_top_albums(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns lifetime top albums table for a given artist dataframe.
    Columns:
        - Album (index)
        - Total Minutes
    """
    tracks = (
        df.groupby(["albumName", "artistName"], as_index=False)
        .agg(
            Total_Minutes=("minutesPlayed", "sum"),
        )
        .sort_values("Total_Minutes", ascending=False)
        .drop(columns="artistName")
        .set_index("albumName")
    )

    return tracks


def compute_yearly_album_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns yearly track leaderboard dataframe.
    Columns:
        - Album (index)
        - Total Minutes
    """
    leaderboard = (
        df.groupby(["albumName", "artistName"], as_index=False)
        .agg(
            Total_Minutes=("minutesPlayed", "sum"),
        )
        .sort_values(
            ["Total_Minutes"],
            ascending=False,
        )
        .drop(columns="artistName")
        .set_index("albumName")
    )

    return leaderboard


def aggregate_track_minutes(df: pd.DataFrame) -> pd.Series:
    """
    Returns minutes played per track (by artist), sorted descending.
    Index: MultiIndex (artistName, trackName)
    """
    return (
        df.groupby(["artistName", "trackName"])["minutesPlayed"]
        .sum(numeric_only=True)
        .sort_values(ascending=False)
    )


def get_track_order(df: pd.DataFrame, top_n: int | None = None) -> list[str]:
    """
    Returns track names in descending listening order.
    If top_n is provided, limits the result.
    """
    minutes = aggregate_track_minutes(df)
    order = minutes.index.get_level_values("trackName").tolist()
    return order if top_n is None else order[:top_n]


def get_track_rank(
    df: pd.DataFrame,
    artist: str,
    track: str,
) -> int | None:
    """
    Returns 1-based rank of a track by total minutes.
    """
    minutes = aggregate_track_minutes(df)
    key = (artist, track)

    if key not in minutes.index:
        return None

    return minutes.index.get_loc(key) + 1


def compute_top_songs(df: pd.DataFrame, top_n: int = 50) -> dict:
    """
    Returns one row per (artist, track), ordered by listens.
    Rank is explicit and 1-based.
    """

    songs_df = (
        df.groupby(["artistName", "trackName"], as_index=False)
        .agg(Listens=("msPlayed", "count"))
        .sort_values("Listens", ascending=False)
        .reset_index(drop=True)
        .assign(rank=lambda d: range(1, len(d) + 1))
    )

    return {
        "df": songs_df,
        "order": songs_df.head(top_n)["trackName"].tolist(),
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
