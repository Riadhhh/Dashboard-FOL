import pandas as pd
from utils.calculations import calculate_kpis

STATUSES = ("Fail", "Pass")
FREQUENCIES = ("Harian", "Mingguan")
TOP_N = 6

def _clean_group(source, column):
    """Membersihkan label pengelompokan tanpa mengubah data asli."""

    source[column] = (
        source[column]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .fillna(f"{column} Tidak Terdata")
    )

def _rank_by_status(df, group_columns, status="Fail"):
    """Menghitung volume, rate, dan kontribusi tiap kelompok."""

    if status not in STATUSES:
        raise ValueError("Status harus 'Fail' atau 'Pass'.")

    groups = (
        [group_columns]
        if isinstance(group_columns, str)
        else list(group_columns)
    )

    count_col = f"Total {status}"
    rate_col = f"{status} Rate (%)"
    share_col = f"Kontribusi {status} (%)"

    columns = groups + [
        "Total FOL",
        count_col,
        rate_col,
        share_col,
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    source = df[groups + ["Location"]].copy()

    for group in groups:
        _clean_group(source, group)

    source["_selected"] = (
        source["Location"]
        .eq(status)
        .fillna(False)
        .astype(int)
    )

    summary = (
        source.groupby(groups, dropna=False)
        .agg(
            **{
                "Total FOL": ("_selected", "size"),
                count_col: ("_selected", "sum"),
            }
        )
        .reset_index()
    )

    summary[rate_col] = (
        100
        * summary[count_col]
        / summary["Total FOL"]
    )

    all_selected = int(summary[count_col].sum())

    summary[share_col] = (
        100 * summary[count_col] / all_selected
        if all_selected
        else 0.0
    )

    return (
        summary.sort_values(
            [count_col, rate_col, "Total FOL", *groups],
            ascending=[
                False,
                False,
                False,
                *([True] * len(groups)),
            ],
            kind="stable",
        )
        .reset_index(drop=True)[columns]
    )


def _status_trend(df, granularity="Harian", status="Fail"):
    if granularity not in FREQUENCIES:
        raise ValueError(
            "Resolusi tren hanya 'Harian' atau 'Mingguan'."
        )

    if status not in STATUSES:
        raise ValueError("Status harus 'Fail' atau 'Pass'.")

    count_col = f"Total {status}"
    rate_col = f"{status} Rate (%)"

    columns = [
        "Periode",
        "Total FOL",
        count_col,
        rate_col,
    ]

    if df.empty:
        return pd.DataFrame(columns=columns), granularity

    dates = pd.to_datetime(
        df["Tanggal Order Priority"],
        errors="coerce",
    )

    valid = dates.notna()

    if not valid.any():
        return pd.DataFrame(columns=columns), granularity

    period = dates.loc[valid].dt.normalize()

    if granularity == "Mingguan":
        period = (
            period.dt.to_period("W-SUN")
            .dt.start_time
        )

    source = pd.DataFrame(
        {
            "Periode": period,
            "_selected": (
                df.loc[valid, "Location"]
                .eq(status)
                .fillna(False)
                .astype(int)
            ),
        }
    )

    summary = (
        source.groupby("Periode")
        .agg(
            **{
                "Total FOL": ("_selected", "size"),
                count_col: ("_selected", "sum"),
            }
        )
        .reset_index()
        .sort_values("Periode")
    )

    summary[rate_col] = (
        100
        * summary[count_col]
        / summary["Total FOL"]
    )

    return summary[columns], granularity


def build_priority_summary(
    filtered_df,
    granularity="Harian",
    focus_depo=None,
    status="Fail",
):
    if status not in STATUSES:
        raise ValueError("Status harus 'Fail' atau 'Pass'.")

    kpis = calculate_kpis(filtered_df)

    by_depo = _rank_by_status(
        filtered_df,
        "Depo",
        status,
    )

    by_driver = _rank_by_status(
        filtered_df,
        ["Nama Driver", "Depo"],
        status,
    )

    driver_source = filtered_df

    if focus_depo is not None:
        normalized_depo = (
            filtered_df["Depo"]
            .astype("string")
            .str.strip()
        )

        driver_source = filtered_df.loc[
            normalized_depo.eq(focus_depo).fillna(False)
        ]

    focus_drivers = _rank_by_status(
        driver_source,
        ["Nama Driver", "Depo"],
        status,
    )

    # Tren berdasarkan status yang dipilih
    trend, frequency = _status_trend(
        filtered_df,
        granularity,
        status,
    )

    count_col = f"Total {status}"

    valid_depos = by_depo.loc[
        by_depo["Depo"] != "Depo Tidak Terdata"
    ]

    top3_count = int(
        valid_depos.head(3)[count_col].sum()
    )

    total_count = int(
        kpis[f"total_{status.lower()}"]
    )

    share_top3 = (
        100 * top3_count / total_count
        if total_count
        else 0.0
    )

    top_depos = (
        valid_depos.loc[valid_depos[count_col] > 0]
        .head(TOP_N)
    )

    top_drivers = (
        by_driver.loc[by_driver[count_col] > 0]
        .head(TOP_N)
    )

    unnamed_depo_count = int(
        by_depo.loc[
            by_depo["Depo"] == "Depo Tidak Terdata",
            count_col,
        ].sum()
    )

    return {
        "status": status,
        "kpis": kpis,
        "by_depo": by_depo,
        "by_driver": by_driver,
        "focus_drivers": focus_drivers,
        "trend": trend,
        "frequency": frequency,
        "focus_depo": focus_depo,
        "share_top3_depos": share_top3,
        "top3_count": top3_count,
        "top3_fail": (
            top3_count if status == "Fail" else 0
        ),
        "top_depos": top_depos,
        "top_drivers": top_drivers,
        "affected_depos": int(
            (valid_depos[count_col] > 0).sum()
        ),
        "other_statuses": int(
            kpis["total_fol"]
            - kpis["total_pass"]
            - kpis["total_fail"]
        ),
        "unnamed_depo_status": unnamed_depo_count,
        "unnamed_depo_fails": (
            unnamed_depo_count
            if status == "Fail"
            else 0
        ),
    }
