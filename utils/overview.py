import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.priority_analysis import build_priority_summary

FAIL = "#C45F51"
PASS = "#158278"
INK = "#24363B"
MUTED = "#657981"
TOP_N = 5
MIN_VOLUME_FOR_RATE = 10
CHART_HEIGHT = 185  
MODES = ("Jumlah Fail", "Fail Rate", "Jumlah Pass", "Pass Rate")


def _compact_style():
    st.markdown("""
    <style>
      section.main .block-container {
        max-width: 1650px;
        padding-top: 1.05rem !important;
        padding-bottom: 0.25rem !important;
      }
      .st-key-fol-single-screen [data-testid="stVerticalBlock"] {
        gap: 0.28rem !important;
      }
      .st-key-fol-single-screen [data-testid="stMetric"] {
        padding: 0.08rem 0.15rem !important;
      }
      .st-key-fol-single-screen [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        line-height: 1.05 !important;
      }
      .st-key-fol-single-screen [data-testid="stMetricLabel"] {
        font-size: 0.73rem !important;
      }
      .st-key-fol-single-screen [data-testid="stPlotlyChart"] {
        margin: -0.25rem 0 -0.45rem !important;
      }
      .st-key-fol-single-screen [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 8px;
      }
      .st-key-fol-single-screen div[data-testid="stSelectbox"] label {
        font-size: 0.7rem !important;
      }
    </style>
    """, unsafe_allow_html=True)


def _fmt(value):
    return f"{int(value):,}".replace(",", ".")


def _metric_config(mode):
    if mode not in MODES:
        raise ValueError(f"Pilihan metrik tidak didukung: {mode}")
    status = "Pass" if "Pass" in mode else "Fail"
    is_rate = mode.endswith("Rate")
    return status, is_rate, (f"{status} Rate (%)" if is_rate else f"Total {status}")


def _rank(frame, mode):
    status, is_rate, column = _metric_config(mode)
    if frame.empty:
        return frame.copy()
    count_col = f"Total {status}"
    df = frame.loc[frame[count_col] > 0].copy()
    if is_rate:
        df = df.loc[df["Total FOL"] >= MIN_VOLUME_FOR_RATE]
    secondary = count_col if is_rate else f"{status} Rate (%)"
    return df.sort_values(
        [column, secondary, "Total FOL"],
        ascending=[False, False, False],
        kind="stable",
    ).head(TOP_N)


def _figure(fig, left=34):
    fig.update_layout(
        height=CHART_HEIGHT,
        margin=dict(l=left, r=40, t=23, b=20),
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(family="Arial", color=MUTED, size=10),
        hoverlabel=dict(bgcolor=INK, font_color="white"),
        bargap=0.3,
    )
    fig.update_xaxes(title=None, zeroline=False)
    fig.update_yaxes(title=None, zeroline=False, gridcolor="#E8EEEC")
    return fig


def _trend_chart(frame, frequency, mode):
    if frame.empty:
        return None

    status, rate, col = _metric_config(mode)
    color = PASS if status == "Pass" else FAIL
    count = f"Total {status}"
    rate_col = f"{status} Rate (%)"
    series = frame[col].astype(float)
    labels = ([f"{v:.1f}%" for v in series]
              if rate else [_fmt(v) for v in series])

    fig = go.Figure(go.Scatter(
        x=frame["Periode"], y=series,
        mode="lines+markers+text",
        text=labels,
        textposition="top center",
        textfont=dict(size=9, color=INK),
        cliponaxis=False,
        line=dict(color=color, width=2.5),
        marker=dict(size=6, color="white", line=dict(color=color, width=2)),
        fill="tozeroy",
        fillcolor="rgba(196,95,81,0.07)" if status == "Fail" else "rgba(21,130,120,0.07)",
        customdata=frame[["Total FOL", count, rate_col]].to_numpy(),
        hovertemplate=(
            "%{x|%d %b %Y}"
            "<br>Total FOL: %{customdata[0]:,.0f}"
            f"<br>Jumlah {status}: %{{customdata[1]:,.0f}}"
            f"<br>{status} Rate: %{{customdata[2]:.1f}}%"
            "<extra></extra>"
        ),
    ))
    _figure(fig, left=37)
    fig.update_yaxes(range=[0, max(1, float(series.max()) * 1.4)],
                     ticksuffix="%" if rate else "", nticks=4)
    fig.update_xaxes(showgrid=False, nticks=6,
                     tickformat="%d %b" if frequency == "Harian" else "%d %b %y")
    return fig


