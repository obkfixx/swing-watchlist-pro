# app.py – Swing Watchlist – Debug & Minimal – alle try/except vollständig (13. März 2026)

import streamlit as st
from supabase import create_client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview

st.set_page_config(page_title="Swing Watchlist Debug", layout="wide")

st.title("Swing Watchlist – Debug-Modus")
st.markdown("Ziel: Schritt-für-Schritt sehen, wo der Code hängen bleibt")

# Supabase prüfen
st.subheader("1. Supabase-Verbindung")
try:
    supabase = create_client(st.secrets.supabase.url, st.secrets.supabase.key)
    st.success("Supabase-Verbindung OK")
except Exception as e:
    st.error(f"Supabase-Fehler: {str(e)}")
    st.stop()

# ────────────────────────────────────────────────
# Daten laden – ohne Cache, viele Statusmeldungen
# ────────────────────────────────────────────────

def load_data(max_tickers=20):
    st.write("load_data() wurde aufgerufen")

    results = []
    progress = st.progress(0)

    try:
        st.write("Versuche Finviz-Screener ohne Filter (sicherste Variante)")
        foverview = Overview()
        df_fin = foverview.screener_view()

        st.write(f"Finviz hat {len(df_fin)} Zeilen zurückgegeben")

        if df_fin.empty:
            st.warning("Finviz-Tabelle ist leer – Abbruch")
            return pd.DataFrame()

        tickers = df_fin['Ticker'].head(max_tickers).tolist()
        st.write(f"{len(tickers)} Ticker ausgewählt")

        for i, ticker in enumerate(tickers):
            st.write(f"Verarbeite {ticker} ({i+1}/{len(tickers)})")

            try:
                hist = yf.Ticker(ticker).history(period="1y")
                if len(hist) < 150:
                    st.write(f"  {ticker}: zu wenige Daten → überspringen")
                    continue

                close = hist['Close'][-1]
                sma50 = hist['Close'].rolling(50).mean()[-1]
                sma150 = hist['Close'].rolling(150).mean()[-1]

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

                st.write(f"  {ticker} OK")

            except Exception as inner_e:
                st.write(f"  Fehler bei {ticker}: {str(inner_e)}")

            progress.progress((i + 1) / len(tickers))

        progress.empty()
        st.write(f"load_data() fertig – {len(results)} Ergebnisse")
        return pd.Data
