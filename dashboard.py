import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_processing import (
    read_excel_fol,
    validate_columns,
    clean_data,
    get_data_period,
    get_unique_values,
)

from utils.calculations import (
    calculate_kpis,
    calculate_location_summary,
    calculate_daily_summary,
    calculate_fail_by_driver,
    calculate_pass_by_driver,
    calculate_pass_fail_by_driver,
    calculate_pass_fail_percentage_by_driver,
    calculate_pass_fail_by_depo,
    calculate_fail_detail,
)


st.set_page_config(
    page_title="Dashboard FOL",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Dashboard FOL")

st.caption(
    "Dashboard untuk menganalisis data FOL berdasarkan "
    "tanggal, driver, depo, serta status Pass dan Fail."
)


with st.sidebar:

    st.header("Pengaturan")

    uploaded_files = st.file_uploader(
        "Upload Data FOL",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        help="Upload satu atau beberapa file Excel FOL.",
    )


if not uploaded_files:

    st.info(
        "📂 Silakan upload file Excel FOL terlebih dahulu "
        "untuk menampilkan dashboard."
    )

    st.stop()


dataframes = []
error_files = []


for uploaded_file in uploaded_files:

    try:

        df_file = read_excel_fol(
            uploaded_file
        )

        valid, missing_columns = validate_columns(
            df_file
        )

        if not valid:

            error_files.append(
                f"{uploaded_file.name}: "
                f"kolom tidak tersedia - "
                f"{', '.join(missing_columns)}"
            )

            continue

        df_file = clean_data(
            df_file
        )

        dataframes.append(
            df_file
        )

    except Exception as e:

        error_files.append(
            f"{uploaded_file.name}: {str(e)}"
        )


if error_files:

    st.warning(
        "⚠️ Beberapa file tidak dapat diproses:"
    )

    for error in error_files:
        st.write(f"- {error}")


if not dataframes:

    st.error(
        "❌ Tidak ada file yang berhasil diproses."
    )

    st.stop()


df = pd.concat(
    dataframes,
    ignore_index=True
)


df["Location"] = (
    df["Location"]
    .astype("string")
    .str.strip()
    .str.title()
)

df["Location"] = df["Location"].replace(
    "",
    pd.NA
)

df["Location"] = df["Location"].fillna(
    "Tidak Diketahui"
)


df["Nama Driver"] = (
    df["Nama Driver"]
    .astype("string")
    .str.strip()
)

df["Nama Driver"] = df["Nama Driver"].replace(
    "",
    pd.NA
)

df["Nama Driver"] = df["Nama Driver"].fillna(
    "Driver Tidak Terdata"
)


with st.sidebar:

    st.divider()

    st.header("Filter Data")

    st.subheader("Fokus Analisis Driver")

    driver_analysis = st.radio(
        "Pilih status",
        options=[
            "Pass",
            "Fail",
        ],
        index=1,
        horizontal=True,
        label_visibility="collapsed",
    )


    min_date, max_date = get_data_period(
        df
    )

    selected_date_range = None

    if min_date is not None and max_date is not None:

        selected_date_range = st.date_input(
            "Rentang Tanggal DO",
            value=(
                min_date.date(),
                max_date.date(),
            ),
            format="DD-MM-YYYY",
        )

    show_unknown_date = st.checkbox(
        "Tampilkan Tanggal DO Tidak Diketahui",
        value=True,
    )

    show_unregistered_driver = st.checkbox(
        "Tampilkan Driver Tidak Terdata",
        value=True,
    )

    depo_options = get_unique_values(
        df,
        "Depo",
    )

    depo_selection = st.multiselect(
        "Nama Depo",
        options=[
            "Select All"
        ] + depo_options,
        default=[],
    )

    if "Select All" in depo_selection:

        selected_depo = depo_options

    else:

        selected_depo = depo_selection


    driver_options = get_unique_values(
        df,
        "Nama Driver",
    )

    driver_selection = st.multiselect(
        "Nama Driver",
        options=[
            "Select All"
        ] + driver_options,
        default=[],
    )

    if "Select All" in driver_selection:

        selected_driver = driver_options

    else:

        selected_driver = driver_selection

filtered_df = df.copy()


if selected_date_range:

    if (
        isinstance(
            selected_date_range,
            tuple,
        )
        and len(selected_date_range) == 2
    ):

        start_date = pd.Timestamp(
            selected_date_range[0]
        )

        end_date = (
            pd.Timestamp(
                selected_date_range[1]
            )
            + pd.Timedelta(days=1)
        )

        known_date_mask = (
            filtered_df["Tanggal DO"].notna()
            & (
                filtered_df["Tanggal DO"]
                >= start_date
            )
            & (
                filtered_df["Tanggal DO"]
                < end_date
            )
        )

        unknown_date_mask = (
            filtered_df["Tanggal DO"].isna()
        )

        if show_unknown_date:

            filtered_df = filtered_df[
                known_date_mask
                | unknown_date_mask
            ]

        else:

            filtered_df = filtered_df[
                known_date_mask
            ]


if selected_depo:

    filtered_df = filtered_df[
        filtered_df["Depo"].isin(
            selected_depo
        )
    ]


if selected_driver:

    filtered_df = filtered_df[
        filtered_df["Nama Driver"].isin(
            selected_driver
        )
    ]


driver_analysis_df = filtered_df.copy()


if not show_unregistered_driver:

    driver_analysis_df = driver_analysis_df[
        driver_analysis_df["Nama Driver"]
        != "Driver Tidak Terdata"
    ]


total_filtered = (
    f"{len(filtered_df):,}"
    .replace(",", ".")
)

total_data = (
    f"{len(df):,}"
    .replace(",", ".")
)


st.caption(
    f"Menampilkan {total_filtered} "
    f"dari {total_data} data FOL"
)


kpis = calculate_kpis(
    filtered_df
)


col1, col2, col3, col4, col5 = st.columns(5)


col1.metric(
    "Total FOL",
    f"{kpis['total_fol']:,}".replace(",", "."),
)


col2.metric(
    "Total Pass",
    f"{kpis['total_pass']:,}".replace(",", "."),
)


col3.metric(
    "Total Fail",
    f"{kpis['total_fail']:,}".replace(",", "."),
)


col4.metric(
    "Persentase Pass",
    f"{kpis['persentase_pass']:.1f}%",
)


col5.metric(
    "Persentase Fail",
    f"{kpis['persentase_fail']:.1f}%",
)


st.divider()


st.subheader(
    "Distribusi Pass vs Fail"
)


location_summary = calculate_location_summary(
    filtered_df
)


if location_summary.empty:

    st.info(
        "Tidak terdapat data untuk ditampilkan."
    )

else:

    fig_location = px.pie(
        location_summary,
        names="Location",
        values="Jumlah",
        hole=0.55,
    )

    fig_location.update_traces(
        texttemplate="%{label}<br>%{percent:.1%}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Jumlah FOL: %{value:,.0f}<br>"
            "Persentase: %{percent:.1%}"
            "<extra></extra>"
        ),
    )

    fig_location.update_layout(
        legend_title_text="Status",
    )

    st.plotly_chart(
        fig_location,
        use_container_width=True,
    )


