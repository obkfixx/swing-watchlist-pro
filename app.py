# app.py – Swing Watchlist mit Finviz + yfinance (ATR manuell, saubere Syntax)

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview
from datetime import datetime

st.set_page_config(page_title="Swing Watchlist Pro", layout="wide")

st.title("Swing Watchlist – Stage 2 + ATR + Extension")
st.caption("Manuelle ATR-Berechnung – kompatibel mit Python 3.14 / Streamlit Cloud")

# ────────────────────────────────────────────────
# Supabase Client
# ────────────────────────────────────────────────

@st.cache_resource
def get_supabase_client():
    try:
        client = create_client(
            st.secrets["supabase"]["url"],
            st.secrets["supabase"]["key"]
        )
        return client
    except Exception as e:
        st.error(f"Supabase-Client konnte nicht initialisiert werden:\n{e}")
        return None

supabase = get_supabase_client()

if supabase:
    st.success("Supabase-Verbindung steht ✓")
else:
    st.stop()

# ────────────────────────────────────────────────
# Daten laden und berechnen
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800)  # 30 Minuten Cache
def get_watchlist_data(max_tickers=80):
    foverview = Overview()
    df_fin = foverview.screener_view(
        filters_dict={
            'Average Volume': 'Over 1M',
            'Market Cap.': 'Mid ($2 - $10B)+',
            'Performance': 'Week'
        }
    )

    tickers = df_fin['Ticker'].head(max_tickers).tolist()

    data = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"Daten für {ticker} ({i+1}/{len(tickers)})")

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y", auto_adjust=True)
            if len(hist) < 160:
                continue

            close = hist['Close'].iloc[-1]
            sma50 = hist['Close'].rolling(50).mean().iloc[-1]
            sma150 =
