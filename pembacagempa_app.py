import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="SeismoTrack Indonesia",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 SeismoTrack Indonesia")
st.caption("Data realtime bersumber dari BMKG")

URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"

@st.cache_data(ttl=300)
def load_data():
    r = requests.get(URL)
    data = r.json()

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

st.sidebar.header("Filter Data")

mag = st.sidebar.slider(
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

hasil = df[df["Magnitude"] >= mag]

if keyword:
    hasil = hasil[
        hasil["Wilayah"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

c1,c2,c3 = st.columns(3)

c1.metric(
    "Jumlah Gempa",
    len(hasil)
)

c2.metric(
    "Magnitudo Maks",
    hasil["Magnitude"].max()
)

c3.metric(
    "Rata-rata Magnitudo",
    round(hasil["Magnitude"].mean(),2)
)

st.subheader("🗺️ Peta Gempa")

m = folium.Map(
    location=[-2.5,118],
    zoom_start=5
)

for _,r in hasil.iterrows():

    folium.Marker(
        [r["Lintang"],r["Bujur"]],
        popup=f"""
        <b>{r['Wilayah']}</b><br>
        Magnitudo : {r['Magnitude']}<br>
        Kedalaman : {r['Kedalaman']}<br>
        {r['Potensi']}
        """
    ).add_to(m)

st_folium(
    m,
    width=1200,
    height=500
)

st.subheader("📋 Data Gempa")

st.dataframe(
    hasil,
    use_container_width=True
)

st.subheader("ℹ Detail Gempa")

pilih = st.selectbox(
    "Pilih Gempa",
    hasil.index
)

st.write(hasil.loc[pilih])
