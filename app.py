# app.py – Swing Watchlist – finviz Filter angepasst (März 2026)

import streamlit as st
from supabase import create_client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview

st.set_page_config(page_title="Swing Watchlist – Test", layout="wide")

st.title("Swing Watchlist – Debug & Testversion")
st.markdown("Aktuell nur minimale Filter, um finvizfinance-Fehler zu umgehen")

# Supabase Test
try:
    supabase = create_client(st.secrets.supabase.url, st.secrets.supabase.key)
    st.success("Supabase OK")
except Exception as e:
    st.error(f"Supabase Fehler: {e}")
    st.stop()

# ────────────────────────────────────────────────
# Daten laden – mit defensiven Filtern
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_data(max_tickers=60):
    foverview = Overview()

    # Sehr konservative Filter – nur solche, die aktuell fast immer gehen
    safe_filters = {
        'Average Volume': 'Over 1M',          # meist noch stabil
        'Market Cap.': 'Mid ($2 - $10B)',     # oft OK
        'Optionable': 'Yes',                  # hilft, liquide Namen zu bekommen
        # 'Perf Week': 'Positive'             # oft problematisch → auskommentiert
    }

    try:
        foverview.set_filter(filters_dict=safe_filters)
        df_fin = foverview.screener_view()
    except Exception as e:
        st.warning(f"finviz Filter-Fehler: {e}")
        st.info("Versuche ohne Filter...")
        df_fin = foverview.screener_view()  # fallback ohne Filter

    if df_fin.empty:
        st.error("Finviz hat keine Daten zurückgegeben")
        return pd.DataFrame()

    # Nach Performance sortieren (wenn Spalte existiert)
    if 'Perf Week' in df_fin.columns:
        df_fin = df_fin.sort_values('Perf Week', ascending=False)

    tickers = df_fin['Ticker'].head(max_tickers).tolist()

    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"{ticker} ({i+1}/{len(tickers)})")
        try:
            hist = yf.Ticker(ticker).history(period="1y")
            if len(hist) < 150:
                continue

            close = hist['Close'][-1]
            sma50 = hist['Close'].rolling(50).mean()[-1]
            sma150 = hist['Close'].rolling(150).mean()[-1]

            # ATR manuell
            tr = pd.concat([
                hist['High'] - hist['Low'],
                abs(hist['High'] - hist['Close'].shift()),
                abs(hist['Low'] - hist['Close'].shift())
            ], axis=1).max(axis=1)

            atr = tr.rolling(14).mean()[-1] if len(tr) >= 14 else 0

            atr_pct = round(atr / close * 100, 1) if close > 0 else 0
            ext = round((close - sma50) / atr, 1) if atr > 0 else 0

            stage = "2" if close > sma50 > sma150 else "1/3/4"

            results.append({
                'Ticker': ticker,
                'Close': round(close, 2),
                'Stage': stage,
                'ATR%': atr_pct,
                'Ext': ext
            })
        except:
            pass

        progress.progress((i + 1) / len(tickers))

    status.text("Fertig")
    progress.empty()

    return pd.DataFrame(results)

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────

if st.button("Daten laden (max. 60 Ticker)", type="primary"):
    df = load_data
