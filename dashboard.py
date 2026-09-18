import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_processing import (
    read_excel_fol,
    validate_columns,
    clean_data,
    get_data_period,
    get_unique_values,
    VALID_DRIVERS,
)

from utils.calculations import (
    calculate_kpis,
    calculate_location_summary,
    calculate_daily_summary,
    calculate_fail_by_driver,
    calculate_pass_by_driver,
    calculate_pass_fail_by_driver,
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
        st.write(
            f"- {error}"
        )

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

df = df[
    df["Nama Driver"].isin(
        VALID_DRIVERS
    )
].copy()

if "week_selection" not in st.session_state:
    st.session_state.week_selection = []


def update_week_selection():
    st.session_state.week_selection = (
        st.session_state.week_filter
    )


with st.sidebar:

    st.divider()

    st.header("Filter Data")

    st.subheader(
        "Fokus Analisis Driver"
    )

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

    min_date, max_date = get_data_period(df)

    if st.session_state.week_selection:

        selected_date_range = st.date_input(
            "Rentang Tanggal Order Priority",
            value=(
                min_date.date(),
                max_date.date(),
            ),
            min_value=min_date.date(),
            max_value=max_date.date(),
            format="DD-MM-YYYY",
            disabled=True,
            key="date_range_week",
        )

    else:

        selected_date_range = st.date_input(
            "Rentang Tanggal Order Priority",
            value=(
                min_date.date(),
                max_date.date(),
            ),
            min_value=min_date.date(),
            max_value=max_date.date(),
            format="DD-MM-YYYY",
            key="date_range_manual",
        )

    week_options = sorted(
        df["Week"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_week = st.multiselect(
        "Week",
        options=week_options,
        default=st.session_state.week_selection,
        key="week_filter",
        on_change=update_week_selection,
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

    driver_options = sorted(
        [
            driver
            for driver in VALID_DRIVERS
            if driver in df[
                "Nama Driver"
            ].unique()
        ]
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

if selected_week:

    filtered_df = filtered_df[
        filtered_df["Week"].isin(
            selected_week
        )
    ].copy()

else:

    if selected_date_range is not None:

        if len(selected_date_range) == 2:

            start_date, end_date = (
                selected_date_range
            )

            filtered_df = filtered_df[
                filtered_df[
                    "Tanggal Order Priority"
                ].dt.date.between(
                    start_date,
                    end_date,
                )
            ].copy()

if selected_depo or selected_driver:

    depo_condition = (
        filtered_df["Depo"].isin(
            selected_depo
        )
        if selected_depo
        else False
    )

    driver_condition = (
        filtered_df["Nama Driver"].isin(
            selected_driver
        )
        if selected_driver
        else False
    )

    filtered_df = filtered_df[
        depo_condition | driver_condition
    ].copy()

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
    f"{kpis['total_fol']:,}".replace(
        ",",
        "."
    ),
)

col2.metric(
    "Total Pass",
    f"{kpis['total_pass']:,}".replace(
        ",",
        "."
    ),
)

col3.metric(
    "Total Fail",
    f"{kpis['total_fail']:,}".replace(
        ",",
        "."
    ),
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
        color="Location",
        color_discrete_map={
            "Pass": "#2E86DE",
            "Fail": "#E74C3C",
        },
    )

    fig_location.update_traces(
        texttemplate=(
            "%{label}<br>%{percent:.1%}"
        ),
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
    "Tren FOL Berdasarkan Tanggal Order Priority"
)

daily_summary = calculate_daily_summary(
    filtered_df
)

if daily_summary.empty:

    st.info(
        "Tidak terdapat data dengan Tanggal Order Priority "
        "yang dapat ditampilkan."
    )

else:

    daily_summary[
        "Tanggal Order Priority"
    ] = pd.to_datetime(
        daily_summary[
            "Tanggal Order Priority"
        ],
        errors="coerce"
    )

    daily_summary["Jumlah"] = pd.to_numeric(
        daily_summary["Jumlah"],
        errors="coerce"
    )

    daily_summary["Total FOL"] = pd.to_numeric(
        daily_summary["Total FOL"],
        errors="coerce"
    )

    daily_summary["Persentase"] = pd.to_numeric(
        daily_summary["Persentase"],
        errors="coerce"
    )

    fig_daily = px.line(
        daily_summary,
        x="Tanggal Order Priority",
        y="Jumlah",
        color="Location",
        markers=True,
        labels={
            "Tanggal Order Priority": (
                "Tanggal Order Priority"
            ),
            "Jumlah": "Jumlah FOL",
            "Location": "Status",
        },
        custom_data=[
            "Total FOL",
            "Persentase",
        ],
    )

    fig_daily.update_traces(
        hovertemplate=(
            "<b>%{x|%d-%b-%Y}</b><br>"
            "Status: %{fullData.name}<br>"
            "Jumlah: %{y:,.0f}<br>"
            "Total FOL: %{customdata[0]:,.0f}<br>"
            "Persentase: %{customdata[1]:.1f}%"
            "<extra></extra>"
        )
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
        config={
            "displayModeBar": True,
        },
    )

st.divider()

st.subheader(
    "Analisis FOL Berdasarkan Driver"
)

pass_data = calculate_pass_by_driver(
    filtered_df
)

fail_data = calculate_fail_by_driver(
    filtered_df
)

pass_data = pass_data.sort_values(
    "Jumlah Pass",
    ascending=False
)

fail_data = fail_data.sort_values(
    "Jumlah Fail",
    ascending=False
)

if pass_data.empty and fail_data.empty:

    st.info(
        "Tidak terdapat data driver "
        "untuk ditampilkan."
    )

else:

    max_driver = max(
        len(pass_data),
        len(fail_data),
    )

    if max_driver <= 1:

        top_n = 1

    else:

        top_n = st.slider(
            "Top N Driver",
            min_value=1,
            max_value=max_driver,
            value=min(
                10,
                max_driver
            ),
            key="top_n_analysis",
        )

    pass_chart_data = pass_data.head(
        top_n
    )

    fail_chart_data = fail_data.head(
        top_n
    )

    col_pass, col_fail = st.columns(2)

    with col_pass:

        st.markdown(
            "### Pass Tertinggi Berdasarkan Driver"
        )

        if pass_chart_data.empty:

            st.info(
                "Tidak terdapat data Pass."
            )

        else:

            fig_pass_driver = px.bar(
                pass_chart_data,
                x="Nama Driver",
                y="Jumlah Pass",
                text_auto=True,
                custom_data=["Depo"],
                color_discrete_sequence=[
                    "#2E86DE"
                ],
                labels={
                    "Nama Driver": "Nama Driver",
                    "Jumlah Pass": "Jumlah Pass",
                },
            )

            fig_pass_driver.update_traces(
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Depo: %{customdata[0]}<br>"
                    "Jumlah Pass: %{y:,.0f}"
                    "<extra></extra>"
                ),
            )

            fig_pass_driver.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_pass_driver,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                },
            )

    with col_fail:

        st.markdown(
            "### Fail Tertinggi Berdasarkan Driver"
        )

        if fail_chart_data.empty:

            st.info(
                "Tidak terdapat data Fail."
            )

        else:

            fig_fail_driver = px.bar(
                fail_chart_data,
                x="Nama Driver",
                y="Jumlah Fail",
                text_auto=True,
                custom_data=["Depo"],
                color_discrete_sequence=[
                    "#E74C3C"
                ],
                labels={
                    "Nama Driver": "Nama Driver",
                    "Jumlah Fail": "Jumlah Fail",
                },
            )

            fig_fail_driver.update_traces(
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Depo: %{customdata[0]}<br>"
                    "Jumlah Fail: %{y:,.0f}"
                    "<extra></extra>"
                ),
            )

            fig_fail_driver.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_fail_driver,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                },
            )

