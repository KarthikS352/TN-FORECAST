"""
TN Load Forecasting — Streamlit Web App
Reads forecast CSV from GitHub. Updates automatically when Colab pushes.
Deploy at: https://share.streamlit.io
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import io

# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="TN Load Forecasting",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.main{background-color:#05080f;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1628 0%,#0f2040 100%);border-right:1px solid #1a3a5c;}
[data-testid="stSidebar"] *{color:#a8c8e8 !important;}
div[data-testid="stMetric"]{background:linear-gradient(135deg,#0a1628,#102040);border:1px solid #1a3a5c;border-radius:14px;padding:18px 20px;}
div[data-testid="stMetric"] label{color:#6a9ec0 !important;font-size:12px;letter-spacing:1px;text-transform:uppercase;}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#e8f4fd !important;font-family:'DM Mono',monospace;font-size:26px;}
.kpi-card{background:linear-gradient(135deg,#0a1628,#102040);border:1px solid #1a3a5c;border-radius:14px;padding:22px 24px;text-align:center;margin-bottom:12px;}
.kpi-label{color:#6a9ec0;font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;}
.kpi-value{color:#e8f4fd;font-size:30px;font-weight:700;font-family:'DM Mono',monospace;}
.kpi-sub{color:#3a7aaa;font-size:12px;margin-top:4px;}
.sec{color:#e8f4fd;font-size:18px;font-weight:700;border-left:3px solid #2d7dd2;padding-left:12px;margin:28px 0 16px 0;}
.info-box{background:rgba(45,125,210,0.08);border:1px solid rgba(45,125,210,0.25);border-radius:10px;padding:14px 18px;color:#7ab0d4;font-size:13px;margin:10px 0;}
.live{display:inline-block;background:#0d3d1f;color:#27ae60;border:1px solid #27ae60;border-radius:20px;padding:4px 14px;font-size:12px;font-weight:600;letter-spacing:1px;}
.nodata{display:inline-block;background:#3d0d0d;color:#e74c3c;border:1px solid #e74c3c;border-radius:20px;padding:4px 14px;font-size:12px;font-weight:600;}
footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  GITHUB SETTINGS  — read from Streamlit Secrets
# ══════════════════════════════════════════════════════════════
def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return default

GITHUB_TOKEN  = get_secret("GITHUB_TOKEN")
GITHUB_REPO   = get_secret("GITHUB_REPO",   "yourusername/tn-forecast")
GITHUB_BRANCH = get_secret("GITHUB_BRANCH", "main")
RAW_BASE      = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

# ══════════════════════════════════════════════════════════════
#  DATA LOADERS  (cache 60 seconds = auto refresh)
# ══════════════════════════════════════════════════════════════
def gh_headers():
    h = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h

@st.cache_data(ttl=60)
def load_meta():
    try:
        r = requests.get(f"{RAW_BASE}/data/forecast_meta.json",
                         headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            return r.json(), True
    except Exception:
        pass
    return {}, False

@st.cache_data(ttl=60)
def load_hourly():
    try:
        r = requests.get(f"{RAW_BASE}/data/TN_Forecast_Hourly.csv",
                         headers=gh_headers(), timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            return df, True
    except Exception:
        pass
    return pd.DataFrame(), False

@st.cache_data(ttl=60)
def load_daily():
    try:
        r = requests.get(f"{RAW_BASE}/data/TN_Forecast_Daily.csv",
                         headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            df['date'] = pd.to_datetime(df['date'])
            return df, True
    except Exception:
        pass
    return pd.DataFrame(), False

# ══════════════════════════════════════════════════════════════
#  PLOTLY BASE THEME
# ══════════════════════════════════════════════════════════════
BG = "#0a1628"
GR = "#1a3a5c"
TX = "#e8f4fd"
TK = "#6a9ec0"
C1 = "#2d7dd2"
C2 = "#e74c3c"
C3 = "#27ae60"
C4 = "#f39c12"

BL = dict(
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(color=TX, family="Syne"),
    xaxis=dict(gridcolor=GR, zerolinecolor=GR, tickfont=dict(color=TK)),
    yaxis=dict(gridcolor=GR, zerolinecolor=GR, tickfont=dict(color=TK)),
    legend=dict(bgcolor="rgba(10,22,40,0.8)", bordercolor=GR, borderwidth=1),
    margin=dict(l=50, r=30, t=55, b=50),
    hovermode="x unified",
)

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:20px 0 10px 0;'>
      <div style='font-size:48px;'>⚡</div>
      <div style='font-size:22px;font-weight:800;color:#e8f4fd;'>TN Load Forecast</div>
      <div style='font-size:11px;color:#3a7aaa;letter-spacing:2px;margin-top:4px;'>TAMIL NADU STATE GRID</div>
    </div>
    <hr style='border-color:#1a3a5c;margin:12px 0;'>
    """, unsafe_allow_html=True)

    st.markdown("**🔗 Data Source**")
    st.code(f"{GITHUB_REPO}\nbranch: {GITHUB_BRANCH}", language="text")

    st.markdown("**🔄 Refresh**")
    if st.button("🔄  Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<hr style='border-color:#1a3a5c;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:12px;color:#3a7aaa;line-height:1.9;'>
      <b style='color:#6a9ec0;'>Automation Flow:</b><br>
      1️⃣  Colab runs forecast<br>
      2️⃣  Colab pushes CSV → GitHub<br>
      3️⃣  App reads GitHub (60s cache)<br>
      4️⃣  Dashboard updates live
    </div>
    """, unsafe_allow_html=True)

# Auto refresh meta tag (every 60 seconds)
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<h1 style='text-align:center;font-size:36px;font-weight:800;color:#e8f4fd;margin-bottom:4px;'>
  ⚡ Tamil Nadu Grid Load Forecasting
</h1>
<p style='text-align:center;color:#3a7aaa;font-size:15px;margin-bottom:10px;'>
  April · May · June 2026 &nbsp;|&nbsp; Gradient Boosting Model &nbsp;|&nbsp; Hourly MW
</p>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  LOAD DATA
# ══════════════════════════════════════════════════════════════
meta, meta_ok = load_meta()
hourly, h_ok  = load_hourly()
daily,  d_ok  = load_daily()

# Status row
cs1, cs2, cs3 = st.columns([1, 3, 6])
with cs1:
    if meta_ok and h_ok:
        st.markdown('<span class="live">● LIVE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="nodata">● NO DATA</span>', unsafe_allow_html=True)
with cs2:
    if meta_ok:
        st.markdown(
            f'<span style="color:#3a7aaa;font-size:13px;">'
            f'Updated: {meta.get("last_updated","—")}</span>',
            unsafe_allow_html=True)

# No data screen
if not h_ok or not meta_ok:
    st.markdown("""
    <div class='info-box' style='border-color:rgba(231,76,60,0.4);
         background:rgba(231,76,60,0.07);color:#c07878;margin-top:30px;'>
      <b>⚠️  No forecast data in GitHub yet.</b><br><br>
      Steps to populate:<br>
      1. Open your Colab notebook<br>
      2. Run all cells  Cell 1 → Cell 13<br>
      3. Run Cell 14b  (GitHub push cell)<br>
      4. Return here — data appears automatically within 60 seconds
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════
#  KPI CARDS
# ══════════════════════════════════════════════════════════════
st.markdown("<div class='sec'>📊 Forecast Summary</div>", unsafe_allow_html=True)

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpis = [
    (k1, "April Avg",  meta.get('april_avg_mw','—'), "MW"),
    (k2, "May Avg",    meta.get('may_avg_mw',  '—'), "MW"),
    (k3, "June Avg",   meta.get('june_avg_mw', '—'), "MW"),
    (k4, "Peak Load",  meta.get('peak_mw',     '—'), "MW"),
    (k5, "MAPE",       meta.get('model_mape',  '—'), "%"),
    (k6, "R²",         meta.get('model_r2',    '—'), ""),
]
for col, lbl, val, unit in kpis:
    with col:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-label'>{lbl}</div>
          <div class='kpi-value'>{val}</div>
          <div class='kpi-sub'>{unit}</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════
t1, t2, t3, t4 = st.tabs([
    "📈 Hourly Forecast",
    "📅 Daily Peak Chart",
    "📊 Monthly Summary",
    "🗃 Data & Download",
])

# ─────────────────────────────────────────────
#  TAB 1 — Hourly Forecast
# ─────────────────────────────────────────────
with t1:
    st.markdown("<div class='sec'>Hourly Load Forecast — Apr to Jun 2026</div>",
                unsafe_allow_html=True)

    month_names = {4:"April 2026", 5:"May 2026", 6:"June 2026"}
    all_months  = sorted(hourly['Datetime'].dt.month.unique())
    sel = st.multiselect(
        "Filter by month",
        options=all_months, default=all_months,
        format_func=lambda x: month_names.get(x, str(x))
    )
    if not sel:
        sel = all_months

    filt = hourly[hourly['Datetime'].dt.month.isin(sel)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.concat([filt['Datetime'], filt['Datetime'][::-1]]),
        y=pd.concat([filt['Upper_90pct'], filt['Lower_90pct'][::-1]]),
        fill='toself', fillcolor='rgba(45,125,210,0.08)',
        line=dict(color='rgba(0,0,0,0)'), name='90% CI', showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([filt['Datetime'], filt['Datetime'][::-1]]),
        y=pd.concat([filt['Upper_50pct'], filt['Lower_50pct'][::-1]]),
        fill='toself', fillcolor='rgba(45,125,210,0.16)',
        line=dict(color='rgba(0,0,0,0)'), name='50% CI', showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=filt['Datetime'], y=filt['Forecast_MW'],
        name='Forecast MW', line=dict(color=C2, width=1.5),
    ))
    for vl in ['2026-04-01','2026-05-01','2026-06-01','2026-07-01']:
        fig.add_vline(x=vl, line_dash="dot", line_color="#2a4a6a", opacity=0.6)

    fig.update_layout(**BL, title="Hourly MW Forecast with Confidence Bands",
                      xaxis_title="Date", yaxis_title="Load (MW)", height=440)
    st.plotly_chart(fig, use_container_width=True)

    sa, sb, sc, sd = st.columns(4)
    sa.metric("Average", f"{filt['Forecast_MW'].mean():,.0f} MW")
    sb.metric("Peak",    f"{filt['Forecast_MW'].max():,.0f} MW")
    sc.metric("Minimum", f"{filt['Forecast_MW'].min():,.0f} MW")
    sd.metric("Std Dev", f"{filt['Forecast_MW'].std():,.0f} MW")

