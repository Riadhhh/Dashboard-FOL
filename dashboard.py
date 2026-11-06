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

from utils.overview import render_overview

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

        # Normalisasi nama kolom sebelum validasi, agar "Depo " terbaca "Depo".
        df_file.columns = [
            col.strip() if isinstance(col, str) else col
            for col in df_file.columns
        ]
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
    st.error("Validasi upload belum berhasil. Perbaiki file berikut:")
    for error in error_files:
        st.write(f"- {error}")
    st.stop()

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

# Validasi akhir terhadap dataset gabungan sebelum mode dashboard tersedia.
if df.empty:
    st.error("Tidak ada data Driver FOL yang memenuhi kriteria validasi.")
    st.stop()

min_date, max_date = get_data_period(df)
if min_date is None or max_date is None:
    st.error("Tidak ada tanggal order valid setelah data diproses.")
    st.stop()

with st.sidebar:
    st.divider()
    view_mode = st.radio(
        "Mode Dashboard",
        ["Dashboard Overview", "Full Analysis"],
        key="dashboard_mode",
        help="Ditampilkan setelah seluruh file berhasil divalidasi.",
    )

if view_mode == "Full Analysis":
    st.title("Dashboard FOL")
    st.caption(
        "Dashboard untuk menganalisis data FOL berdasarkan "
        "tanggal, driver, depo, serta status Pass dan Fail."
    )

if "week_selection" not in st.session_state:

    st.session_state.week_selection = []


def update_week_selection():

    st.session_state.week_selection = (
        st.session_state.week_filter
    )


with st.sidebar:

    st.divider()

    st.header("Filter Data")

    if view_mode == "Full Analysis":
        st.subheader("Fokus Analisis Driver")
        driver_analysis = st.radio(
            "Pilih status",
            options=["Pass", "Fail"],
            index=1,
            horizontal=True,
            label_visibility="collapsed",
        )

    min_date, max_date = get_data_period(
        df
    )

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

if view_mode == "Dashboard Overview":
    render_overview(filtered_df, total_rows=len(df))
    st.stop()

st.caption(
    f"Menampilkan {total_filtered} "
    f"dari {total_data} data FOL"
)

kpis = calculate_kpis(filtered_df)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total FOL", f"{kpis['total_fol']:,}".replace(",", "."))
col2.metric("Total Pass", f"{kpis['total_pass']:,}".replace(",", "."))
col3.metric("Total Fail", f"{kpis['total_fail']:,}".replace(",", "."))
col4.metric("Persentase Pass", f"{kpis['persentase_pass']:.1f}%")
col5.metric("Persentase Fail", f"{kpis['persentase_fail']:.1f}%")

st.divider()

col_distribution, col_depo = st.columns(2)

with col_distribution:

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
                "Pass": "#237E7A",
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
            key="location_distribution_chart",
        )

