
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# ==========================
# KONFIGURASI HALAMAN
# ==========================

st.set_page_config(
    page_title="SeismoTrack Indonesia",
    page_icon="🌍",
    layout="wide"
)

# ==========================
# HEADER
# ==========================

st.title("🌍 SeismoTrack Indonesia")
st.markdown(
"""
### Sistem Monitoring Gempa Bumi Indonesia
Data realtime bersumber dari BMKG
---
"""
)

# ==========================
# SIDEBAR
# ==========================

st.sidebar.title("⚙️ Panel Kontrol")
st.sidebar.markdown("---")

URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"

# ==========================
# AMBIL DATA BMKG
# ==========================

@st.cache_data(ttl=300)
def load_data():

    response = requests.get(URL)
    data = response.json()

    rows = []

    for g in data["Infogempa"]["gempa"]:

        coord = g["Coordinates"].split(",")

        lat = float(coord[0])
        lon = float(coord[1])

        rows.append({
            "Tanggal": g["Tanggal"],
            "Jam": g["Jam"],
            "Magnitude": float(g["Magnitude"]),
            "Kedalaman": g["Kedalaman"],
            "Wilayah": g["Wilayah"],
            "Lintang": lat,
            "Bujur": lon,
            "Dirasakan": g.get("Dirasakan", "-")
        })

    return pd.DataFrame(rows)


df = load_data()

# ==========================
# FILTER
# ==========================

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

if keyword != "":
    hasil = hasil[
        hasil["Wilayah"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

# ==========================
# DASHBOARD
# ==========================

st.subheader("📊 Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "📌 Total Gempa",
    len(hasil)
)

if len(hasil) > 0:

    col2.metric(
        "📈 Magnitudo Max",
        hasil["Magnitude"].max()
    )

    col3.metric(
        "📊 Rata-rata M",
        round(
            hasil["Magnitude"].mean(),
            2
        )
    )

    col4.metric(
        "🔎 Wilayah",
        keyword if keyword else "Semua"
    )

# ==========================
# PETA GEMPA
# ==========================

st.subheader("🗺️ Peta Gempa Indonesia")

peta = folium.Map(
    location=[-2.5, 118],
    zoom_start=5
)

for _, r in hasil.iterrows():

    if r["Magnitude"] >= 6:
        warna = "red"
    elif r["Magnitude"] >= 5:
        warna = "orange"
    else:
        warna = "green"

    folium.CircleMarker(
        location=[
            r["Lintang"],
            r["Bujur"]
        ],
        radius=r["Magnitude"] * 2,
        color=warna,
        fill=True,
        fill_opacity=0.8,
        popup=f"""
<b>{r['Wilayah']}</b><br>
Tanggal : {r['Tanggal']}<br>
Jam : {r['Jam']}<br>
Magnitudo : {r['Magnitude']}<br>
Kedalaman : {r['Kedalaman']}<br>
Dirasakan : {r['Dirasakan']}
"""
    ).add_to(peta)

st_folium(
    peta,
    width=1200,
    height=500
)

# ==========================
# GRAFIK MAGNITUDO
# ==========================

st.subheader("📈 Grafik Magnitudo")

chart = hasil[[
    "Wilayah",
    "Magnitude"
]].set_index("Wilayah")

st.bar_chart(chart)

# ==========================
# TABEL DATA
# ==========================

st.subheader("📋 Data Gempa")

st.dataframe(
    hasil,
    use_container_width=True
)

# ==========================
# DETAIL GEMPA
# ==========================

st.subheader("🔍 Detail Gempa")

if len(hasil) > 0:

    pilih = st.selectbox(
        "Pilih Data Gempa",
        hasil.index
    )

    st.write(
        hasil.loc[pilih]
    )

# ==========================
# DOWNLOAD CSV
# ==========================

csv = hasil.to_csv(
    index=False
).encode(
    "utf-8"
)

st.download_button(
    label="📥 Download Data Gempa",
    data=csv,
    file_name="Data_Gempa_BMKG.csv",
    mime="text/csv"
)

# ==========================
# FOOTER
# ==========================

st.markdown("---")
st.caption(
    "SeismoTrack Indonesia | Data Realtime BMKG | Dibuat dengan Streamlit"
)
```