# ─────────────────────────────────────────────
#  TAB 2 — Daily Peak
# ─────────────────────────────────────────────
with t2:
    st.markdown("<div class='sec'>Daily Peak / Average / Minimum</div>",
                unsafe_allow_html=True)

    col_map  = {4: C2, 5: C4, 6: '#c0392b'}
    bar_cols = [col_map.get(d.month, C2) for d in daily['date']]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=daily['date'], y=daily['Peak_MW'],
        name='Daily Peak MW', marker_color=bar_cols, opacity=0.85,
    ))
    fig2.add_trace(go.Scatter(
        x=daily['date'], y=daily['Avg_MW'],
        name='Daily Avg MW', line=dict(color=C1, width=2),
        mode='lines+markers', marker=dict(size=4),
    ))
    fig2.add_trace(go.Scatter(
        x=daily['date'], y=daily['Min_MW'],
        name='Daily Min MW', line=dict(color=C3, width=1.5, dash='dash'),
    ))
    fig2.update_layout(**BL,
        title="Daily Peak / Avg / Min Load — Apr to Jun 2026",
        xaxis_title="Date", yaxis_title="Load (MW)", height=420,
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Heatmap
    st.markdown("<div class='sec'>Hourly Load Heatmap</div>", unsafe_allow_html=True)
    hm = hourly.copy()
    hm['hour']     = hm['Datetime'].dt.hour
    hm['date_str'] = hm['Datetime'].dt.strftime('%d %b')
    pivot = hm.pivot_table(index='hour', columns='date_str',
                            values='Forecast_MW', aggfunc='mean')
    fig_h = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale='RdYlBu_r',
        colorbar=dict(title='MW', tickfont=dict(color=TX)),
    ))
    fig_h.update_layout(**BL, title="Load Heatmap (Hour of Day vs Date)",
                         xaxis_title="Date", yaxis_title="Hour of Day", height=380)
    st.plotly_chart(fig_h, use_container_width=True)

