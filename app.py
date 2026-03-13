# app.py – Swing Watchlist (minimal, sauber, ohne pandas_ta)

import streamlit as st
from supabase import create_client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview

st.set_page_config(page_title="Swing Watchlist", layout="wide")

st.title("Swing Watchlist – Testversion März 2026")

# Supabase nur zum Testen
supabase = create_client(st.secrets.supabase.url, st.secrets.supabase.key)
st.success("Supabase-Client initialisiert")

# ────────────────────────────────────────────────
# Daten laden – sehr einfach gehalten
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_data(max_tickers=50):
    foverview = Overview()
    df = foverview.screener_view(
        filters_dict={
            'Average Volume': 'Over 1M',
            'Performance': 'Week'
        }
    )
    tickers = df['Ticker'].head(max_tickers).tolist()

    results = []
    progress = st.progress(0)

    for i, ticker in enumerate(tickers):
        try:
            hist = yf.Ticker(ticker).history(period="1y")
            if len(hist) < 150:
                continue

            close = hist['Close'][-1]
            sma50  = hist['Close'].rolling(50).mean()[-1]
            sma150 = hist['Close'].rolling(150).mean()[-1]

            # ganz einfache ATR-Approximation
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

        progress.progress((i+1) / len(tickers))

    return pd.DataFrame(results)

# ────────────────────────────────────────────────
# Button & Ausgabe
# ────────────────────────────────────────────────

if st.button("Daten laden (50 Ticker)", type="primary"):
    with st.spinner("Lade Daten …"):
        df = load_data()

    if df.empty:
        st.warning("Keine Daten erhalten")
    else:
        st.success(f"{len(df)} Aktien geladen")

        st.dataframe(
            df.sort_values('Ext', ascending=False),
            use_container_width=True,
            hide_index=True
        )

st.caption("Minimalversion – ohne Industry-Gruppierung & Farben – nur um Syntax & Laufzeit zu prüfen")