with col_depo:

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
                "Persentase",
                "Jumlah",
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
                    "Pass": "#237E7A",
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
                text_auto=".1f",
                color_discrete_map={
                    "Pass": "#237E7A",
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
            key="depo_comparison_chart",
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

    display_mode_daily = st.selectbox(
        "Tampilkan Berdasarkan",
        ["Persentase", "Jumlah"],
        index=0,
        key="daily_trend_display_mode",
    )

    if display_mode_daily == "Persentase":
        fig_daily = px.line(
            daily_summary,
            x="Tanggal Order Priority",
            y="Persentase",
            color="Location",
            markers=True,
            text="Persentase",
            color_discrete_map={
                "Pass": "#237E7A",
                "Fail": "#E74C3C",
            },
            labels={
                "Tanggal Order Priority": (
                    "Tanggal Order Priority"
                ),
                "Persentase": "Persentase FOL",
                "Location": "Status",
            },
            custom_data=[
                "Jumlah",
                "Total FOL",
            ],
        )

        fig_daily.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="top center",
            hovertemplate=(
                "<b>%{x|%d-%b-%Y}</b><br>"
                "Status: %{fullData.name}<br>"
                "Persentase: %{y:.1f}%<br>"
                "Jumlah: %{customdata[0]:,.0f}<br>"
                "Total FOL: %{customdata[1]:,.0f}"
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
                title="Persentase FOL",
                tickformat=".1f",
                ticksuffix="%",
                rangemode="tozero",
            ),
            hovermode="x unified",
        )

    else:
        fig_daily = px.line(
            daily_summary,
            x="Tanggal Order Priority",
            y="Jumlah",
            color="Location",
            markers=True,
            text="Jumlah",
            color_discrete_map={
                "Pass": "#237E7A",
                "Fail": "#E74C3C",
            },
            labels={
                "Tanggal Order Priority": (
                    "Tanggal Order Priority"
                ),
                "Jumlah": "Jumlah FOL",
                "Location": "Status",
            },
            custom_data=[
                "Persentase",
                "Total FOL",
            ],
        )

        fig_daily.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="top center",
            hovertemplate=(
                "<b>%{x|%d-%b-%Y}</b><br>"
                "Status: %{fullData.name}<br>"
                "Jumlah: %{y:,.0f}<br>"
                "Persentase: %{customdata[0]:.1f}%<br>"
                "Total FOL: %{customdata[1]:,.0f}"
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
                title="Jumlah FOL",
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
        key="daily_trend_chart",
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

if pass_data.empty and fail_data.empty:
    st.info(
        "Tidak terdapat data driver "
        "untuk ditampilkan."
    )

else:
    driver_summary = calculate_pass_fail_by_driver(
        filtered_df
    )

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

    display_mode_analysis = st.selectbox(
        "Tampilkan Berdasarkan",
        [
            "Persentase",
            "Jumlah",
        ],
        key="driver_analysis_display_mode",
    )

    max_driver_analysis = len(
        ranking_data
    )

    if max_driver_analysis <= 1:

        top_n_analysis = 1

    else:

        top_n_analysis = st.slider(
            "Top N Driver",
            min_value=1,
            max_value=max_driver_analysis,
            value=min(
                10,
                max_driver_analysis
            ),
            key="top_n_analysis",
        )

    selected_drivers_analysis = (
        ranking_data
        .head(
            top_n_analysis
        )
        .index
        .tolist()
    )

    pass_chart_data = pass_data[
        pass_data["Nama Driver"].isin(
            selected_drivers_analysis
        )
    ].copy()

    fail_chart_data = fail_data[
        fail_data["Nama Driver"].isin(
            selected_drivers_analysis
        )
    ].copy()

    total_driver = (
        driver_summary
        .groupby(
            "Nama Driver"
        )["Jumlah"]
        .sum()
        .reset_index(
            name="Total FOL"
        )
    )

    pass_chart_data = pass_chart_data.merge(
        total_driver,
        on="Nama Driver",
        how="left"
    )

    fail_chart_data = fail_chart_data.merge(
        total_driver,
        on="Nama Driver",
        how="left"
    )

    pass_chart_data["Persentase Pass"] = (
        pass_chart_data["Jumlah Pass"]
        / pass_chart_data["Total FOL"]
        * 100
    )

    fail_chart_data["Persentase Fail"] = (
        fail_chart_data["Jumlah Fail"]
        / fail_chart_data["Total FOL"]
        * 100
    )

    pass_chart_data["Driver Depo"] = (
        pass_chart_data["Nama Driver"]
        + " ("
        + pass_chart_data["Depo"]
        + ")"
    )

    fail_chart_data["Driver Depo"] = (
        fail_chart_data["Nama Driver"]
        + " ("
        + fail_chart_data["Depo"]
        + ")"
    )

    pass_chart_data = pass_chart_data.sort_values(
        "Persentase Pass"
        if display_mode_analysis == "Persentase"
        else "Jumlah Pass",
        ascending=False
    )

    fail_chart_data = fail_chart_data.sort_values(
        "Persentase Fail"
        if display_mode_analysis == "Persentase"
        else "Jumlah Fail",
        ascending=False
    )

    col_pass, col_fail = st.columns(2)

    with col_pass:

        if display_mode_analysis == "Jumlah":

            st.markdown(
                "### Pass Terbanyak Berdasarkan Driver"
            )

            fig_pass_driver = px.bar(
                pass_chart_data,
                x="Driver Depo",
                y="Jumlah Pass",
                text_auto=".0f",
                color_discrete_sequence=[
                    "#237E7A"
                ],
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Jumlah Pass": "Jumlah Pass",
                },
            )

            fig_pass_driver.update_traces(
                texttemplate="%{y:,.0f}",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Jumlah Pass: %{y:,.0f}<br>"
                    "Total FOL: %{customdata[0]:,.0f}<br>"
                    "Persentase Pass: %{customdata[1]:.1f}%"
                    "<extra></extra>"
                ),
                customdata=pass_chart_data[
                    [
                        "Total FOL",
                        "Persentase Pass",
                    ]
                ].values,
            )

            fig_pass_driver.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Jumlah Pass",
                    tickformat=",.0f",
                    rangemode="tozero",
                ),
                showlegend=False,
            )

        else:

            st.markdown(
                "### Persentase Pass Berdasarkan Driver"
            )

            fig_pass_driver = px.bar(
                pass_chart_data,
                x="Driver Depo",
                y="Persentase Pass",
                text_auto=".1f",
                color_discrete_sequence=[
                    "#237E7A"
                ],
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Persentase Pass": "Persentase Pass (%)",
                },
            )

            fig_pass_driver.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Persentase Pass: %{y:.1f}%<br>"
                    "Jumlah Pass: %{customdata[0]:,.0f}<br>"
                    "Total FOL: %{customdata[1]:,.0f}"
                    "<extra></extra>"
                ),
                customdata=pass_chart_data[
                    [
                        "Jumlah Pass",
                        "Total FOL",
                    ]
                ].values,
            )

            fig_pass_driver.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Persentase Pass (%)",
                    range=[0, 100],
                    ticksuffix="%",
                    dtick=20,
                ),
                showlegend=False,
            )

        st.plotly_chart(
            fig_pass_driver,
            use_container_width=True,
            config={
                "displayModeBar": True,
            },
            key="pass_driver_analysis_chart",
        )

    with col_fail:

        if display_mode_analysis == "Jumlah":

            st.markdown(
                "### Fail Terbanyak Berdasarkan Driver"
            )

            fig_fail_driver = px.bar(
                fail_chart_data,
                x="Driver Depo",
                y="Jumlah Fail",
                text_auto=".0f",
                color_discrete_sequence=[
                    "#E74C3C"
                ],
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Jumlah Fail": "Jumlah Fail",
                },
            )

            fig_fail_driver.update_traces(
                texttemplate="%{y:,.0f}",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Jumlah Fail: %{y:,.0f}<br>"
                    "Total FOL: %{customdata[0]:,.0f}<br>"
                    "Persentase Fail: %{customdata[1]:.1f}%"
                    "<extra></extra>"
                ),
                customdata=fail_chart_data[
                    [
                        "Total FOL",
                        "Persentase Fail",
                    ]
                ].values,
            )

            fig_fail_driver.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Jumlah Fail",
                    tickformat=",.0f",
                    rangemode="tozero",
                ),
                showlegend=False,
            )

        else:

            st.markdown(
                "### Persentase Fail Berdasarkan Driver"
            )

            fig_fail_driver = px.bar(
                fail_chart_data,
                x="Driver Depo",
                y="Persentase Fail",
                text_auto=".1f",
                color_discrete_sequence=[
                    "#E74C3C"
                ],
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Persentase Fail": "Persentase Fail (%)",
                },
            )

            fig_fail_driver.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Persentase Fail: %{y:.1f}%<br>"
                    "Jumlah Fail: %{customdata[0]:,.0f}<br>"
                    "Total FOL: %{customdata[1]:,.0f}"
                    "<extra></extra>"
                ),
                customdata=fail_chart_data[
                    [
                        "Jumlah Fail",
                        "Total FOL",
                    ]
                ].values,
            )

            fig_fail_driver.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Persentase Fail (%)",
                    range=[0, 100],
                    ticksuffix="%",
                    dtick=20,
                ),
                showlegend=False,
            )

        st.plotly_chart(
            fig_fail_driver,
            use_container_width=True,
            config={
                "displayModeBar": True,
            },
            key="fail_driver_analysis_chart",
        )