# ─────────────────────────────────────────────
#  TAB 3 — Monthly Summary
# ─────────────────────────────────────────────
with t3:
    st.markdown("<div class='sec'>Monthly Load Summary</div>", unsafe_allow_html=True)

    hourly['month_label'] = hourly['Datetime'].dt.to_period('M').astype(str)
    monthly = hourly.groupby('month_label').agg(
        avg_mw=('Forecast_MW','mean'),
        peak_mw=('Forecast_MW','max'),
        min_mw=('Forecast_MW','min'),
    ).reset_index()

    fig3 = go.Figure()
    for val_col, name, color in [
        ('min_mw',  'Min MW',  C3),
        ('avg_mw',  'Avg MW',  C1),
        ('peak_mw', 'Peak MW', C2),
    ]:
        fig3.add_trace(go.Bar(
            name=name, x=monthly['month_label'], y=monthly[val_col],
            marker_color=color, opacity=0.85,
            text=monthly[val_col].round(0).astype(int),
            textposition='outside',
            textfont=dict(color=TX, size=11),
        ))
    fig3.update_layout(**BL, barmode='group',
        title="Monthly Min / Average / Peak Load (MW)",
        yaxis_title="Load (MW)", height=380,
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Accuracy metrics
    st.markdown("<div class='sec'>Model Accuracy Metrics</div>", unsafe_allow_html=True)
    ma, mb, mc, md = st.columns(4)
    ma.metric("MAE",  f"{meta.get('model_mae','—')} MW",  help="Mean Absolute Error")
    mb.metric("RMSE", f"{meta.get('model_rmse','—')} MW", help="Root Mean Square Error")
    mc.metric("MAPE", f"{meta.get('model_mape','—')} %",  help="Mean Absolute Percentage Error")
    md.metric("R²",   f"{meta.get('model_r2','—')}",      help="1.0 = perfect fit")

    st.markdown(f"""
    <div class='info-box'>
      <b>Model :</b> Gradient Boosting Regressor &nbsp;|&nbsp;
      <b>Training :</b> Jan 2020 – Mar 2026 (54,768 hourly records) &nbsp;|&nbsp;
      <b>Features :</b> time, cyclical encoding, lag-24h, lag-168h,
      rolling averages, temperature, humidity, rain, wind, radiation, cloud cover
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TAB 4 — Data & Download
# ─────────────────────────────────────────────
with t4:
    st.markdown("<div class='sec'>Hourly Forecast Data</div>", unsafe_allow_html=True)

    da, db = st.columns(2)
    with da:
        mf = st.selectbox("Filter month",
            options=[0]+list(all_months),
            format_func=lambda x: "All months" if x==0 else month_names.get(x, str(x))
        )
    with db:
        sf = st.selectbox("Sort by", [
            "Datetime",
            "Forecast_MW — high to low",
            "Forecast_MW — low to high",
        ])

    show = hourly.copy()
    if mf != 0:
        show = show[show['Datetime'].dt.month == mf]
    if sf == "Forecast_MW — high to low":
        show = show.sort_values('Forecast_MW', ascending=False)
    elif sf == "Forecast_MW — low to high":
        show = show.sort_values('Forecast_MW', ascending=True)

    disp = show[['Datetime','Forecast_MW','Lower_90pct',
                 'Lower_50pct','Upper_50pct','Upper_90pct']].copy()
    disp['Datetime'] = disp['Datetime'].dt.strftime('%Y-%m-%d %H:%M')
    disp = disp.round(1)
    st.dataframe(disp, use_container_width=True, height=340)

    st.markdown("<div class='sec'>Download</div>", unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "⬇️  Hourly Forecast CSV",
            data=hourly.to_csv(index=False),
            file_name="TN_Forecast_Hourly_Apr_Jun_2026.csv",
            mime="text/csv", use_container_width=True,
        )
    with dl2:
        st.download_button(
            "⬇️  Daily Summary CSV",
            data=daily.to_csv(index=False),
            file_name="TN_Forecast_Daily_Apr_Jun_2026.csv",
            mime="text/csv", use_container_width=True,
        )

    st.markdown("<div class='sec'>GitHub Source</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='info-box'>
      <b>Repo   :</b> {GITHUB_REPO}<br>
      <b>Branch :</b> {GITHUB_BRANCH}<br>
      <b>Files  :</b> data/TN_Forecast_Hourly.csv &nbsp;·&nbsp;
                      data/TN_Forecast_Daily.csv &nbsp;·&nbsp;
                      data/forecast_meta.json<br>
      <b>Refresh:</b> Every 60 seconds automatically
    </div>""", unsafe_allow_html=True)

# Footer
st.markdown("""
<hr style='border-color:#1a3a5c;margin-top:40px;'>
<p style='text-align:center;color:#2a4a6a;font-size:13px;'>
  TN Load Forecasting · Gradient Boosting Model · GitHub → Streamlit Pipeline
</p>""", unsafe_allow_html=True)
