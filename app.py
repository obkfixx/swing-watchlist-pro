# app.py – Swing Watchlist – Debug & Minimal (März 2026)

import streamlit as st
from supabase import create_client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview
import traceback

st.set_page_config(page_title="Swing Watchlist Debug", layout="wide")

st.title("Swing Watchlist – Debug-Modus")
st.markdown("**Ziel:** Sehen, ob der Code überhaupt läuft und wo es hängen bleibt")

# ────────────────────────────────────────────────
# Supabase – nur Test
# ────────────────────────────────────────────────

st.subheader("1. Supabase-Verbindung")
try:
    supabase = create_client(st.secrets.supabase.url, st.secrets.supabase.key)
    st.success("Supabase-Client OK")
except Exception as e:
    st.error(f"Supabase-Fehler: {str(e)}")
    st.stop()

# ────────────────────────────────────────────────
# Daten laden – mit maximalem Debugging
# ────────────────────────────────────────────────

def load_data(max_tickers=30):  # ← Cache absichtlich entfernt zum Debug
    st.write("→ load_data() gestartet")

    try:
        foverview = Overview()
        st.write("Finviz Overview-Objekt erstellt")

        # Sehr konservative Filter
        filters = {
            'Average Volume': 'Over 500K',   # etwas niedriger → mehr Ergebnisse
            'Market Cap.': 'Mid ($2 - $10B)',
        }
        st.write(f"Filter setzen: {filters}")

        foverview.set_filter(filters_dict=filters)
        st.write("Filter erfolgreich gesetzt")

        df_fin = foverview.screener_view()
        st.write(f"Finviz-Screener zurückgegeben: {len(df_fin)} Zeilen")

        if df_fin.empty:
            st.warning("Finviz hat leere Tabelle zurückgegeben → Fallback ohne Filter")
            df_fin = foverview.screener_view()  # ohne Filter

        if df_fin.empty:
            st.error("Auch ohne Filter leer – Finviz-Problem?")
            return pd.DataFrame()

        tickers = df_fin['Ticker'].head(max_tickers).tolist()
        st.write(f"{len(tickers)} Ticker ausgewählt")

        results = []
        progress = st.progress(0)

        for i, ticker in enumerate(tickers):
            st.write(f"  Verarbeite {ticker} ({i+1}/{len(tickers)})")
            try:
                hist = yf.Ticker(ticker).history(period="1y")
                if len(hist) < 150:
                    st.write(f"    {ticker}: zu wenig Daten → überspringen")
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

                st.write(f"    {ticker} erfolgreich verarbeitet")

            except Exception as e:
                st.write(f"    Fehler bei {ticker}: {str(e)}")

            progress.progress((i + 1) / len(tickers))

        progress.empty()
        st.write("→ load_data() beendet")
        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Schwerer Fehler in load_data(): {str(e)}")
        st.code(traceback.format_exc())
        return pd.DataFrame()

# ────────────────────────────────────────────────
# Haupt-Button mit vollem Try-Except
# ────────────────────────────────────────────────

st.subheader("2. Daten laden")

if st.button("Daten laden (max. 30 Ticker)", type="primary"):
    st.write("Button wurde gek