def _rank_chart(frame, mode, group):
    selected = _rank(frame, mode)
    if selected.empty:
        return None

    status, rate, column = _metric_config(mode)
    color = PASS if status == "Pass" else FAIL
    count_col = f"Total {status}"
    rate_col = f"{status} Rate (%)"
    contribution = f"Kontribusi {status} (%)"
    ordered = selected.iloc[::-1]

    if group == "Driver":
        labels = [
            f"{str(r['Nama Driver'])[:18]} · {str(r['Depo'])[:13]}"
            for _, r in ordered.iterrows()
        ]
        extra = ordered[["Nama Driver", "Depo", "Total FOL", count_col,
                         rate_col, contribution]].to_numpy()
        tooltip = (
            "<b>%{customdata[0]}</b>"
            "<br>Depo: %{customdata[1]}"
            "<br>Total FOL: %{customdata[2]:,.0f}"
            f"<br>Jumlah {status}: %{{customdata[3]:,.0f}}"
            f"<br>{status} Rate: %{{customdata[4]:.1f}}%"
            f"<br>Kontribusi {status}: %{{customdata[5]:.1f}}%"
            "<extra></extra>"
        )
        left = 195
    else:
        labels = [str(v)[:25] for v in ordered["Depo"]]
        extra = ordered[["Total FOL", count_col, rate_col, contribution]].to_numpy()
        tooltip = (
            "<b>%{customdata[4]}</b>"
            "<br>Total FOL: %{customdata[0]:,.0f}"
            f"<br>Jumlah {status}: %{{customdata[1]:,.0f}}"
            f"<br>{status} Rate: %{{customdata[2]:.1f}}%"
            f"<br>Kontribusi {status}: %{{customdata[3]:.1f}}%"
            "<extra></extra>"
        )
        # Atribut kelima khusus Depo untuk menjaga hover nama utuh.
        extra = ordered[["Total FOL", count_col, rate_col, contribution, "Depo"]].to_numpy()
        left = 112

    values = ordered[column].astype(float)
    fig = go.Figure(go.Bar(
        x=values,
        y=list(range(len(ordered))),
        orientation="h",
        marker_color=color,
        text=([f"{v:.1f}%" for v in values]
              if rate else [_fmt(v) for v in values]),
        textposition="outside",
        textfont=dict(size=10, color=INK),
        cliponaxis=False,
        customdata=extra,
        hovertemplate=tooltip,
    ))
    _figure(fig, left=left)
    fig.update_yaxes(tickmode="array", tickvals=list(range(len(ordered))),
                     ticktext=labels, showgrid=False, tickfont=dict(size=9))
    fig.update_xaxes(range=[0, max(1, float(values.max()) * 1.29)],
                     ticksuffix="%" if rate else "", nticks=4)
    return fig


def _show_chart(fig, message):
    if fig is None:
        st.caption(message)
    else:
        st.plotly_chart(fig, width="stretch", theme=None,
                        config={"displayModeBar": False, "responsive": True})


def _insight_lines(summary, mode):
    """Tiga temuan singkat agar panel analisis tidak menambah tinggi halaman."""
    status, _, _ = _metric_config(mode)
    total = int(summary["kpis"][f"total_{status.lower()}"])
    if total == 0:
        return [f"Tidak ada status {status} pada data terfilter."]

    count_col = f"Total {status}"
    rate_col = f"{status} Rate (%)"
    depo = _rank(summary["by_depo"].loc[
        summary["by_depo"]["Depo"] != "Depo Tidak Terdata"
    ], mode)
    drivers = _rank(summary["focus_drivers"], mode)
    lines = []
    if not depo.empty:
        r = depo.iloc[0]
        lines.append(
            f"**Depo teratas:** {r['Depo']} · {_fmt(r[count_col])} {status} "
            f"({r[rate_col]:.1f}%)"
        )
    if not drivers.empty:
        r = drivers.iloc[0]
        lines.append(
            f"**Driver teratas:** {r['Nama Driver']} · {r['Depo']} · "
            f"{_fmt(r[count_col])} {status} ({r[rate_col]:.1f}%)"
        )
    lines.append(
        f"**Kontribusi 3 Depo terbesar (volume):** {summary['share_top3_depos']:.1f}%"
    )
    if mode.endswith("Rate"):
        lines.append(f"*Rate minimum {MIN_VOLUME_FOR_RATE} FOL per unit.*")
    return lines


