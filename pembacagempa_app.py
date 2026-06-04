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

st.sidebar.header("Filter Gempa")

min_mag = st.sidebar.slider(
    "Minimal Magnitudo",
    0.0,
    10.0,
    0.0,
    0.1
)

cari = st.sidebar.text_input(
    "Cari Wilayah",
    ""
)

hasil = df[df["Magnitude"] >= min_mag]

if cari != "":
    hasil = hasil[
        hasil["Wilayah"].str.contains(
            cari,
            case=False,
            na=False
        )
    ]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Jumlah Gempa",
    len(hasil)
)

if len(hasil) > 0:
    col2.metric(
        "Magnitudo Maksimum",
        hasil["Magnitude"].max()
    )

    col3.metric(
        "Rata-rata Magnitudo",
        round(hasil["Magnitude"].mean(), 2)
    )

st.subheader("🗺️ Peta Gempa")

peta = folium.Map(
    location=[-2.5, 118],
    zoom_start=5
)

for _, r in hasil.iterrows():

    folium.Marker(
        location=[r["Lintang"], r["Bujur"]],
        popup=
        f"""
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

st.subheader("📋 Data Gempa")

st.dataframe(
    hasil,
    use_container_width=True
)

st.subheader("🔍 Detail Gempa")

if len(hasil) > 0:
    pilihan = st.selectbox(
        "Pilih Data",
        hasil.index
    )

    st.write(hasil.loc[pilihan])
else:
    st.warning("Data tidak ditemukan.")
