import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Reifen Manager",
    page_icon="🚗",
    layout="wide"
)

@st.cache_data
def load_data():
    csv_path = r"C:\Users\zabun\Desktop\Master_Chief´s_Master_Apps\Reifen_manager\Ramsperger_Winterreifen_20250826_160010.csv"
    
    if not os.path.exists(csv_path):
        st.error(f"CSV-Datei nicht gefunden: {csv_path}")
        return pd.DataFrame()
    
    df = pd.read_csv(csv_path)
    df['Preis_EUR'] = df['Preis_EUR'].str.replace(',', '.').astype(float)
    df['Breite'] = df['Breite'].astype(int)
    df['Hoehe'] = df['Hoehe'].astype(int)
    df['Zoll'] = df['Zoll'].astype(int)
    
    return df

def get_efficiency_color(rating):
    colors = {
        'A': '🟢', 'B': '🟡', 'C': '🟠', 
        'D': '🟠', 'E': '🔴', 'F': '🔴', 'G': '⚫'
    }
    return colors.get(rating, '⚪')

# Header mit Logo - leicht nach links verschoben für Sidebar-Kompatibilität
logo_path = "ramsperger_logo.png"  # Logo im gleichen Verzeichnis
logo_path_alt = r"C:\Users\zabun\Desktop\Master_Chief´s_Master_Apps\Reifen_manager\ramsperger_logo.png"

# Logo etwas links von der Mitte positionieren (wegen Sidebar)
col1, col2, col3 = st.columns([0.3, 2, 1.7])
with col2:
    # Erst relativen Pfad probieren, dann absoluten
    if os.path.exists(logo_path):
        st.image(logo_path, width=1200)
    elif os.path.exists(logo_path_alt):
        st.image(logo_path_alt, width=1200)
    else:
        st.warning("⚠️ Logo nicht gefunden. Bitte kopieren Sie 'ramsperger_logo.png' in das App-Verzeichnis.")
        st.info("💡 Tipp: Logo sollte im gleichen Ordner wie die Python-Datei liegen.")

# Etwas Abstand nach dem Logo
st.markdown("<br>", unsafe_allow_html=True)

st.title("Reifen Manager")
st.markdown("### Reifen Auswahl für Ramsperger")

df = load_data()

if df.empty:
    st.stop()

# Sidebar Filter
st.sidebar.header("🔍 Detailfilter")

breite_filter = st.sidebar.selectbox(
    "Breite (mm)",
    options=['Alle'] + sorted(df['Breite'].unique().tolist()),
    index=0
)

hoehe_filter = st.sidebar.selectbox(
    "Höhe (%)",
    options=['Alle'] + sorted(df['Hoehe'].unique().tolist()),
    index=0
)

zoll_filter = st.sidebar.selectbox(
    "Zoll",
    options=['Alle'] + sorted(df['Zoll'].unique().tolist()),
    index=0
)

fabrikat = st.sidebar.selectbox(
    "Fabrikat",
    options=['Alle'] + sorted(df['Fabrikat'].unique().tolist()),
    index=0
)

loadindex_filter = st.sidebar.selectbox(
    "Loadindex",
    options=['Alle'] + sorted(df['Loadindex'].unique().tolist()),
    index=0
)

speedindex_filter = st.sidebar.selectbox(
    "Speedindex",
    options=['Alle'] + sorted(df['Speedindex'].unique().tolist()),
    index=0
)

min_preis, max_preis = st.sidebar.slider(
    "Preisbereich (€)",
    min_value=float(df['Preis_EUR'].min()),
    max_value=float(df['Preis_EUR'].max()),
    value=(float(df['Preis_EUR'].min()), float(df['Preis_EUR'].max())),
    step=5.0
)

sortierung = st.sidebar.selectbox(
    "Sortieren nach",
    options=['Preis aufsteigend', 'Preis absteigend', 'Fabrikat', 'Reifengröße']
)

show_stats = st.sidebar.checkbox("📊 Statistiken anzeigen", value=False)

# Session State für aktuelle Auswahl
if 'selected_size' not in st.session_state:
    st.session_state.selected_size = None

# Schnellstarter Buttons
st.subheader("🚀 Schnellauswahl - Gängige Reifengrößen")

# Top Reifengrößen als Buttons
top_sizes = [
    "215/65 R16", "205/55 R16", "205/60 R16", "215/60 R16", 
    "215/65 R17", "195/65 R15", "215/55 R17", "205/65 R16",
    "215/60 R17", "195/60 R16", "215/55 R16", "205/50 R17"
]

# 4 Spalten für Buttons
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

for i, size in enumerate(top_sizes):
    col = [col_btn1, col_btn2, col_btn3, col_btn4][i % 4]
    
    with col:
        if st.button(size, key=f"btn_{size}", use_container_width=True):
            st.session_state.selected_size = size
            # Parse die Größe
            parts = size.split('/')
            breite_val = int(parts[0])
            hoehe_zoll = parts[1].split(' R')
            hoehe_val = int(hoehe_zoll[0])
            zoll_val = int(hoehe_zoll[1])
            
            # Rerun mit den neuen Werten (wird über session state gehandhabt)
            st.rerun()