st.divider()


st.subheader(
    "Tren FOL Berdasarkan Tanggal DO"
)


daily_summary = calculate_daily_summary(
    filtered_df
)


if daily_summary.empty:

    st.info(
        "Tidak terdapat data dengan Tanggal DO "
        "yang dapat ditampilkan."
    )

else:

    fig_daily = px.line(
        daily_summary,
        x="Tanggal DO",
        y="Jumlah",
        color="Location",
        markers=False,
        labels={
            "Tanggal DO": "Tanggal DO",
            "Jumlah": "Jumlah FOL",
            "Location": "Status",
        },
    )

    fig_daily.update_traces(
        hovertemplate=(
            "<b>%{x|%d-%b-%Y}</b><br>"
            "Jumlah FOL: %{y:,.0f}"
            "<extra>%{fullData.name}</extra>"
        ),
    )

    fig_daily.update_layout(
        xaxis=dict(
            type="date",
            tickformat="%d-%b-%Y",
            tickangle=-45,
            nticks=15,
        ),
        yaxis=dict(
            tickformat=",.0f",
            rangemode="tozero",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_daily,
        use_container_width=True,
    )


st.divider()


if driver_analysis == "Pass":

    driver_title = (
        "Pass Tertinggi Berdasarkan Driver"
    )

    driver_data = calculate_pass_by_driver(
        driver_analysis_df
    )

    value_column = "Jumlah Pass"
    x_axis_title = "Jumlah Pass"

else:

    driver_title = (
        "Fail Tertinggi Berdasarkan Driver"
    )

    driver_data = calculate_fail_by_driver(
        driver_analysis_df
    )

    value_column = "Jumlah Fail"
    x_axis_title = "Jumlah Fail"


st.subheader(
    driver_title
)


if driver_data.empty:

    st.info(
        f"Tidak terdapat data {driver_analysis} "
        "untuk ditampilkan."
    )

else:

    max_driver = len(
        driver_data
    )

    if max_driver >= 2:

        default_driver = min(
            10,
            max_driver
        )

        selected_driver_count = st.slider(
            "Jumlah Driver",
            min_value=2,
            max_value=max_driver,
            value=default_driver,
            key="driver_ranking_count",
        )

        driver_data = (
            driver_data
            .sort_values(
                value_column,
                ascending=False,
            )
            .head(
                selected_driver_count
            )
        )

    driver_data = driver_data.sort_values(
        value_column,
        ascending=True,
    )

    fig_driver_ranking = px.bar(
        driver_data,
        x=value_column,
        y="Nama Driver",
        orientation="h",
        text=value_column,
        labels={
            value_column: x_axis_title,
            "Nama Driver": "Nama Driver",
        },
    )

    fig_driver_ranking.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"{x_axis_title}: "
            "%{x:,.0f}"
            "<extra></extra>"
        ),
    )

    fig_driver_ranking.update_layout(
        xaxis=dict(
            tickformat=",.0f",
            rangemode="tozero",
        ),
    )

    st.plotly_chart(
        fig_driver_ranking,
        use_container_width=True,
    )