def render_overview(filtered_df, total_rows=None):
    """Halaman compact. Tidak mengubah filter/sidebar/Analisis Lengkap."""
    _compact_style()
    if filtered_df.empty:
        st.warning("Tidak ada data sesuai filter sidebar.")
        return

    dates = pd.to_datetime(filtered_df["Tanggal Order Priority"], errors="coerce").dropna()
    period = (f"{dates.min():%d %b %Y} – {dates.max():%d %b %Y}"
              if not dates.empty else "Periode tidak tersedia")
    depo_options = sorted(filtered_df["Depo"].dropna().astype(str).str.strip()
                          .loc[lambda x: x.ne("")].unique().tolist())

    with st.container(key="fol-single-screen"):
        title, period_col = st.columns([3.4, 1], vertical_alignment="center", gap="small")
        with title:
            st.markdown("### FOL Performance Overview")
        with period_col:
            st.caption(f"{period}")

        one, two, three = st.columns([1, 1.15, 1.4], gap="small")
        with one:
            frequency = st.selectbox("Tren", ("Harian", "Mingguan"), key="exec_trend_scale")
        with two:
            mode = st.selectbox("Metrik", MODES, key="exec_rank_mode")
        with three:
            focus = st.selectbox("Fokus Driver", ["Seluruh Depo", *depo_options],
                                 key="exec_depo_focus")

        status, _, _ = _metric_config(mode)
        summary = build_priority_summary(
            filtered_df,
            granularity=frequency,
            focus_depo=None if focus == "Seluruh Depo" else focus,
            status=status,
        )
        kpi = summary["kpis"]
        metric_data = (
            ("TOTAL FOL", _fmt(kpi["total_fol"])),
            (f"TOTAL {status.upper()}", _fmt(kpi[f"total_{status.lower()}"])),
            (f"{status.upper()} RATE", f"{kpi[f'persentase_{status.lower()}']:.1f}%"),
        )
        for slot, (label, value) in zip(st.columns(3, gap="small"), metric_data):
            with slot:
                with st.container(border=True):
                    st.metric(label, value)

        left, right = st.columns([1.22, 1], gap="small")
        with left:
            with st.container(border=True):
                st.markdown(f"**01 · Tren {mode}**")
                _show_chart(_trend_chart(summary["trend"], frequency, mode),
                            "Tidak ada tanggal yang valid.")
        with right:
            with st.container(border=True):
                st.markdown(f"**02 · Depo berdasarkan {mode}**")
                named = summary["by_depo"].loc[
                    summary["by_depo"]["Depo"] != "Depo Tidak Terdata"
                ]
                _show_chart(_rank_chart(named, mode, "Depo"),
                            "Tidak ada Depo sesuai kriteria.")

        left, right = st.columns([1.22, 1], gap="small")
        with left:
            with st.container(border=True):
                st.markdown(f"**03 · Driver + Depo berdasarkan {mode}**")
                _show_chart(_rank_chart(summary["focus_drivers"], mode, "Driver"),
                            "Tidak ada Driver sesuai kriteria.")
        with right:
            with st.container(border=True):
                st.markdown("**04 · Operational Insights**")
                for line in _insight_lines(summary, mode):
                    st.markdown(line)
                st.caption("Peringkat untuk prioritas evaluasi, bukan bukti penyebab masalah.")

        n = len(filtered_df)
        total = total_rows if total_rows is not None else n
        st.caption(f"{_fmt(n)} dari {_fmt(total)} data FOL · Filter utama berada di sidebar")