st.divider()

st.subheader(
    "Perbandingan Jumlah Pass dan Fail Berdasarkan Driver"
)

pass_fail_driver = calculate_pass_fail_by_driver(
    filtered_df
)

if pass_fail_driver.empty:

    st.info(
        "Tidak terdapat data driver untuk ditampilkan."
    )

else:

    driver_total = (
        pass_fail_driver
        .groupby(
            "Nama Driver"
        )["Jumlah"]
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

        selected_drivers_total = (
            driver_total
            .head(
                selected_driver_total
            )["Nama Driver"]
            .tolist()
        )

        pass_fail_driver = (
            pass_fail_driver[
                pass_fail_driver[
                    "Nama Driver"
                ].isin(
                    selected_drivers_total
                )
            ]
        )

    driver_order = (
        driver_total[
            driver_total[
                "Nama Driver"
            ].isin(
                pass_fail_driver[
                    "Nama Driver"
                ]
            )
        ]
        .sort_values(
            "Jumlah",
            ascending=True,
        )["Nama Driver"]
        .tolist()
    )

    fig_pass_fail_driver = px.bar(
        pass_fail_driver,
        x="Nama Driver",
        y="Jumlah",
        color="Location",
        barmode="group",
        text="Jumlah",
        custom_data=["Depo"],
        color_discrete_map={
            "Pass": "#2E86DE",
            "Fail": "#E74C3C",
        },
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
            "Depo: %{customdata[0]}<br>"
            "Jumlah FOL: %{y:,.0f}"
            "<extra>%{fullData.name}</extra> "
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
    "Pass vs Fail Berdasarkan Driver"
)

driver_summary = calculate_pass_fail_by_driver(
    filtered_df
)

if driver_summary.empty:

    st.info(
        "Tidak terdapat data driver "
        "untuk ditampilkan."
    )

else:

    ranking_column = (
        "Jumlah Pass"
        if driver_analysis == "Pass"
        else "Jumlah Fail"
    )

    ranking_data = (
        driver_summary
        .pivot(
            index="Nama Driver",
            columns="Location",
            values="Jumlah"
        )
        .fillna(0)
    )

    if "Pass" not in ranking_data.columns:
        ranking_data["Pass"] = 0

    if "Fail" not in ranking_data.columns:
        ranking_data["Fail"] = 0

    ranking_data["Jumlah Pass"] = (
        ranking_data["Pass"]
    )

    ranking_data["Jumlah Fail"] = (
        ranking_data["Fail"]
    )

    ranking_data = ranking_data.sort_values(
        ranking_column,
        ascending=False
    )

    display_mode_driver = st.selectbox(
        "Tampilkan Berdasarkan",
        [
            "Persentase",
            "Jumlah",
        ],
        index=0,
        key="driver_display_mode",
    )

    max_driver = len(
        ranking_data
    )

    if max_driver <= 1:

        top_n_driver = 1

    else:

        top_n_driver = st.slider(
            "Top N Driver",
            min_value=1,
            max_value=max_driver,
            value=min(
                10,
                max_driver
            ),
            key="top_n_driver_comparison",
        )

    selected_drivers = (
        ranking_data
        .head(
            top_n_driver
        )
        .index
        .tolist()
    )

    driver_chart = driver_summary[
        driver_summary[
            "Nama Driver"
        ].isin(
            selected_drivers
        )
    ].copy()

    driver_chart["Nama Driver"] = pd.Categorical(
        driver_chart[
            "Nama Driver"
        ],
        categories=selected_drivers,
        ordered=True
    )

    driver_chart = driver_chart.sort_values(
        "Nama Driver"
    )

    if display_mode_driver == "Jumlah":

        fig_driver_comparison = px.bar(
            driver_chart,
            x="Nama Driver",
            y="Jumlah",
            color="Location",
            barmode="stack",
            text_auto=".0f",
            color_discrete_map={
                "Pass": "#2E86DE",
                "Fail": "#E74C3C",
            },
            labels={
                "Nama Driver": "Nama Driver",
                "Jumlah": "Jumlah FOL",
                "Location": "Status",
            },
        )

        fig_driver_comparison.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Status: %{fullData.name}<br>"
                "Jumlah FOL: %{y:,.0f}"
                "<extra></extra>"
            )
        )

        fig_driver_comparison.update_layout(
            yaxis=dict(
                title="Jumlah FOL",
                tickformat=",.0f",
                rangemode="tozero",
            ),
            xaxis=dict(
                tickangle=-45,
            ),
        )

    else:

        total_driver = (
            driver_chart
            .groupby(
                "Nama Driver",
                observed=True
            )["Jumlah"]
            .transform("sum")
        )

        driver_chart["Persentase"] = (
            driver_chart["Jumlah"]
            / total_driver
            * 100
        )

        fig_driver_comparison = px.bar(
            driver_chart,
            x="Nama Driver",
            y="Persentase",
            color="Location",
            barmode="stack",
            text_auto=".1f",
            color_discrete_map={
                "Pass": "#2E86DE",
                "Fail": "#E74C3C",
            },
            labels={
                "Nama Driver": "Nama Driver",
                "Persentase": "Persentase (%)",
                "Location": "Status",
            },
        )

        fig_driver_comparison.update_traces(
            texttemplate="%{y:.1f}%",
            textposition="inside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Status: %{fullData.name}<br>"
                "Persentase: %{y:.1f}%"
                "<extra></extra>"
            ),
        )

        fig_driver_comparison.update_layout(
            yaxis=dict(
                title="Persentase (%)",
                range=[0, 100],
                ticksuffix="%",
                dtick=20,
            ),
            xaxis=dict(
                tickangle=-45,
            ),
        )

    st.plotly_chart(
        fig_driver_comparison,
        use_container_width=True,
        config={
            "displayModeBar": True,
        },
    )

