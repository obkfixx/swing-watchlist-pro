# app.py – Erste Watchlist mit Finviz + yfinance (Version 3)

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from finvizfinance.screener.overview import Overview
from datetime import datetime

st.set_page_config(page_title="Swing Watchlist Pro – v3", layout="wide")

st.title("Swing Watchlist – Erste echte Daten")

# ────────────────────────────────────────────────
# Supabase Client
# ────────────────────────────────────────────────

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = get_supabase_client()

# ────────────────────────────────────────────────
# Finviz + yfinance Daten holen (cached für Performance)
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600)  # 1 Stunde Cache
def get_watchlist_data(max_tickers=60):
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
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(tickers):
        status_text.text(f"Hole Daten für {ticker} ({i+1}/{len(tickers)})")
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if len(hist) < 150:
                continue

            close = hist['Close'][-1]
            sma50 = hist['Close'].rolling(50).mean()[-1]
            sma150 = hist['Close'].rolling(150).mean()[-1]
            atr = ta.atr(high=hist['High'], low=hist['Low'], close=hist['Close'], length=14)[-1]

            atr_pct = round(atr / close * 100, 1) if close > 0 else 0
            extension = round((close - sma50) / atr, 1) if atr > 0 else 0

            stage = "2 📈" if (close > sma50 > sma150) else "1/3/4"

            # Einfaches proj. R:R (Ziel ~15% über 52w-High, Stop ~12% unter Close)
            high52 = hist['Close'].max()
            rr = round(((high52 * 1.15 - close) / (close * 0.88 - close)), 1) if close > 0 else 0

            industry = df_fin[df_fin['Ticker'] == ticker]['Industry'].values[0] if 'Industry' in df_fin.columns else "N/A"

            data.append({
                'Ticker': ticker,
                'Industry': industry,
                'Stage': stage,
                'ATR%': atr_pct,
                'Ext': extension,
                'R:R': rr,
                'Close': round(close, 2)
            })
        except:
            pass

        progress_bar.progress((i + 1) / len(tickers))

    status_text.text("Daten geladen ✓")
    progress_bar.empty()

    return pd.DataFrame(data)

# ────────────────────────────────────────────────
# Haupt-UI
# ────────────────────────────────────────────────

if st.button("→ Frische Watchlist laden (Finviz + Stage + ATR)"):
    with st.spinner("Lade Top-Aktien und berechne Metriken... (kann 1–3 Min dauern)"):
        df = get_watchlist_data(max_tickers=80)  # mehr = länger, aber umfassender

    if not df.empty:
        st.success(f"{len(df)} Aktien analysiert")

        # Group by Industry
        grouped = df.groupby('Industry')

        for industry, group in grouped:
            with st.expander(f"**{industry}** ({len(group)} Aktien)"):
                group_sorted = group.sort_values('R:R', ascending=False)

                # Farb-Highlighting für Extension
                def highlight_ext(val):
                    if val > 7: return 'background-color: #ffcccc; color: darkred'
                    if val > 5: return 'background-color: #ffccff; color: purple'
                    return ''

                styled = group_sorted.style.applymap(highlight_ext, subset=['Ext']) \
                                          .format(precision=1, na_rep="-")

                st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.warning("Keine Daten geladen – probiere später nochmal")

# ────────────────────────────────────────────────
# Watchlist-Speicher (optional erweitern)
# ────────────────────────────────────────────────

st.subheader("Gespeicherte Listen (Test)")
if st.button("→ Meine Listen laden"):
    res = supabase.table("watchlists").select("*").execute()
    if res.data:
        st.dataframe(res.data)
    else:
        st.info("Noch leer")