st.divider()

st.subheader(
    "Perbandingan Pass dan Fail Berdasarkan Driver"
)

driver_summary_final = calculate_pass_fail_by_driver(
    filtered_df
)

if driver_summary_final.empty:

    st.info(
        "Tidak terdapat data driver untuk ditampilkan."
    )

else:

    ranking_data_final = (
        driver_summary_final
        .pivot(
            index="Nama Driver",
            columns="Location",
            values="Jumlah"
        )
        .fillna(0)
    )

    if "Pass" not in ranking_data_final.columns:
        ranking_data_final["Pass"] = 0

    if "Fail" not in ranking_data_final.columns:
        ranking_data_final["Fail"] = 0

    ranking_data_final["Jumlah Pass"] = (
        ranking_data_final["Pass"]
    )

    ranking_data_final["Jumlah Fail"] = (
        ranking_data_final["Fail"]
    )

    ranking_column_final = (
        "Jumlah Pass"
        if driver_analysis == "Pass"
        else "Jumlah Fail"
    )

    ranking_data_final = ranking_data_final.sort_values(
        ranking_column_final,
        ascending=False
    )

    display_mode_final = st.selectbox(
        "Tampilkan Berdasarkan",
        [
            "Persentase",
            "Jumlah",
        ],
        index=0,
        key="driver_final_display_mode",
    )

    max_driver_final = len(
        ranking_data_final
    )

    if max_driver_final <= 1:

        top_n_final = 1

    else:

        top_n_final = st.slider(
            "Top N Driver",
            min_value=1,
            max_value=max_driver_final,
            value=min(
                10,
                max_driver_final
            ),
            key="driver_final_top_n",
        )

    selected_drivers_final = (
        ranking_data_final
        .head(
            top_n_final
        )
        .index
        .tolist()
    )

    driver_chart_final = driver_summary_final[
        driver_summary_final[
            "Nama Driver"
        ].isin(
            selected_drivers_final
        )
    ].copy()

    driver_chart_final["Driver Depo"] = (
        driver_chart_final["Nama Driver"]
        + " ("
        + driver_chart_final["Depo"]
        + ")"
    )

    driver_order_final = (
        driver_chart_final
        .groupby(
            "Driver Depo"
        )["Jumlah"]
        .sum()
        .sort_values(
            ascending=True
        )
        .index
        .tolist()
    )

    total_driver_final = (
        driver_chart_final
        .groupby(
            "Nama Driver",
            observed=True
        )["Jumlah"]
        .transform("sum")
    )

    driver_chart_final["Persentase"] = (
        driver_chart_final["Jumlah"]
        / total_driver_final
        * 100
    )

    col_driver_1, col_driver_2 = st.columns(2)

    with col_driver_1:

        st.markdown(
            "### Perbandingan Jumlah Pass dan Fail Berdasarkan Driver"
        )

        if display_mode_final == "Jumlah":

            fig_pass_fail_grouped = px.bar(
                driver_chart_final,
                x="Driver Depo",
                y="Jumlah",
                color="Location",
                barmode="group",
                text="Jumlah",
                color_discrete_map={
                    "Pass": "#237E7A",
                    "Fail": "#E74C3C",
                },
                category_orders={
                    "Driver Depo": driver_order_final
                },
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Jumlah": "Jumlah FOL",
                    "Location": "Status",
                },
            )

            fig_pass_fail_grouped.update_traces(
                texttemplate="%{y:,.0f}",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Status: %{fullData.name}<br>"
                    "Jumlah FOL: %{y:,.0f}"
                    "<extra></extra>"
                ),
            )

            fig_pass_fail_grouped.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Jumlah FOL",
                    tickformat=",.0f",
                    rangemode="tozero",
                ),
            )

        else:

            fig_pass_fail_grouped = px.bar(
                driver_chart_final,
                x="Driver Depo",
                y="Persentase",
                color="Location",
                barmode="group",
                text="Persentase",
                color_discrete_map={
                    "Pass": "#237E7A",
                    "Fail": "#E74C3C",
                },
                category_orders={
                    "Driver Depo": driver_order_final
                },
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Persentase": "Persentase (%)",
                    "Location": "Status",
                },
            )

            fig_pass_fail_grouped.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Status: %{fullData.name}<br>"
                    "Persentase: %{y:.1f}%"
                    "<extra></extra>"
                ),
            )

            fig_pass_fail_grouped.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Persentase (%)",
                    range=[0, 100],
                    ticksuffix="%",
                    dtick=20,
                ),
            )

        st.plotly_chart(
            fig_pass_fail_grouped,
            use_container_width=True,
            config={
                "displayModeBar": True,
            },
            key="final_driver_grouped_chart",
        )

    with col_driver_2:

        st.markdown(
            "### Pass vs Fail Berdasarkan Driver"
        )

        if display_mode_final == "Jumlah":

            fig_pass_fail_stacked = px.bar(
                driver_chart_final,
                x="Driver Depo",
                y="Jumlah",
                color="Location",
                barmode="stack",
                text="Jumlah",
                color_discrete_map={
                    "Pass": "#237E7A",
                    "Fail": "#E74C3C",
                },
                category_orders={
                    "Driver Depo": driver_order_final
                },
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Jumlah": "Jumlah FOL",
                    "Location": "Status",
                },
            )

            fig_pass_fail_stacked.update_traces(
                texttemplate="%{y:,.0f}",
                textposition="inside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Status: %{fullData.name}<br>"
                    "Jumlah FOL: %{y:,.0f}"
                    "<extra></extra>"
                ),
            )

            fig_pass_fail_stacked.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Jumlah FOL",
                    tickformat=",.0f",
                    rangemode="tozero",
                ),
            )

        else:

            fig_pass_fail_stacked = px.bar(
                driver_chart_final,
                x="Driver Depo",
                y="Persentase",
                color="Location",
                barmode="stack",
                text="Persentase",
                color_discrete_map={
                    "Pass": "#237E7A",
                    "Fail": "#E74C3C",
                },
                category_orders={
                    "Driver Depo": driver_order_final
                },
                labels={
                    "Driver Depo": "Driver (Depo)",
                    "Persentase": "Persentase (%)",
                    "Location": "Status",
                },
            )

            fig_pass_fail_stacked.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="inside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Status: %{fullData.name}<br>"
                    "Persentase: %{y:.1f}%"
                    "<extra></extra>"
                ),
            )

            fig_pass_fail_stacked.update_layout(
                xaxis=dict(
                    tickangle=-45,
                ),
                yaxis=dict(
                    title="Persentase (%)",
                    range=[0, 100],
                    ticksuffix="%",
                    dtick=20,
                ),
            )

        st.plotly_chart(
            fig_pass_fail_stacked,
            use_container_width=True,
            config={
                "displayModeBar": True,
            },
            key="final_driver_stacked_chart",
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