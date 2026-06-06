import streamlit as st
import pandas as pd
import requests
import folium

from folium.plugins import HeatMap
from folium.plugins import MarkerCluster

from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="SeismoTrack Indonesia",
    page_icon="🌍",
    layout="wide"
)

# Refresh setiap 60 detik
st_autorefresh(
    interval=60000,
    key="refresh"
)

# =====================================
# HEADER
# =====================================

st.title("🌍 SeismoTrack Indonesia")
st.markdown(
"""
### Sistem Monitoring Gempa Bumi Indonesia

📡 Data Realtime BMKG
⚡ Auto Update 60 Detik

---
"""
)

# =====================================
# SIDEBAR
# =====================================

st.sidebar.title("⚙️ Panel Kontrol")

st.sidebar.success("🟢 Sistem Online")

URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"

# =====================================
# LOAD DATA
# =====================================

@st.cache_data(ttl=300)
def load_data():

    r = requests.get(URL)

    data = r.json()

    rows = []

    for g in data["Infogempa"]["gempa"]:

        rows.append({
            "Tanggal": g["Tanggal"],
            "Jam": g["Jam"],
            "Magnitude": float(g["Magnitude"]),
            "Kedalaman": g["Kedalaman"],
            "Wilayah": g["Wilayah"],
            "Koordinat": g["Coordinates"],
            "Dirasakan": g.get("Dirasakan", "-")
        })

    return pd.DataFrame(rows)

df = load_data()

# =====================================
# FILTER
# =====================================

st.sidebar.subheader("🔍 Filter")

min_mag = st.sidebar.slider(
    "Minimal Magnitudo",
    0.0,
    10.0,
    0.0,
    0.1
)

keyword = st.sidebar.text_input(
    "Cari Wilayah"
)

hasil = df[df["Magnitude"] >= min_mag]

if keyword:

    hasil = hasil[
        hasil["Wilayah"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

# =====================================
# ALARM GEMPA BESAR
# =====================================

if len(hasil) > 0:

    max_mag = hasil["Magnitude"].max()

    if max_mag >= 6:

        st.error(
            f"🚨 PERINGATAN GEMPA BESAR TERDETEKSI (M {max_mag})"
        )

# =====================================
# DASHBOARD
# =====================================

st.subheader("📊 Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "📌 Total Event",
    len(hasil)
)

if len(hasil) > 0:

    c2.metric(
        "📈 Magnitudo Maks",
        hasil["Magnitude"].max()
    )

    c3.metric(
        "📊 Rata-rata Magnitudo",
        round(
            hasil["Magnitude"].mean(),
            2
        )
    )

    wilayah_aktif = (
        hasil["Wilayah"]
        .value_counts()
        .idxmax()
    )

    c4.metric(
        "🔥 Wilayah Aktif",
        wilayah_aktif[:20]
    )

# =====================================
# PETA
# =====================================

st.subheader("🗺️ Peta Gempa Indonesia")

peta = folium.Map(
    location=[-2.5, 118],
    zoom_start=5,
    tiles="CartoDB dark_matter"
)

cluster = MarkerCluster()
cluster.add_to(peta)

heat_data = []

for _, r in hasil.iterrows():

    lat = float(
        r["Koordinat"].split(",")[0]
    )

    lon = float(
        r["Koordinat"].split(",")[1]
    )

    heat_data.append([
        lat,
        lon,
        r["Magnitude"]
    ])

    warna = "green"

    if r["Magnitude"] >= 6:
        warna = "red"

    elif r["Magnitude"] >= 5:
        warna = "orange"

    popup = f"""
    <b>Wilayah:</b> {r['Wilayah']}<br>
    <b>Magnitude:</b> {r['Magnitude']}<br>
    <b>Kedalaman:</b> {r['Kedalaman']}<br>
    <b>Tanggal:</b> {r['Tanggal']}<br>
    <b>Jam:</b> {r['Jam']}<br>
    <b>Dirasakan:</b> {r['Dirasakan']}
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=r["Magnitude"] * 2,
        color=warna,
        fill=True,
        fill_color=warna,
        fill_opacity=0.8,
        popup=popup
    ).add_to(cluster)

HeatMap(
    heat_data,
    radius=20
).add_to(peta)

st_folium(
    peta,
    width=None,
    height=600
)

# =====================================
# GRAFIK MAGNITUDO
# =====================================

st.subheader("📈 Grafik Magnitudo")

chart = hasil[
    ["Wilayah", "Magnitude"]
].set_index("Wilayah")

st.bar_chart(chart)

# =====================================
# WILAYAH AKTIF
# =====================================

st.subheader("🔥 Wilayah Paling Aktif")

st.bar_chart(
    hasil["Wilayah"]
    .value_counts()
    .head(10)
)

# =====================================
# DATA TABLE
# =====================================

st.subheader("📋 Data Gempa")

st.dataframe(
    hasil,
    use_container_width=True
)

# =====================================
# DETAIL EVENT
# =====================================

st.subheader("🔍 Detail Gempa")

if len(hasil) > 0:

    pilih = st.selectbox(
        "Pilih Event",
        hasil.index
    )

    st.json(
        hasil.loc[pilih].to_dict()
    )

# =====================================
# DOWNLOAD
# =====================================

csv = hasil.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "📥 Download CSV",
    csv,
    "gempa_bmkg.csv",
    "text/csv"
)

# =====================================
# FOOTER
# =====================================

st.markdown("---")

st.caption(
    "SeismoTrack Indonesia v2.0 | BMKG Realtime | Streamlit"
)
