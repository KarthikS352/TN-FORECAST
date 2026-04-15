# ================================================================
# FIXED VERSION — STRICT DATA CONTROL (NO COLAB = NO DATA)
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hashlib, json, os, calendar, requests
from datetime import datetime
from io import StringIO

st.set_page_config(page_title="TN Load Forecasting", page_icon="⚡", layout="wide")

# ================================================================
# CONFIG
# ================================================================
GITHUB_USER   = "KarthikS352"
GITHUB_REPO   = "TN-LOAD-FORECAST"
GITHUB_BRANCH = "main"
GITHUB_RAW    = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/results"

# ================================================================
# 🔥 STRICT DATA LOADER (MAIN FIX)
# ================================================================
@st.cache_data(ttl=60)
def fetch_github(filename):
    url = f"{GITHUB_RAW}/{filename}"
    try:
        r = requests.get(url, timeout=10)
        return r.text if r.status_code == 200 else None
    except Exception:
        return None


def load_results():
    """
    STRICT RULE:
    - Only show data if generated recently
    - Otherwise return NONE
    """
    data = fetch_github("rolling_results.csv")

    if not data:
        return None, None

    try:
        df = pd.read_csv(StringIO(data))

        # ❌ No timestamp = reject
        if 'generated_at' not in df.columns:
            return None, None

        latest_time = pd.to_datetime(df['generated_at'].iloc[0])
        now = datetime.now()

        # ❌ Older than 10 minutes = reject
        if (now - latest_time).total_seconds() > 600:
            return None, None

        return df, "github"

    except Exception:
        return None, None

# ================================================================
# DASHBOARD
# ================================================================
def show_dashboard():
    st.title("⚡ TN Load Forecasting Dashboard")

    df, source = load_results()

    # 🚨 MAIN CONTROL
    if df is None or len(df) == 0:
        st.warning("🚫 No Active Data\n\nRun Colab to generate fresh results.")
        return

    st.success("✅ Live Data (Fresh Run Detected)")

    # Example KPI
    st.metric("Total Days", len(df))

    # Simple chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['day'],
        y=df['predicted_avg'],
        mode='lines+markers',
        name='Predicted Avg'
    ))

    fig.update_layout(title="Daily Forecast", xaxis_title="Day", yaxis_title="Load")

    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.dataframe(df.head(50))

# ================================================================
# MAIN
# ================================================================
show_dashboard()

# ================================================================
# 🔥 REQUIRED CHANGE IN COLAB CODE
# ================================================================
# ADD THIS BEFORE SAVING CSV:
#
# from datetime import datetime
# df_results['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# df_results.to_csv('results/rolling_results.csv', index=False)
# ================================================================