# Filter anwenden
filtered_df = df.copy()

# Wenn eine Schnellauswahl aktiv ist
if st.session_state.selected_size:
    parts = st.session_state.selected_size.split('/')
    schnell_breite = int(parts[0])
    hoehe_zoll = parts[1].split(' R')
    schnell_hoehe = int(hoehe_zoll[0])
    schnell_zoll = int(hoehe_zoll[1])
    
    filtered_df = filtered_df[
        (filtered_df['Breite'] == schnell_breite) &
        (filtered_df['Hoehe'] == schnell_hoehe) &
        (filtered_df['Zoll'] == schnell_zoll)
    ]
    
    st.info(f"🎯 Schnellauswahl aktiv: **{st.session_state.selected_size}**")
    if st.button("❌ Schnellauswahl zurücksetzen"):
        st.session_state.selected_size = None
        st.rerun()

# Detailfilter anwenden (zusätzlich zur Schnellauswahl)
if breite_filter != 'Alle':
    filtered_df = filtered_df[filtered_df['Breite'] == int(breite_filter)]

if hoehe_filter != 'Alle':
    filtered_df = filtered_df[filtered_df['Hoehe'] == int(hoehe_filter)]

if zoll_filter != 'Alle':
    filtered_df = filtered_df[filtered_df['Zoll'] == int(zoll_filter)]

if fabrikat != 'Alle':
    filtered_df = filtered_df[filtered_df['Fabrikat'] == fabrikat]

if loadindex_filter != 'Alle':
    filtered_df = filtered_df[filtered_df['Loadindex'] == loadindex_filter]

if speedindex_filter != 'Alle':
    filtered_df = filtered_df[filtered_df['Speedindex'] == speedindex_filter]

filtered_df = filtered_df[
    (filtered_df['Preis_EUR'] >= min_preis) & 
    (filtered_df['Preis_EUR'] <= max_preis)
]

# Sortierung
if sortierung == 'Preis aufsteigend':
    filtered_df = filtered_df.sort_values('Preis_EUR')
elif sortierung == 'Preis absteigend':
    filtered_df = filtered_df.sort_values('Preis_EUR', ascending=False)
elif sortierung == 'Fabrikat':
    filtered_df = filtered_df.sort_values(['Fabrikat', 'Preis_EUR'])
elif sortierung == 'Reifengröße':
    filtered_df = filtered_df.sort_values(['Zoll', 'Breite', 'Hoehe', 'Preis_EUR'])

# Ergebnisse anzeigen
st.subheader(f"🎯 Gefundene Reifen: {len(filtered_df)}")

if len(filtered_df) > 0:
    display_df = filtered_df.copy()
    display_df['Reifengröße'] = display_df['Breite'].astype(str) + '/' + display_df['Hoehe'].astype(str) + ' R' + display_df['Zoll'].astype(str)
    display_df['Kraftstoff'] = display_df['Kraftstoffeffizienz'].apply(lambda x: f"{get_efficiency_color(x)} {x}" if pd.notna(x) else "")
    display_df['Nasshaft.'] = display_df['Nasshaftung'].apply(lambda x: f"{get_efficiency_color(x)} {x}" if pd.notna(x) else "")
    display_df['Preis €'] = display_df['Preis_EUR'].apply(lambda x: f"{x:.2f} €")
    display_df['Lautstärke'] = display_df['Geräuschklasse'].astype(str) + ' dB'
    
    show_cols = ['Reifengröße', 'Fabrikat', 'Profil', 'Preis €', 'Kraftstoff', 'Nasshaft.', 'Lautstärke', 'Loadindex', 'Speedindex', 'Teilenummer']
    
    st.dataframe(
        display_df[show_cols],
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    # Statistiken nur wenn gewünscht
    if show_stats:
        st.subheader("📊 Statistiken")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Durchschnittspreis", f"{filtered_df['Preis_EUR'].mean():.2f} €")
        
        with col_stat2:
            st.metric("Günstigster Reifen", f"{filtered_df['Preis_EUR'].min():.2f} €")
        
        with col_stat3:
            st.metric("Teuerster Reifen", f"{filtered_df['Preis_EUR'].max():.2f} €")
        
        with col_stat4:
            st.metric("Verfügbare Größen", len(filtered_df[['Breite', 'Hoehe', 'Zoll']].drop_duplicates()))
            
else:
    st.warning("⚠️ Keine Reifen gefunden. Bitte Filter anpassen oder andere Reifengröße wählen.")

st.markdown("---")
st.markdown("**Legende:**")
col_leg1, col_leg2 = st.columns(2)
with col_leg1:
    st.markdown("**⚡ Speedindex (max. zulässige Geschwindigkeit):**")
    st.markdown("R = 170 km/h | S = 180 km/h | T = 190 km/h | H = 210 km/h | V = 240 km/h")
with col_leg2:
    st.markdown("**Reifengröße:** Breite/Höhe R Zoll")
    st.markdown("**Loadindex:** Tragfähigkeit pro Reifen in kg")