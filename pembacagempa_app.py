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
st.markdown("""
### Sistem Monitoring Gempa Bumi Indonesia
Data realtime bersumber dari BMKG
---
""")

st.sidebar.title("⚙️ Panel Kontrol")
st.sidebar.markdown("---")

URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"

@st.cache_data(ttl=300)
def load_data():

    response = requests.get(URL)
    data = response.json()

    rows = []

    for g in data["Infogempa"]["gempa"]:

        coord = g["Coordinates"].split(",")

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

st.subheader("📊 Dashboard")

c1, c2, c3 = st.columns(3)

c1.metric(
    "📌 Total Gempa",
    len(hasil)
)

if len(hasil) > 0:
    c2.metric(
        "📈 Magnitudo Maks",
        hasil["Magnitude"].max()
    )

    c3.metric(
        "📊 Rata-rata Magnitudo",
        round(hasil["Magnitude"].mean(), 2)
    )

st.subheader("🗺️ Peta Gempa")

peta = folium.Map(
    location=[-2.5, 118],
    zoom_start=5
)

for _, r in hasil.iterrows():

    koordinat = r["Koordinat"].split(",")

    lat = float(koordinat[0])
    lon = float(koordinat[1])

    warna = "green"

    if r["Magnitude"] >= 6:
        warna = "red"
    elif r["Magnitude"] >= 5:
        warna = "orange"

    folium.CircleMarker(
        location=[lat, lon],
        radius=r["Magnitude"] * 2,
        color=warna,
        fill=True,
        fill_opacity=0.8,
        popup=f"""
Wilayah : {r['Wilayah']}
Tanggal : {r['Tanggal']}
Jam : {r['Jam']}
Magnitudo : {r['Magnitude']}
Kedalaman : {r['Kedalaman']}
Dirasakan : {r['Dirasakan']}
"""
    ).add_to(peta)

st_folium(
    peta,
    width=1200,
    height=500
)

st.subheader("📈 Grafik Magnitudo")

grafik = hasil[["Wilayah", "Magnitude"]]
grafik = grafik.set_index("Wilayah")

st.bar_chart(grafik)

st.subheader("📋 Data Gempa")

st.dataframe(
    hasil,
    use_container_width=True
)

st.subheader("🔍 Detail Gempa")

if len(hasil) > 0:

    pilih = st.selectbox(
        "Pilih Data Gempa",
        hasil.index
    )

    st.write(
        hasil.loc[pilih]
    )

csv = hasil.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "📥 Download CSV",
    csv,
    "Data_Gempa_BMKG.csv",
    "text/csv"
)

st.markdown("---")
st.caption(
    "SeismoTrack Indonesia | Data Realtime BMKG | Dibuat dengan Streamlit"
)
