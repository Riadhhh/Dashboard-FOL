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
        subset=["Tanggal DO"]
    ).copy()

    summary = (
        daily_data
        .groupby(
            ["Tanggal DO", "Location"]
        )
        .size()
        .reset_index(name="Jumlah")
        .sort_values("Tanggal DO")
    )

    return summary


def calculate_fail_by_driver(df):
    fail_data = df[
        df["Location"] == "Fail"
    ].copy()

    summary = (
        fail_data["Nama Driver"]
        .value_counts()
        .rename_axis("Nama Driver")
        .reset_index(name="Jumlah Fail")
    )

    return summary


def calculate_pass_by_driver(df):
    pass_data = df[
        df["Location"] == "Pass"
    ].copy()

    summary = (
        pass_data["Nama Driver"]
        .value_counts()
        .rename_axis("Nama Driver")
        .reset_index(name="Jumlah Pass")
    )

    return summary


def calculate_pass_fail_by_driver(df):
    summary = (
        df[
            df["Location"].isin(
                ["Pass", "Fail"]
            )
        ]
        .groupby(
            ["Nama Driver", "Location"]
        )
        .size()
        .reset_index(name="Jumlah")
    )

    return summary


def calculate_pass_fail_percentage_by_driver(df):
    data = df[
        df["Location"].isin(
            ["Pass", "Fail"]
        )
    ].copy()

    summary = (
        data.groupby("Nama Driver")
        .agg(
            Total_FOL=("Location", "size"),
            Total_Pass=(
                "Location",
                lambda x: (x == "Pass").sum()
            ),
            Total_Fail=(
                "Location",
                lambda x: (x == "Fail").sum()
            ),
        )
        .reset_index()
    )

    summary["Persentase Pass"] = (
        summary["Total_Pass"]
        / summary["Total_FOL"]
        * 100
    )

    summary["Persentase Fail"] = (
        summary["Total_Fail"]
        / summary["Total_FOL"]
        * 100
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
            ["Depo", "Location"]
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
        "Tanggal DO",
        ascending=False,
        na_position="last"
    )