# app.py – Supabase Verbindungstest (Cloud-only)

import streamlit as st
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="Swing Watchlist – Supabase Test", layout="wide")

st.title("Swing Watchlist – Supabase Verbindungstest")
st.markdown("Aktueller Stand: App läuft auf Streamlit Cloud + Secrets sind hinterlegt")

# ────────────────────────────────────────────────
# Supabase Client initialisieren
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
        st.error(f"Fehler beim Erstellen des Supabase-Clients:\n{e}")
        st.stop()
        return None

supabase = get_supabase_client()

if supabase:
    st.success("✅ Supabase-Client erfolgreich initialisiert")

# ────────────────────────────────────────────────
# Test-Insert in watchlists
# ────────────────────────────────────────────────

st.subheader("1. Test-Eintrag in watchlists schreiben")

if st.button("→ Test-Watchlist erstellen"):
    try:
        test_data = {
            "name": f"Test {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "tickers": ["TESTA", "TESTB", "DEMO"],
            # user_id bewusst weggelassen → nur wenn RLS aus ist oder Policy passt
        }

        response = supabase.table("watchlists").insert(test_data).execute()

        if response.data:
            st.success("Eintrag erfolgreich geschrieben")
            st.json(response.data[0])
        else:
            st.warning("Insert lief, aber response.data ist leer")

    except Exception as e:
        st.error(f"Insert fehlgeschlagen\n\n{str(e)}")

# ────────────────────────────────────────────────
# Alle Einträge aus watchlists anzeigen
# ────────────────────────────────────────────────

st.subheader("2. watchlists Tabelle anzeigen")

if st.button("→ Alle Einträge laden"):
    try:
        response = supabase.table("watchlists").select("*").execute()

        if response.data:
            st.dataframe(response.data)
        else:
            st.info("Keine Einträge vorhanden (Tabelle leer)")

    except Exception as e:
        st.error(f"Select fehlgeschlagen\n\n{str(e)}")

# Hinweise
st.markdown("---")
st.caption("""
**Wichtige Hinweise zum aktuellen Stand**
• Wenn Insert oder Select fehlschlägt → meist Row Level Security (RLS)
• Lösung zum Testen: RLS für watchlists kurz deaktivieren
  → Supabase Dashboard → Authentication → Policies → watchlists → Enable RLS ausschalten
• Später bauen wir eine richtige Policy mit auth.uid()
""")
