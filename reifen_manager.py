# reifen_manager.py
import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------- Basiskonfig ---------------------------
st.set_page_config(page_title="Reifen Manager", page_icon="🚗", layout="wide")

BASE_DIR = Path(__file__).parent  # Ordner der App-Datei

# --------------------------- Hilfsfunktionen ---------------------------
def latest_csv(pattern: str = "Ramsperger_Winterreifen_*.csv") -> Path | None:
    """Findet die neueste CSV im App-Ordner (z. B. wenn Datum im Namen steckt)."""
    files = sorted(BASE_DIR.glob(pattern))
    return files[-1] if files else None

@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """
    Lädt die Reifenliste:
    1) versucht die 'neueste' CSV (Pattern),
    2) Fallback: fester Dateiname im gleichen Ordner.
    Korrigiert Datentypen.
    """
    # 1) dynamisch suchen
    csv_path = latest_csv()
    # 2) Fallback auf festen Namen (falls Pattern nichts findet)
    if csv_path is None:
        csv_path = BASE_DIR / "Ramsperger_Winterreifen_20250826_160010.csv"

    if not csv_path.exists():
        st.error(f"CSV-Datei nicht gefunden: {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    # Erwartete Spalten minimal absichern
    # (falls CSV mal ohne Komma/als Float kommt etc.)
    if "Preis_EUR" in df.columns:
        if df["Preis_EUR"].dtype == object:
            df["Preis_EUR"] = (
                df["Preis_EUR"]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace("€", "", regex=False)
                .str.strip()
            )
        df["Preis_EUR"] = pd.to_numeric(df["Preis_EUR"], errors="coerce")
    else:
        df["Preis_EUR"] = pd.NA

    for c in ["Breite", "Hoehe", "Zoll"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        else:
            df[c] = pd.NA

    # String-Spalten, die wir anzeigen
    for c in [
        "Fabrikat",
        "Profil",
        "Kraftstoffeffizienz",
        "Nasshaftung",
        "Geräuschklasse",
        "Loadindex",
        "Speedindex",
        "Teilenummer",
    ]:
        if c not in df.columns:
            df[c] = pd.NA

    # Nullwerte rausfiltern, damit Filter/Sortierung stabil laufen
    df = df.dropna(subset=["Preis_EUR", "Breite", "Hoehe", "Zoll"], how="any")
    df["Breite"] = df["Breite"].astype(int)
    df["Hoehe"] = df["Hoehe"].astype(int)
    df["Zoll"] = df["Zoll"].astype(int)

    return df

def effi_emoji(rating: str | float | None) -> str:
    if pd.isna(rating):
        return "⚪"
    rating = str(rating).strip().upper()[:1]
    return {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🟠", "E": "🔴", "F": "🔴", "G": "⚫"}.get(rating, "⚪")

# --------------------------- Header / Logo ---------------------------
logo_path = BASE_DIR / "ramsperger_logo.png"
col1, col2, col3 = st.columns([1, 3, 1])  # Symmetrisch zentriert
with col2:
    if logo_path.exists():
        st.image(str(logo_path), use_column_width=True)  # Responsive Logo
    else:
        st.warning("⚠️ Logo nicht gefunden. Lege 'ramsperger_logo.png' in den App-Ordner.")

st.markdown("<br>", unsafe_allow_html=True)
st.title("Reifen Manager")
st.markdown("### Reifen Auswahl für Ramsperger")

# --------------------------- Daten laden ---------------------------
df = load_data()
if df.empty:
    st.stop()

# --------------------------- Sidebar: Filter ---------------------------
st.sidebar.header("🔍 Detailfilter")

breite_opt = ["Alle"] + sorted(df["Breite"].unique().tolist())
hoehe_opt = ["Alle"] + sorted(df["Hoehe"].unique().tolist())
zoll_opt = ["Alle"] + sorted(df["Zoll"].unique().tolist())
fabrikat_opt = ["Alle"] + sorted([x for x in df["Fabrikat"].dropna().unique().tolist()])

breite_filter = st.sidebar.selectbox("Breite (mm)", options=breite_opt, index=0)
hoehe_filter = st.sidebar.selectbox("Höhe (%)", options=hoehe_opt, index=0)
zoll_filter = st.sidebar.selectbox("Zoll", options=zoll_opt, index=0)
fabrikat = st.sidebar.selectbox("Fabrikat", options=fabrikat_opt, index=0)

loadindex_opt = ["Alle"] + sorted([x for x in df["Loadindex"].dropna().astype(str).unique().tolist()])
speedindex_opt = ["Alle"] + sorted([x for x in df["Speedindex"].dropna().astype(str).unique().tolist()])

loadindex_filter = st.sidebar.selectbox("Loadindex", options=loadindex_opt, index=0)
speedindex_filter = st.sidebar.selectbox("Speedindex", options=speedindex_opt, index=0)

min_price = float(df["Preis_EUR"].min())
max_price = float(df["Preis_EUR"].max())
min_preis, max_preis = st.sidebar.slider(
    "Preisbereich (€)",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    step=5.0,
)

sortierung = st.sidebar.selectbox(
    "Sortieren nach",
    options=["Preis aufsteigend", "Preis absteigend", "Fabrikat", "Reifengröße"],
)

show_stats = st.sidebar.checkbox("📊 Statistiken anzeigen", value=False)

# --------------------------- Session-/Schnellauswahl ---------------------------
if "selected_size" not in st.session_state:
    st.session_state.selected_size = None

st.subheader("🚀 Schnellauswahl – gängige Reifengrößen")
top_sizes = [
    "215/65 R16", "205/55 R16", "205/60 R16", "215/60 R16",
    "215/65 R17", "195/65 R15", "215/55 R17", "205/65 R16",
    "215/60 R17", "195/60 R16", "215/55 R16", "205/50 R17",
]
c1, c2, c3, c4 = st.columns(4)
cols = [c1, c2, c3, c4]
for i, size in enumerate(top_sizes):
    with cols[i % 4]:
        if st.button(size, key=f"btn_{size}", use_container_width=True):
            st.session_state.selected_size = size
            st.rerun()

# --------------------------- Filter anwenden ---------------------------
filtered = df.copy()

# Schnellauswahl
if st.session_state.selected_size:
    parts = st.session_state.selected_size.split("/")
    b = int(parts[0])
    h = int(parts[1].split(" R")[0])
    z = int(parts[1].split(" R")[1])
    filtered = filtered[(filtered["Breite"] == b) & (filtered["Hoehe"] == h) & (filtered["Zoll"] == z)]
    st.info(f"🎯 Schnellauswahl aktiv: **{st.session_state.selected_size}**")
    if st.button("❌ Schnellauswahl zurücksetzen"):
        st.session_state.selected_size = None
        st.rerun()

# Detailfilter
if breite_filter != "Alle":
    filtered = filtered[filtered["Breite"] == int(breite_filter)]
if hoehe_filter != "Alle":
    filtered = filtered[filtered["Hoehe"] == int(hoehe_filter)]
if zoll_filter != "Alle":
    filtered = filtered[filtered["Zoll"] == int(zoll_filter)]
if fabrikat != "Alle":
    filtered = filtered[filtered["Fabrikat"] == fabrikat]
if loadindex_filter != "Alle":
    filtered = filtered[filtered["Loadindex"].astype(str) == str(loadindex_filter)]
if speedindex_filter != "Alle":
    filtered = filtered[filtered["Speedindex"].astype(str) == str(speedindex_filter)]

filtered = filtered[(filtered["Preis_EUR"] >= min_preis) & (filtered["Preis_EUR"] <= max_preis)]

# Sortierung
if sortierung == "Preis aufsteigend":
    filtered = filtered.sort_values("Preis_EUR")
elif sortierung == "Preis absteigend":
    filtered = filtered.sort_values("Preis_EUR", ascending=False)
elif sortierung == "Fabrikat":
    filtered = filtered.sort_values(["Fabrikat", "Preis_EUR"])
elif sortierung == "Reifengröße":
    filtered = filtered.sort_values(["Zoll", "Breite", "Hoehe", "Preis_EUR"])

# --------------------------- Tabelle / Ausgabe ---------------------------
st.subheader(f"🎯 Gefundene Reifen: {len(filtered)}")

if len(filtered) > 0:
    display = filtered.copy()
    display["Reifengröße"] = (
        display["Breite"].astype(str) + "/" + display["Hoehe"].astype(str) + " R" + display["Zoll"].astype(str)
    )
    display["Kraftstoff"] = display["Kraftstoffeffizienz"].apply(lambda x: f"{effi_emoji(x)} {x}" if pd.notna(x) else "")
    display["Nasshaft."] = display["Nasshaftung"].apply(lambda x: f"{effi_emoji(x)} {x}" if pd.notna(x) else "")
    display["Preis €"] = display["Preis_EUR"].apply(lambda x: f"{float(x):.2f} €")
    if "Geräuschklasse" in display.columns:
        display["Lautstärke"] = display["Geräuschklasse"].astype(str) + " dB"
    else:
        display["Lautstärke"] = ""

    show_cols = [
        "Reifengröße", "Fabrikat", "Profil", "Preis €",
        "Kraftstoff", "Nasshaft.", "Lautstärke",
        "Loadindex", "Speedindex", "Teilenummer",
    ]
    # Nur vorhandene Spalten anzeigen (falls CSV mal variieren sollte)
    show_cols = [c for c in show_cols if c in display.columns]

    st.dataframe(
        display[show_cols],
        use_container_width=True,
        hide_index=True,
        height=520,
    )

    if show_stats:
        st.subheader("📊 Statistiken")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Durchschnittspreis", f"{filtered['Preis_EUR'].mean():.2f} €")
        with s2:
            st.metric("Günstigster Reifen", f"{filtered['Preis_EUR'].min():.2f} €")
        with s3:
            st.metric("Teuerster Reifen", f"{filtered['Preis_EUR'].max():.2f} €")
        with s4:
            unique_sizes = len(filtered[["Breite", "Hoehe", "Zoll"]].drop_duplicates())
            st.metric("Verfügbare Größen", unique_sizes)
else:
    st.warning("⚠️ Keine Reifen gefunden. Bitte Filter anpassen oder andere Reifengröße wählen.")

st.markdown("---")
st.markdown("**Legende:**")
cL, cR = st.columns(2)
with cL:
    st.markdown("**⚡ Speedindex (max. zulässige Geschwindigkeit):**")
    st.markdown("R = 170 km/h | S = 180 km/h | T = 190 km/h | H = 210 km/h | V = 240 km/h")
with cR:
    st.markdown("**Reifengröße:** Breite/Höhe R Zoll")
    st.markdown("**Loadindex:** Tragfähigkeit pro Reifen in kg")