st.divider()


st.subheader(
    "Perbandingan Jumlah Pass dan Fail Berdasarkan Driver"
)


pass_fail_driver = calculate_pass_fail_by_driver(
    driver_analysis_df
)


if pass_fail_driver.empty:

    st.info(
        "Tidak terdapat data driver untuk ditampilkan."
    )

else:

    driver_total = (
        pass_fail_driver
        .groupby("Nama Driver")["Jumlah"]
        .sum()
        .reset_index()
        .sort_values(
            "Jumlah",
            ascending=False,
        )
    )

    max_driver_total = len(
        driver_total
    )

    if max_driver_total >= 2:

        default_driver_total = min(
            10,
            max_driver_total
        )

        selected_driver_total = st.slider(
            "Jumlah Driver",
            min_value=2,
            max_value=max_driver_total,
            value=default_driver_total,
            key="pass_fail_driver_count",
        )

        selected_drivers = (
            driver_total
            .head(selected_driver_total)
            ["Nama Driver"]
            .tolist()
        )

        pass_fail_driver = pass_fail_driver[
            pass_fail_driver["Nama Driver"].isin(
                selected_drivers
            )
        ]

    driver_order = (
        driver_total[
            driver_total["Nama Driver"].isin(
                pass_fail_driver["Nama Driver"]
            )
        ]
        .sort_values(
            "Jumlah",
            ascending=True,
        )
        ["Nama Driver"]
        .tolist()
    )

    fig_pass_fail_driver = px.bar(
        pass_fail_driver,
        x="Nama Driver",
        y="Jumlah",
        color="Location",
        barmode="group",
        text="Jumlah",
        category_orders={
            "Nama Driver": driver_order
        },
        labels={
            "Nama Driver": "Nama Driver",
            "Jumlah": "Jumlah FOL",
            "Location": "Status",
        },
    )

    fig_pass_fail_driver.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Jumlah FOL: %{y:,.0f}"
            "<extra>%{fullData.name}</extra>"
        ),
    )

    fig_pass_fail_driver.update_layout(
        yaxis=dict(
            tickformat=",.0f",
            rangemode="tozero",
        ),
    )

    st.plotly_chart(
        fig_pass_fail_driver,
        use_container_width=True,
    )

st.divider()

st.subheader(
    "Persentase Pass vs Fail Berdasarkan Driver"
)


percentage_driver = (
    calculate_pass_fail_percentage_by_driver(
        driver_analysis_df
    )
)


if percentage_driver.empty:

    st.info(
        "Tidak terdapat data driver untuk ditampilkan."
    )

