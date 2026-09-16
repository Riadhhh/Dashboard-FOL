import pandas as pd


def calculate_kpis(df):
    total_fol = len(df)

    total_pass = (df["Location"] == "Pass").sum()

    total_fail = (df["Location"] == "Fail").sum()

    persentase_pass = (
        (total_pass / total_fol) * 100
        if total_fol > 0
        else 0
    )

    persentase_fail = (
        (total_fail / total_fol) * 100
        if total_fol > 0
        else 0
    )

    return {
        "total_fol": total_fol,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "persentase_pass": persentase_pass,
        "persentase_fail": persentase_fail,
    }


def calculate_location_summary(df):
    summary = (
        df["Location"]
        .value_counts()
        .rename_axis("Location")
        .reset_index(name="Jumlah")
    )

    return summary


def calculate_daily_summary(df):
    daily_data = df.dropna(
        subset=["Tanggal Order Priority"]
    ).copy()

    summary = (
        daily_data
        .groupby(
            [
                "Tanggal Order Priority",
                "Location",
            ]
        )
        .size()
        .reset_index(name="Jumlah")
    )

    total_daily = (
        daily_data
        .groupby("Tanggal Order Priority")
        .size()
        .reset_index(name="Total FOL")
    )

    summary = summary.merge(
        total_daily,
        on="Tanggal Order Priority",
        how="left"
    )

    summary["Persentase"] = (
        summary["Jumlah"]
        / summary["Total FOL"]
        * 100
    )

    return summary.sort_values(
        "Tanggal Order Priority"
    )


def calculate_pass_fail_by_driver(df):
    summary = (
        df[
            df["Location"].isin(
                ["Pass", "Fail"]
            )
        ]
        .groupby(
            [
                "Nama Driver",
                "Depo",
                "Location",
            ]
        )
        .size()
        .reset_index(name="Jumlah")
    )

    return summary


def calculate_pass_by_driver(df):
    pass_data = df[
        df["Location"] == "Pass"
    ].copy()

    summary = (
        pass_data
        .groupby(
            [
                "Nama Driver",
                "Depo",
            ]
        )
        .size()
        .reset_index(name="Jumlah Pass")
        .sort_values(
            "Jumlah Pass",
            ascending=False
        )
    )

    return summary


def calculate_fail_by_driver(df):
    fail_data = df[
        df["Location"] == "Fail"
    ].copy()

    summary = (
        fail_data
        .groupby(
            [
                "Nama Driver",
                "Depo",
            ]
        )
        .size()
        .reset_index(name="Jumlah Fail")
        .sort_values(
            "Jumlah Fail",
            ascending=False
        )
    )

    return summary

def calculate_pass_fail_by_depo(df):
    summary = (
        df[
            df["Location"].isin(
                ["Pass", "Fail"]
            )
        ]
        .groupby(
            [
                "Depo",
                "Location",
            ]
        )
        .size()
        .reset_index(name="Jumlah")
    )

    return summary


def calculate_fail_detail(df):
    fail_data = df[
        df["Location"] == "Fail"
    ].copy()

    return fail_data.sort_values(
        "Tanggal Order Priority",
        ascending=False,
        na_position="last"
    )