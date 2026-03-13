# app.py – Supabase Insert + Select Test (Version 2)

import streamlit as st
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="Swing Watchlist – Supabase Test v2", layout="wide")

st.title("Swing Watchlist – Supabase Test Phase 2")
st.markdown("Ziel: Schreiben und Lesen in `watchlists` testen")

# ────────────────────────────────────────────────
# Supabase Client (cached)
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
        st.error(f"Client-Initialisierung fehlgeschlagen:\n{e}")
        return None

supabase = get_supabase_client()

if supabase:
    st.success("Supabase-Client bereit ✓")
else:
    st.stop()

# ────────────────────────────────────────────────
# Test-Insert
# ────────────────────────────────────────────────

st.subheader("A – Neue Test-Watchlist schreiben")

watchlist_name = st.text_input("Name der Watchlist", "Testliste " + datetime.now().strftime("%Y-%m-%d %H:%M"))

if st.button("→ Watchlist speichern"):
    if not watchlist_name.strip():
        st.warning("Bitte einen Namen eingeben")
    else:
        try:
            data = {
                "name": watchlist_name,
                "tickers": ["AAPL", "NVDA", "TSLA", "TEST" + str(datetime.now().second)],
                "created_at": datetime.utcnow().isoformat()
            }
            response = supabase.table("watchlists").insert(data).execute()

            if response.data:
                st.success(f"Gespeichert! Neue ID: {response.data[0]['id']}")
                st.json(response.data[0])
            else:
                st.warning("Insert lief, aber keine Daten zurückbekommen")

        except Exception as e:
            st.error(f"Insert Fehler:\n{str(e)}")

# ────────────────────────────────────────────────
# Alle Einträge laden + anzeigen
# ────────────────────────────────────────────────

st.subheader("B – Alle gespeicherten Watchlists anzeigen")

if st.button("→ Alle Einträge laden"):
    try:
        response = supabase.table("watchlists").select("*").execute()

        if response.data:
            st.success(f"{len(response.data)} Einträge gefunden")
            st.dataframe(response.data)
        else:
            st.info("Noch keine Einträge in der Tabelle")

    except Exception as e:
        st.error(f"Select Fehler:\n{str(e)}")

st.markdown("---")
st.caption("Nächster Schritt (nach erfolgreichem Test): finvizfinance + yfinance + erste Industry-Gruppierung")