else:

    if driver_analysis == "Pass":

        percentage_ranking = (
            percentage_driver
            .sort_values(
                "Persentase Pass",
                ascending=False,
            )
        )

    else:

        percentage_ranking = (
            percentage_driver
            .sort_values(
                "Persentase Fail",
                ascending=False,
            )
        )

    max_percentage_driver = len(
        percentage_ranking
    )

    if max_percentage_driver >= 2:

        default_percentage_driver = min(
            10,
            max_percentage_driver
        )

        selected_percentage_driver = st.slider(
            "Jumlah Driver",
            min_value=2,
            max_value=max_percentage_driver,
            value=default_percentage_driver,
            key="percentage_driver_count",
        )

        selected_drivers = (
            percentage_ranking
            .head(selected_percentage_driver)
            ["Nama Driver"]
            .tolist()
        )

        percentage_driver = percentage_driver[
            percentage_driver["Nama Driver"].isin(
                selected_drivers
            )
        ]

    if driver_analysis == "Pass":

        driver_order = (
            percentage_driver
            .sort_values(
                "Persentase Pass",
                ascending=True,
            )
            ["Nama Driver"]
            .tolist()
        )

    else:

        driver_order = (
            percentage_driver
            .sort_values(
                "Persentase Fail",
                ascending=True,
            )
            ["Nama Driver"]
            .tolist()
        )

    fig_percentage_driver = px.bar(
        percentage_driver,
        x="Nama Driver",
        y=[
            "Persentase Pass",
            "Persentase Fail",
        ],
        barmode="stack",
        text_auto=".1f",
        category_orders={
            "Nama Driver": driver_order
        },
        labels={
            "Nama Driver": "Nama Driver",
            "value": "Persentase (%)",
            "variable": "Status",
        },
    )

    fig_percentage_driver.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Persentase: %{y:.1f}%"
            "<extra>%{fullData.name}</extra>"
        ),
    )

    fig_percentage_driver.update_layout(
        yaxis=dict(
            range=[0, 100],
            ticksuffix="%",
            dtick=20,
        ),
        xaxis=dict(
            tickangle=-45,
        ),
    )

    st.plotly_chart(
        fig_percentage_driver,
        use_container_width=True,
    )

st.divider()

st.subheader(
    "Pass vs Fail Berdasarkan Depo"
)


pass_fail_depo = calculate_pass_fail_by_depo(
    filtered_df
)


if pass_fail_depo.empty:

    st.info(
        "Tidak terdapat data depo untuk ditampilkan."
    )

else:

    if driver_analysis == "Pass":

        depo_ranking = (
            pass_fail_depo[
                pass_fail_depo["Location"] == "Pass"
            ]
            .sort_values(
                "Jumlah",
                ascending=False,
            )
        )

    else:

        depo_ranking = (
            pass_fail_depo[
                pass_fail_depo["Location"] == "Fail"
            ]
            .sort_values(
                "Jumlah",
                ascending=False,
            )
        )

    depo_order = (
        depo_ranking
        .sort_values(
            "Jumlah",
            ascending=True,
        )
        ["Depo"]
        .tolist()
    )

    fig_depo = px.bar(
        pass_fail_depo,
        x="Depo",
        y="Jumlah",
        color="Location",
        barmode="group",
        text="Jumlah",
        category_orders={
            "Depo": depo_order
        },
        labels={
            "Depo": "Nama Depo",
            "Jumlah": "Jumlah FOL",
            "Location": "Status",
        },
    )

    fig_depo.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Jumlah FOL: %{y:,.0f}"
            "<extra>%{fullData.name}</extra>"
        ),
    )

    fig_depo.update_layout(
        yaxis=dict(
            tickformat=",.0f",
            rangemode="tozero",
        ),
    )

    st.plotly_chart(
        fig_depo,
        use_container_width=True,
    )


st.divider()


st.subheader(
    "Detail Data Fail"
)


fail_detail = calculate_fail_detail(
    filtered_df
)


if fail_detail.empty:

    st.info(
        "Tidak terdapat data Fail."
    )

else:

    detail_columns = [
        "Depo",
        "Tanggal DO Tampilan",
        "Nama Driver",
        "Location",
    ]

    available_columns = [
        column
        for column in detail_columns
        if column in fail_detail.columns
    ]

    detail_display = fail_detail[
        available_columns
    ].copy()

    detail_display = detail_display.rename(
        columns={
            "Tanggal DO Tampilan": "Tanggal DO",
        }
    )

    st.dataframe(
        detail_display,
        use_container_width=True,
        hide_index=True,
    )