st.divider()

st.subheader(
    "Pass vs Fail Berdasarkan Depo"
)

depo_summary = calculate_pass_fail_by_depo(
    filtered_df
)

if depo_summary.empty:

    st.info(
        "Tidak terdapat data depo "
        "untuk ditampilkan."
    )

else:

    display_mode = st.selectbox(
        "Tampilkan Berdasarkan",
        [
            "Jumlah",
            "Persentase",
        ],
        key="depo_display_mode",
    )

    depo_chart = depo_summary.copy()

    if display_mode == "Jumlah":

        fig_depo = px.bar(
            depo_chart,
            x="Depo",
            y="Jumlah",
            color="Location",
            barmode="group",
            text_auto=".0f",
            color_discrete_map={
                "Pass": "#2E86DE",
                "Fail": "#E74C3C",
            },
            labels={
                "Depo": "Nama Depo",
                "Jumlah": "Jumlah FOL",
                "Location": "Status",
            },
        )

        fig_depo.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Status: %{fullData.name}<br>"
                "Jumlah: %{y:,.0f}"
                "<extra></extra>"
            )
        )

        fig_depo.update_layout(
            yaxis=dict(
                title="Jumlah FOL",
                tickformat=",.0f",
                rangemode="tozero",
            ),
            xaxis=dict(
                tickangle=-45,
            ),
        )

    else:

        total_depo = (
            depo_chart
            .groupby(
                "Depo"
            )["Jumlah"]
            .transform("sum")
        )

        depo_chart["Persentase"] = (
            depo_chart["Jumlah"]
            / total_depo
            * 100
        )

        fig_depo = px.bar(
            depo_chart,
            x="Depo",
            y="Persentase",
            color="Location",
            barmode="group",
            text_auto=".1f%",
            color_discrete_map={
                "Pass": "#2E86DE",
                "Fail": "#E74C3C",
            },
            labels={
                "Depo": "Nama Depo",
                "Persentase": "Persentase (%)",
                "Location": "Status",
            },
        )

        fig_depo.update_traces(
            texttemplate="%{y:.1f}%",
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Status: %{fullData.name}<br>"
                "Persentase: %{y:.1f}%"
                "<extra></extra>"
            )
        )

        fig_depo.update_layout(
            yaxis=dict(
                title="Persentase (%)",
                range=[0, 100],
                ticksuffix="%",
                dtick=20,
            ),
            xaxis=dict(
                tickangle=-45,
            ),
        )

    st.plotly_chart(
        fig_depo,
        use_container_width=True,
        config={
            "displayModeBar": True,
        },
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
        "Tanggal Order Priority Tampilan",
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
            "Tanggal Order Priority Tampilan":
                "Tanggal Order Priority",
        }
    )

    st.dataframe(
        detail_display,
        use_container_width=True,
        hide_index=True,
    )