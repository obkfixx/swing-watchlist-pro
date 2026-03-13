# app.py – Swing Watchlist Minimalversion (März 2026)

import streamlit as st
from supabase import create_client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview

st.set_page_config(page_title="Swing Watchlist – Minimal", layout="wide")

st.title("Swing Watchlist – Testversion")
st.markdown("Ziel: erstmal nur sehen, ob die App ohne Syntax- und Import-Fehler läuft")

# ────────────────────────────────────────────────
# Supabase – nur zum Testen der Secrets
# ────────────────────────────────────────────────

try:
    supabase = create_client(st.secrets.supabase.url, st.secrets.supabase.key)
    st.success("Supabase-Client erfolgreich initialisiert")
except Exception as e:
    st.error(f"Supabase-Verbindungsfehler:\n{e}")
    st.stop()

# ────────────────────────────────────────────────
# Finviz + yfinance – mit korrekter Filter-Methode
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_data(max_tickers=40):
    foverview = Overview()

    # Filter setzen – so wie es finvizfinance aktuell erwartet
    filters = {
        'Average Volume': 'Over 1M',
        'Performance': 'Week'
    }
    foverview.set_filter(filters_dict=filters)

    # Screener aufrufen – ohne zusätzliche Argumente
    df_fin = foverview.screener_view()

    if df_fin.empty:
        st.warning("Finviz hat keine Ergebnisse zurückgegeben")
        return pd.DataFrame()

    tickers = df_fin['Ticker'].head(max_tickers).tolist()

    results = []
    progress = st.progress(0)
    status_text = st.empty()

    for idx, ticker in enumerate(tickers):
        status_text.text(f"Hole Daten: {ticker} ({idx+1}/{len(tickers)})")

        try:
            hist = yf.Ticker(ticker).history(period="1y")
            if len(hist) < 150:
                continue

            close = hist['Close'][-1]
            sma50  = hist['Close'].rolling(50).mean()[-1]
            sma150 = hist['Close'].rolling(150).mean()[-1]

            # Sehr einfache ATR-Approximation
            tr = pd.concat([
                hist['High'] - hist['Low'],
                abs(hist['High'] - hist['Close'].shift()),
                abs(hist['Low'] - hist['Close'].shift())
            ], axis=1).max(axis=1)

            atr = tr.rolling(14).mean()[-1] if len(tr) >= 14 else 0

            atr_pct = round(atr / close * 100, 1) if close > 0 else 0
            extension = round((close - sma50) / atr, 1) if atr > 0 else 0

            stage = "2" if close > sma50 > sma150 else "1/3/4"

            results.append({
                'Ticker': ticker,
                'Close': round(close, 2),
                'Stage': stage,
                'ATR%': atr_pct,
                'Ext': extension
            })

        except Exception:
            pass  # Ein Ticker fehlschlägt → weiter

        progress.progress((idx + 1) / len(tickers))

    status_text.text("Fertig")
    progress.empty()

    return pd.DataFrame(results)

# ────────────────────────────────────────────────
# Haupt-Button
# ────────────────────────────────────────────────

if st.button("Daten laden (max. 40 Ticker)", type="primary"):
    df = load_data()

    if df.empty:
        st.warning("Keine verwertbaren Daten erhalten")
    else:
        st.success(f"{len(df)} Aktien geladen")
        st.dataframe(
            df.sort_values('Ext', ascending=False),
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")
st.caption("Minimalversion – ohne Gruppierung, Farben, Reward:Risk – nur zum Testen der Basics")
