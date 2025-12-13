import altair as alt
import pandas as pd
import datetime as dt
import calendar

from data_processing import get_month_weeks, build_date_from_pieces # Import helper functions

def create_top_artists_chart(df: pd.DataFrame, top_artists_order: list, corner_radius: int) -> alt.Chart:
    chart = (
        alt.Chart(df.head(40).reset_index().assign(rank=lambda x: x.index + 1))
        .mark_bar(width=40, cornerRadius=corner_radius)
        .encode(
            y=alt.Y(
                "artistName",
                sort=top_artists_order[0:40],
                title="Artist",
                axis=alt.Axis(
                    labels=False,
                ),
            ),
            x=alt.X(
                "hours:Q",
                title="Total Hours",
                axis=alt.Axis(
                    format="d",
                ),
                scale=alt.Scale(domain=(0, df["hours"].max() * 1.2)),
            ),
            color=alt.Color(
                "artistName:N",
                title="Artist",
                sort=top_artists_order[0:40],
                scale=alt.Scale(scheme="viridis"),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("rank", title="Order"),
                alt.Tooltip("artistName:N", title="Artist"),
                alt.Tooltip("hours:Q", format=",.0f", title="Hours"),
            ],
        )
        .properties(height=500)
    )
    text = chart.mark_text(align="left", baseline="middle", dx=3, fontSize=12).encode(text=alt.Text("artistName:N", title="Artist"))
    return chart + text


def create_top_songs_chart(df: pd.DataFrame, top_songs_order: list, top_artists_order: list, corner_radius: int, top_n: int = 50) -> alt.Chart:
    chart = (
        alt.Chart(df.head(top_n))
        .mark_bar(cornerRadius=corner_radius)
        .encode(
            x=alt.X(
                "Listens",
                title="# Plays",
                axis=alt.Axis(labelAngle=0),
                scale=alt.Scale(domain=(0, df["Listens"].max() * 1.2)),
            ),
            y=alt.Y(
                "trackName",
                title="Track",
                axis=alt.Axis(labels=False),
                sort=top_songs_order,
            ),
            color=alt.Color(
                "artistName:N",
                title="Artist",
                scale=alt.Scale(scheme="viridis"),
                sort=top_artists_order,
                legend=None,
            ),
            order=alt.Order("rank", sort="ascending"),
            tooltip=[
                alt.Tooltip("rank", title="Order"),
                alt.Tooltip("trackName:N", title="Track"),
                alt.Tooltip("artistName:N", title="Artist"),
                alt.Tooltip("Listens:Q", title="# Plays"),
            ],
        )
        .properties(height=600)
    )
    text = chart.mark_text(align="left", baseline="middle", dx=3, fontSize=12).encode(
        x=alt.X("Listens", title="# Plays"),
        y=alt.Y("trackName", title="Track", stack="zero", sort=top_songs_order),
        text=alt.Text("trackName", title="Track"),
        order=alt.Order("rank", sort="ascending"),
    )
    return chart + text

def create_minutes_played_by_month_chart(df: pd.DataFrame, artist_name: str) -> alt.Chart:
    all_artist = df.copy()
    all_artist["year_month"] = pd.to_datetime(all_artist["date"]).dt.strftime("%Y-%m")
    all_artist = all_artist.groupby(["year_month"], as_index=False).sum(numeric_only=True)

    chart = (
        alt.Chart(all_artist)
        .mark_bar()
        .encode(
            x=alt.X("year_month:T", title="Date", axis=alt.Axis(labelAngle=0), timeUnit="yearmonth"),
            y=alt.Y("minutesPlayed:Q", title="Minutes Played", axis=alt.Axis(format=".0f")),
            tooltip=[
                alt.Tooltip("year_month:T", title="Date", format="%b-%Y", timeUnit="yearmonth"),
                alt.Tooltip("minutesPlayed:Q", title="Minutes Played", format=".0f"),
            ],
        )
        .properties(
            width=800,
            height=400,
            title=f"Minutes Played by Month for {artist_name}",
        )
    )
    return chart

def build_heatmap(heatmap_data: pd.DataFrame, days_of_week: list, corner_radius: int, heatmap_artist: str, year_select: int) -> alt.Chart:
    simple_heatmap_data = heatmap_data[
        [
            "artistName",
            "trackName",
            "endTime",
            "minutesPlayed",
            "date",
            "year",
            "week",
            "dow",
            "day_of_week_str",
        ]
    ]
    simple_heatmap_data["week"] = pd.Categorical(
        values=pd.to_datetime(simple_heatmap_data["endTime"]).dt.isocalendar().week,
        categories=list(range(0, 53)),
    )
    simple_heatmap_data["day_of_week_str"] = pd.Categorical(
        values=simple_heatmap_data["day_of_week_str"],
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ordered=True,
    )
    heatmap_agg = (
        simple_heatmap_data.groupby(["week", "day_of_week_str", "year"])
        .sum(numeric_only=True)["minutesPlayed"]
        .reset_index()
    )

    bucket_labels = ["0 min", "1-5 min", "5-15 min", "15-60 min", "60+ min"]
    heatmap_agg["min_bucket"] = pd.cut(
        heatmap_agg["minutesPlayed"], bins=[-1, 1, 5, 15, 60, 60 * 60 * 24], labels=bucket_labels
    )

    month_weeks = get_month_weeks(year_select)

    format_label_expr = "||".join(
        [
            f"datum.value === {month_week} ?  '{month}': ''"
            for month, month_week in zip(calendar.month_abbr[1:], month_weeks)
        ]
    )

    heatmap_agg = (
        heatmap_agg.merge(
            simple_heatmap_data[["date", "week", "year", "day_of_week_str"]].drop_duplicates(),
            left_on=["week", "day_of_week_str", "year"],
            right_on=["week", "day_of_week_str", "year"],
            how="left",
        )
        .drop_duplicates()
        .sort_values(["date", "day_of_week_str"])
    )

    missing_dates = heatmap_agg[heatmap_agg["date"].isnull()]
    not_missing_dates = heatmap_agg[heatmap_agg["date"].notnull()]

    missing_dates["date"] = missing_dates.apply(build_date_from_pieces, axis=1)

    heatmap_agg = pd.concat([missing_dates, not_missing_dates])

    artist_heat = (
        alt.Chart(heatmap_agg)
        .mark_rect(cornerRadius=corner_radius)
        .encode(
            x=alt.X(
                "week:O",
                title="Week",
                axis=alt.Axis(
                    labelExpr=format_label_expr,
                    labelAngle=0,
                ),
            ),
            y=alt.Y(
                "day_of_week_str:O",
                title="Day",
                sort=days_of_week,
                axis=alt.Axis(title=None),
            ),
            color=alt.Color(
                "min_bucket:O",
                title="Minutes Played",
                scale=alt.Scale(
                    range=["#e0e0e0", "#90caf9", "#64b5f6", "#42a5f5", "#1e88e5"],
                    domain=bucket_labels,
                ),
                legend=alt.Legend(
                    orient="bottom",
                ),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("minutesPlayed:Q", title="Minutes Played", format=".0f"),
            ],
        )
        .configure_scale(bandPaddingInner=0.3)
        .properties(
            title=f"Minutes Played by Day for {heatmap_artist} in {year_select}",
        )
    )
    return artist_heat
