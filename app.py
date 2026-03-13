# app.py – Swing Watchlist mit Finviz + yfinance (ATR manuell)

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview
from datetime import datetime

st.set_page_config(page_title="Swing Watchlist Pro", layout="wide")

st.title("Swing Watchlist – Stage 2 + ATR + Extension")
st.caption("ATR manuell berechnet – kompatibel mit Python 3.14 / Streamlit Cloud")

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
        st.error(f"Supabase-Client Initialisierungsfehler:\n{e}")
        return None

supabase = get_supabase_client()

if supabase:
    st.success("Supabase-Verbindung OK ✓")
else:
    st.stop()

# ────────────────────────────────────────────────
# Watchlist-Daten laden
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800)  # 30 Minuten
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
        # ←─── HIER WAR DER FEHLER ────
        status.text(f"Daten für {ticker} ({i+1}/{len(tickers)})")

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y", auto_adjust=True)
            if len(hist) < 160:
                continue

            close = hist['Close'].iloc[-1]
            sma50  = hist['Close'].rolling(50).mean().iloc[-1]
            sma150 = hist['Close'].rolling(150).mean().iloc[-1]

            # Manuelle True Range + ATR(14)
            tr = pd.concat([
                hist['High'] - hist['Low'],
                abs(hist['High'] - hist['Close'].shift()),
                abs(hist['Low'] - hist['Close'].shift())
            ], axis=1).max(axis=1)

            atr = tr.rolling(window=14).mean().iloc[-1] if len(tr) >= 14 else 0

            atr_pct   = round(atr / close * 100, 1) if close > 0 and atr > 0 else 0
            extension = round((close - sma50) / atr, 1) if atr > 0 else 0

            stage = "2 📈" if (close > sma50 > sma150) else "1/3/4"

            high52 = hist['Close'].max()
            rr = round(((high52 * 1.15 - close) / (close * 0.88 - close)), 1) \
                if close > 0 and (close * 0.88 - close) != 0 else 0

            industry = df_fin[df_fin['Ticker'] == ticker]['Industry'].values[0] \
                if 'Industry' in df_fin.columns and len(df_fin[df_fin['Ticker'] == ticker]) > 0 else "—"

            data.append({
                'Ticker': ticker,
                'Industry': industry,
                'Stage': stage,
                'ATR%': atr_pct,
                'Ext': extension,
                'R:R': rr,
                'Close': round(close, 2)
            })

        except Exception:
            pass

        progress.progress((i + 1) / len(tickers))

    status.text("Daten geladen ✓")
    progress.empty()

    return pd.DataFrame(data)

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────

if st.button("→ Watchlist laden (Finviz Top-Performer)", type="primary"):
    with st.spinner("Lade und analysiere Aktien …"):
        df = get_watchlist_data(max_tickers=80)

    if df.empty:
        st.warning("Keine Daten erhalten – später nochmal versuchen")
    else:
        st.success(f"{len(df)} Aktien analysiert")

        grouped = df.groupby('Industry', sort=False)

        for industry, group in grouped:
            count = len(group)
            with st.expander(f"**{industry}** ({count})", expanded=(count >= 4)):
                group_sorted = group.sort_values('R:R', ascending=False).reset_index(drop=True)

                def color_ext(v):
                    if pd.isna(v): return ''
                    if v > 7:   return 'background-color: #ffcccc; color: #c00000'
                    if v > 5:   return 'background-color: #ffccff; color: #800080'
                    return ''

                styled = group_sorted.style\
                    .applymap(color_ext, subset=['Ext'])\
                    .format(precision=1, na_rep="—")\
                    .set_properties(**{'text-align': 'right'}, subset=['ATR%', 'Ext', 'R:R', 'Close'])

                st.dataframe(styled, use_container_width=True, hide_index=True)

# Gespeicherte Listen (optional)
st.subheader("Gespeicherte Watchlists")
if st.button("→ Listen laden"):
    res = supabase.table("watchlists").select("*").execute()
    if res.data:
        st.dataframe(res.data)
    else:
        st.info("Noch nichts gespeichert")

st.caption("Fe
