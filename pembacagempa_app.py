import streamlit as st
import pandas as pd
import requests
import folium

from folium.plugins import HeatMap
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ==========================================
# CONFIG
# ==========================================

st.set_page_config(
    page_title="SeismoTrack Indonesia",
    page_icon="🌍",
    layout="wide"
)

# ==========================================
# HEADER
# ==========================================

st.title("🌍 SeismoTrack Indonesia")

st.markdown("""
### Sistem Monitoring Gempa Bumi Indonesia

📡 Data Realtime BMKG

---
""")

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("⚙️ Panel Kontrol")
st.sidebar.success("🟢 Sistem Online")

# ==========================================
# DATA BMKG
# ==========================================

URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"

@st.cache_data(ttl=300)
def load_data():

    response = requests.get(URL)

    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json()

    rows = []

    for g in data["Infogempa"]["gempa"]:

        rows.append({
            "Tanggal": g.get("Tanggal", ""),
            "Jam": g.get("Jam", ""),
            "Magnitude": float(g.get("Magnitude", 0)),
            "Kedalaman": g.get("Kedalaman", ""),
            "Wilayah": g.get("Wilayah", ""),
            "Koordinat": g.get("Coordinates", ""),
            "Dirasakan": g.get("Dirasakan", "-")
        })

    return pd.DataFrame(rows)

df = load_data()

if df.empty:
    st.error("❌ Gagal mengambil data dari BMKG")
    st.stop()

# ==========================================
# FILTER
# ==========================================

st.sidebar.subheader("🔍 Filter")

min_mag = st.sidebar.slider(
    "Minimal Magnitudo",
    0.0,
    10.0,
    0.0,
    0.1
)

keyword = st.sidebar.text_input(
    "Cari Wilayah",
    ""
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

# ==========================================
# ALARM GEMPA BESAR
# ==========================================

if len(hasil) > 0:

    max_mag = hasil["Magnitude"].max()

    if max_mag >= 6:
        st.error(
            f"🚨 PERINGATAN GEMPA BESAR TERDETEKSI (M {max_mag})"
        )

# ==========================================
# DASHBOARD
# ==========================================

st.subheader("📊 Dashboard")

col1, col2, col3, col4 = st.columns(4)

if len(hasil) > 0:

    col1.metric(
        "📌 Total Event",
        len(hasil)
    )

    col2.metric(
        "📈 Magnitudo Maks",
        round(
            hasil["Magnitude"].max(),
            2
        )
    )

    col3.metric(
        "📊 Rata-rata Magnitudo",
        round(
            hasil["Magnitude"].mean(),
            2
        )
    )

    wilayah_counts = hasil["Wilayah"].value_counts()

    wilayah_aktif = (
        wilayah_counts.index[0]
        if len(wilayah_counts) > 0
        else "-"
    )

    col4.metric(
        "🔥 Wilayah Aktif",
        wilayah_aktif[:20]
    )

else:

    col1.metric("📌 Total Event", 0)
    col2.metric("📈 Magnitudo Maks", "-")
    col3.metric("📊 Rata-rata Magnitudo", "-")
    col4.metric("🔥 Wilayah Aktif", "-")

    st.warning(
        "Tidak ada data yang sesuai dengan filter."
    )

# ==========================================
# PETA GEMPA
# ==========================================

st.subheader("🗺️ Peta Gempa Indonesia")

peta = folium.Map(
    location=[-2.5, 118],
    zoom_start=5,
    tiles="CartoDB dark_matter"
)

cluster = MarkerCluster()
cluster.add_to(peta)

heat_data = []

for _, row in hasil.iterrows():

    try:

        koordinat = str(row["Koordinat"]).split(",")

        if len(koordinat) != 2:
            continue

        lat = float(koordinat[0])
        lon = float(koordinat[1])

        heat_data.append([
            lat,
            lon,
            row["Magnitude"]
        ])

        warna = "green"

        if row["Magnitude"] >= 6:
            warna = "red"

        elif row["Magnitude"] >= 5:
            warna = "orange"

        popup = f"""
        <b>Wilayah:</b> {row['Wilayah']}<br>
        <b>Magnitude:</b> {row['Magnitude']}<br>
        <b>Kedalaman:</b> {row['Kedalaman']}<br>
        <b>Tanggal:</b> {row['Tanggal']}<br>
        <b>Jam:</b> {row['Jam']}<br>
        <b>Dirasakan:</b> {row['Dirasakan']}
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=row["Magnitude"] * 2,
            popup=popup,
            color=warna,
            fill=True,
            fill_color=warna,
            fill_opacity=0.8
        ).add_to(cluster)

    except:
        pass

if len(heat_data) > 0:

    HeatMap(
        heat_data,
        radius=20
    ).add_to(peta)

st_folium(
    peta,
    width=None,
    height=600
)

# ==========================================
# GRAFIK MAGNITUDO
# ==========================================

st.subheader("📈 Grafik Magnitudo")

if len(hasil) > 0:

    grafik = hasil[
        ["Wilayah", "Magnitude"]
    ].set_index("Wilayah")

    st.bar_chart(grafik)

# ==========================================
# WILAYAH PALING AKTIF
# ==========================================

st.subheader("🔥 Wilayah Paling Aktif")

if len(hasil) > 0:

    st.bar_chart(
        hasil["Wilayah"]
        .value_counts()
        .head(10)
    )

# ==========================================
# DATAFRAME
# ==========================================

st.subheader("📋 Data Gempa")

st.dataframe(
    hasil,
    use_container_width=True
)

# ==========================================
# DETAIL EVENT
# ==========================================

st.subheader("🔍 Detail Event")

if len(hasil) > 0:

    pilih = st.selectbox(
        "Pilih Event",
        hasil.index
    )

    st.json(
        hasil.loc[pilih].to_dict()
    )

# ==========================================
# DOWNLOAD CSV
# ==========================================

csv = hasil.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "📥 Download CSV",
    csv,
    "gempa_bmkg.csv",
    "text/csv"
)

# ==========================================
# FOOTER
# ==========================================

st.markdown("---")

st.caption(
    "SeismoTrack Indonesia v2.0 | BMKG Realtime | Dibuat dengan Streamlit"
)
