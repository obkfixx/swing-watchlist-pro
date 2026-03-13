# app.py – Swing Watchlist – Debug-Version mit vollständigen Strings (13. März 2026)

import streamlit as st
from supabase import create_client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview
import traceback

st.set_page_config(page_title="Swing Watchlist Debug", layout="wide")

st.title("Swing Watchlist – Debug-Modus")
st.markdown("Ziel: Schritt-für-Schritt sehen, wo der Code hängen bleibt")

# Supabase-Verbindung prüfen
st.subheader("Supabase-Verbindung")
try:
    supabase = create_client(st.secrets.supabase.url, st.secrets.supabase.key)
    st.success("Supabase-Client erfolgreich erstellt")
except Exception as e:
    st.error(f"Supabase-Verbindungsfehler: {str(e)}")
    st.stop()

# ────────────────────────────────────────────────
# Daten-Ladefunktion (ohne Cache zum Debuggen)
# ────────────────────────────────────────────────

def load_data(max_tickers=25):
    st.write("Funktion load_data() wurde gestartet")

    try:
        foverview = Overview()
        st.write("Finviz Overview-Objekt erstellt")

        # Sehr minimale Filter – nur das, was meistens funktioniert
        filters = {
            'Average Volume': 'Over 500K',
        }
        st.write("Filter, die gesetzt werden sollen:", filters)

        foverview.set_filter(filters_dict=filters)
        st.write("Filter wurden gesetzt")

        df_fin = foverview.screener_view()
        st.write("screener_view() aufgerufen – Ergebniszeilen:", len(df_fin))

        if df_fin.empty:
            st.warning("Finviz-Tabelle leer → versuche ohne Filter")
            df_fin = foverview.screener_view()

        tickers = df_fin['Ticker'].head(max_tickers).tolist()
        st.write("Anzahl ausgewählter Ticker:", len(tickers))

        results = []
        progress = st.progress(0)

        for i, ticker in enumerate(tickers):
            st.write(f"→ Verarbeite Ticker {i+1}/{len(tickers)}: {ticker}")

            try:
                hist = yf.Ticker(ticker).history(period="1y")
                if len(hist) < 150:
                    st.write(f"  → Zu wenige Daten für {ticker}")
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

                st.write(f"  → {ticker} erfolgreich verarbeitet")

            except Exception as ex:
                st.write(f"  → Fehler bei {ticker}: {str(ex)}")

            progress.progress((i + 1) / len(tickers))

        progress.empty()
        st.write("load_data() abgeschlossen – Ergebnisse:", len(results))
        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Schwerer Fehler in load_data(): {str(e)}")
        st.code(traceback.format_exc())
        return pd.DataFrame()

# ────────────────────────────────────────────────
# Button mit maximaler Sichtbarkeit
# ────────────────────────────────────────────────

st.subheader("Daten laden testen")

if st.button("Daten laden (max. 25 Ticker)", type="primary"):
    st.markdown("**Button wurde gedrückt – Verarbeitung startet**")
    st.write("Aktueller Zeitpunkt:", pd.Timestamp.now())

    try:
        df = load_data()
        st.write("Funktion load_data() ist zurückgekehrt")

        if df.empty:
            st.warning
