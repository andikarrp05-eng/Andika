import streamlit as st
import pandas as pd
import requests
import folium
import json
import base64
import math
from datetime import datetime
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
# ==========================================
# CONFIG
# ==========================================
st.set_page_config(
    page_title="SeismoTrack Indonesia",
    page_icon="🌍",
    layout="wide"
)
# ==========================================
# CUSTOM CSS - Premium Glassmorphism Design
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    /* Global styling */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    /* Header styling */
    .hero-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
        padding: 30px 35px;
        border-radius: 20px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.15), transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(255, 107, 107, 0.1), transparent 50%);
        animation: shimmer 8s ease-in-out infinite;
    }
    @keyframes shimmer {
        0%, 100% { transform: translate(0, 0); }
        50% { transform: translate(-5%, 5%); }
    }
    .hero-header h1 {
        font-size: 2.2em;
        font-weight: 800;
        margin: 0;
        position: relative;
        z-index: 2;
        background: linear-gradient(90deg, #fff, #a8edea, #fed6e3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-header p {
        color: rgba(255,255,255,0.75);
        margin: 8px 0 0 0;
        font-size: 1em;
        position: relative;
        z-index: 2;
        font-weight: 300;
    }
    .hero-badges {
        display: flex;
        gap: 12px;
        margin-top: 15px;
        position: relative;
        z-index: 2;
        flex-wrap: wrap;
    }
    .hero-badge {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.15);
        padding: 6px 16px;
        border-radius: 50px;
        font-size: 0.82em;
        color: rgba(255,255,255,0.9);
        display: flex;
        align-items: center;
        gap: 6px;
    }
    /* Notifikasi gempa styling */
    .gempa-alert {
        background: linear-gradient(135deg, #e53935, #b71c1c);
        color: white;
        padding: 24px 28px;
        border-radius: 16px;
        margin: 10px 0;
        border-left: 6px solid #ffcc00;
        animation: pulse-alert 2s infinite;
        box-shadow: 0 8px 32px rgba(229, 57, 53, 0.45);
        position: relative;
        overflow: hidden;
    }
    .gempa-alert::after {
        content: '';
        position: absolute;
        top: 0; right: 0; bottom: 0; left: 0;
        background: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(255,255,255,0.03) 10px,
            rgba(255,255,255,0.03) 20px
        );
    }
    .gempa-alert-warning {
        background: linear-gradient(135deg, #ff9800, #e65100);
        color: white;
        padding: 24px 28px;
        border-radius: 16px;
        margin: 10px 0;
        border-left: 6px solid #ffcc00;
        animation: pulse-warning 3s infinite;
        box-shadow: 0 8px 32px rgba(255, 152, 0, 0.35);
    }
    .gempa-alert-info {
        background: linear-gradient(135deg, #1565C0, #0D47A1);
        color: white;
        padding: 18px 24px;
        border-radius: 16px;
        margin: 10px 0;
        border-left: 6px solid #64B5F6;
        box-shadow: 0 8px 32px rgba(21, 101, 192, 0.3);
    }
    @keyframes pulse-alert {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.008); opacity: 0.92; }
    }
    @keyframes pulse-warning {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.005); opacity: 0.95; }
    }
    /* Stat cards */
    .stat-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 22px 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }
    .stat-card .stat-icon {
        font-size: 2em;
        margin-bottom: 6px;
    }
    .stat-card .stat-value {
        font-size: 1.8em;
        font-weight: 800;
        color: white;
        margin: 4px 0;
    }
    .stat-card .stat-label {
        font-size: 0.8em;
        color: rgba(255,255,255,0.55);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 500;
    }
    .stat-card.red { border-bottom: 3px solid #e94560; }
    .stat-card.blue { border-bottom: 3px solid #0fbcf9; }
    .stat-card.green { border-bottom: 3px solid #0be881; }
    .stat-card.orange { border-bottom: 3px solid #ffa801; }
    /* Satellite detail card */
    .satellite-detail-card {
        background: linear-gradient(145deg, #0d1117, #161b22);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 16px 48px rgba(0,0,0,0.3);
        margin: 15px 0;
    }
    .satellite-detail-card h3 {
        color: #58a6ff;
        margin: 0 0 12px 0;
        font-weight: 700;
    }
    .satellite-detail-card .detail-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        color: rgba(255,255,255,0.8);
        font-size: 0.92em;
    }
    .satellite-detail-card .detail-row .label {
        color: rgba(255,255,255,0.45);
        font-weight: 500;
    }
    .satellite-detail-card .detail-row .value {
        font-weight: 600;
        color: white;
    }
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, rgba(88,166,255,0.1), transparent);
        border-left: 4px solid #58a6ff;
        padding: 12px 20px;
        border-radius: 0 12px 12px 0;
        margin: 20px 0 15px 0;
    }
    .section-header h3 {
        margin: 0;
        color: white;
        font-weight: 700;
        font-size: 1.15em;
    }
    /* Map container */
    .map-container {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.08);
    }
    /* Region card */
    .region-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #e94560;
    }
    .stMetric {
        background: linear-gradient(135deg, #0a0a23, #1a1a3e);
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)
# ==========================================
# HEADER - Premium Hero
# ==========================================
st.markdown("""
<div class="hero-header">
    <h1>🌍 SeismoTrack Indonesia</h1>
    <p>Sistem Monitoring Gempa Bumi Indonesia — Visualisasi Satelit Real-Time</p>
    <div class="hero-badges">
        <span class="hero-badge">📡 BMKG Realtime</span>
        <span class="hero-badge">🛰️ Citra Satelit HD</span>
        <span class="hero-badge">🔔 Notifikasi & Alarm</span>
        <span class="hero-badge">🗺️ Multi-Mode Peta</span>
    </div>
</div>
""", unsafe_allow_html=True)
# ==========================================
# GPS PENGGUNA
# ==========================================
st.markdown("---")
st.subheader("📍 Lokasi Pengguna (GPS)")
if st.button("📍 Ambil Lokasi Saya"):
    st.rerun()
location = streamlit_geolocation()
user_lat = None
user_lon = None
if location and location["latitude"] is not None:
    user_lat = location["latitude"]
    user_lon = location["longitude"]
    st.success(
        f"📍 Latitude: {user_lat:.6f} | Longitude: {user_lon:.6f}"
    )
else:
    st.info("Klik Allow untuk mengaktifkan GPS")
# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("⚙️ Panel Kontrol")
st.sidebar.success("🟢 Sistem Online")
# ==========================================
# BMKG API - Multiple endpoints
# ==========================================
URL_TERKINI = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
URL_DIRASAKAN = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"
URL_M5 = "https://data.bmkg.go.id/DataMKG/TEWS/gempa_m5.json"
# ==========================================
# DAFTAR PROVINSI INDONESIA
# ==========================================
PROVINSI_INDONESIA = [
    "Semua Provinsi",
    "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi",
    "Sumatera Selatan", "Bengkulu", "Lampung", "Kep. Bangka Belitung",
    "Kep. Riau", "DKI Jakarta", "Jawa Barat", "Jawa Tengah",
    "DI Yogyakarta", "Jawa Timur", "Banten", "Bali",
    "Nusa Tenggara Barat", "Nusa Tenggara Timur",
    "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan",
    "Kalimantan Timur", "Kalimantan Utara",
    "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan",
    "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat",
    "Maluku", "Maluku Utara", "Papua", "Papua Barat",
    "Papua Selatan", "Papua Tengah", "Papua Pegunungan", "Papua Barat Daya"
]
# Keyword mapping untuk pencarian wilayah
KEYWORD_WILAYAH = {
    "Aceh": ["aceh", "banda aceh", "lhokseumawe", "sabang"],
    "Sumatera Utara": ["sumatera utara", "sumut", "medan", "nias", "toba"],
    "Sumatera Barat": ["sumatera barat", "sumbar", "padang", "mentawai", "bukittinggi"],
    "Riau": ["riau", "pekanbaru", "dumai"],
    "Jambi": ["jambi"],
    "Sumatera Selatan": ["sumatera selatan", "sumsel", "palembang"],
    "Bengkulu": ["bengkulu"],
    "Lampung": ["lampung", "bandar lampung"],
    "Kep. Bangka Belitung": ["bangka", "belitung", "babel"],
    "Kep. Riau": ["kepri", "batam", "tanjungpinang", "natuna", "anambas"],
    "DKI Jakarta": ["jakarta"],
    "Jawa Barat": ["jawa barat", "jabar", "bandung", "bogor", "sukabumi", "cianjur", "garut", "tasikmalaya", "pangandaran"],
    "Jawa Tengah": ["jawa tengah", "jateng", "semarang", "cilacap", "kebumen", "purworejo"],
    "DI Yogyakarta": ["yogyakarta", "jogja", "bantul", "sleman", "gunungkidul"],
    "Jawa Timur": ["jawa timur", "jatim", "surabaya", "malang", "banyuwangi", "jember", "situbondo"],
    "Banten": ["banten", "serang", "tangerang", "pandeglang", "lebak"],
    "Bali": ["bali", "denpasar", "karangasem", "singaraja"],
    "Nusa Tenggara Barat": ["ntb", "nusa tenggara barat", "lombok", "sumbawa", "mataram", "bima", "dompu"],
    "Nusa Tenggara Timur": ["ntt", "nusa tenggara timur", "kupang", "flores", "ende", "sikka", "sumba", "timor", "alor", "lembata", "manggarai"],
    "Kalimantan Barat": ["kalimantan barat", "kalbar", "pontianak"],
    "Kalimantan Tengah": ["kalimantan tengah", "kalteng", "palangkaraya"],
    "Kalimantan Selatan": ["kalimantan selatan", "kalsel", "banjarmasin"],
    "Kalimantan Timur": ["kalimantan timur", "kaltim", "samarinda", "balikpapan"],
    "Kalimantan Utara": ["kalimantan utara", "kaltara", "tarakan"],
    "Sulawesi Utara": ["sulawesi utara", "sulut", "manado", "minahasa", "sangihe", "talaud"],
    "Sulawesi Tengah": ["sulawesi tengah", "sulteng", "palu", "donggala", "poso", "banggai"],
    "Sulawesi Selatan": ["sulawesi selatan", "sulsel", "makassar", "bone", "bulukumba"],
    "Sulawesi Tenggara": ["sulawesi tenggara", "sultra", "kendari", "wakatobi", "buton", "muna", "konawe"],
    "Gorontalo": ["gorontalo"],
    "Sulawesi Barat": ["sulawesi barat", "sulbar", "mamuju", "majene"],
    "Maluku": ["maluku", "ambon", "seram", "buru", "banda"],
    "Maluku Utara": ["maluku utara", "malut", "ternate", "halmahera", "tidore"],
    "Papua": ["papua", "jayapura", "merauke", "biak", "yapen"],
    "Papua Barat": ["papua barat", "manokwari", "sorong"],
    "Papua Selatan": ["papua selatan"],
    "Papua Tengah": ["papua tengah", "nabire", "timika"],
    "Papua Pegunungan": ["papua pegunungan", "wamena"],
    "Papua Barat Daya": ["papua barat daya"]
}
# ==========================================
# LOAD DATA (MULTI-SOURCE)
# ==========================================
@st.cache_data(ttl=300)
def load_data():
    all_rows = []
    # Sumber 1: Gempa Terkini
    try:
        response = requests.get(URL_TERKINI, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for g in data["Infogempa"]["gempa"]:
                all_rows.append({
                    "Tanggal": g.get("Tanggal", ""),
                    "Jam": g.get("Jam", ""),
                    "Magnitude": float(g.get("Magnitude", 0)),
                    "Kedalaman": g.get("Kedalaman", ""),
                    "Wilayah": g.get("Wilayah", ""),
                    "Koordinat": g.get("Coordinates", ""),
                    "Dirasakan": g.get("Dirasakan", "-"),
                    "Potensi": g.get("Potensi", "-"),
                    "Sumber": "Gempa Terkini"
                })
    except Exception:
        pass
    # Sumber 2: Gempa Dirasakan
    try:
        response = requests.get(URL_DIRASAKAN, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for g in data["Infogempa"]["gempa"]:
                all_rows.append({
                    "Tanggal": g.get("Tanggal", ""),
                    "Jam": g.get("Jam", ""),
                    "Magnitude": float(g.get("Magnitude", 0)),
                    "Kedalaman": g.get("Kedalaman", ""),
                    "Wilayah": g.get("Wilayah", ""),
                    "Koordinat": g.get("Coordinates", ""),
                    "Dirasakan": g.get("Dirasakan", "-"),
                    "Potensi": g.get("Potensi", "-"),
                    "Sumber": "Gempa Dirasakan"
                })
    except Exception:
        pass
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    # Hapus duplikat berdasarkan Tanggal, Jam, dan Koordinat
    df = df.drop_duplicates(subset=["Tanggal", "Jam", "Koordinat"], keep="first")
    return df
df = load_data()
if df.empty:
    st.error("❌ Gagal mengambil data BMKG. Silakan coba lagi nanti.")
    st.stop()
# ==========================================
# SIDEBAR - FILTER WILAYAH INDONESIA
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Pencarian Wilayah")
provinsi_pilihan = st.sidebar.selectbox(
    "📍 Pilih Provinsi",
    PROVINSI_INDONESIA,
    index=0
)
kota_input = st.sidebar.text_input(
    "🔍 Cari Kota / Daerah",
    "",
    placeholder="Contoh: Padang, Lombok, Ternate..."
)
st.sidebar.markdown("---")
st.sidebar.subheader("📐 Pencarian Radius")
use_radius = st.sidebar.checkbox("Aktifkan pencarian radius", value=False)
if use_radius:
    radius_lat = st.sidebar.number_input("Latitude Pusat", value=-2.5, format="%.4f")
    radius_lon = st.sidebar.number_input("Longitude Pusat", value=118.0, format="%.4f")
    radius_km = st.sidebar.slider("Radius (km)", 50, 1000, 300, 50)
# ==========================================
# SIDEBAR - FILTER MAGNITUDO & KEDALAMAN
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Filter Data")
min_mag = st.sidebar.slider("Minimal Magnitudo", 0.0, 10.0, 0.0, 0.1)
max_mag = st.sidebar.slider("Maksimal Magnitudo", 0.0, 10.0, 10.0, 0.1)
kedalaman_filter = st.sidebar.selectbox(
    "Kedalaman Gempa",
    ["Semua", "Dangkal (< 70 km)", "Menengah (70-300 km)", "Dalam (> 300 km)"]
)
# ==========================================
# SIDEBAR - PENGATURAN NOTIFIKASI
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🔔 Pengaturan Notifikasi")
notif_threshold = st.sidebar.slider(
    "Ambang Magnitudo Alarm", 3.0, 9.0, 5.0, 0.5,
    help="Gempa dengan magnitudo di atas nilai ini akan memicu alarm peringatan"
)
enable_sound = st.sidebar.checkbox("🔊 Aktifkan Alarm Suara", value=True)
enable_visual = st.sidebar.checkbox("🚨 Aktifkan Notifikasi Visual", value=True)
# ==========================================
# SIDEBAR - MODE PETA
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Pengaturan Peta")
peta_mode = st.sidebar.radio(
    "Mode Peta Utama",
    ["🛰️ Satelit HD (Esri)", "🛰️ Satelit + Label (Google Hybrid)", "🌑 Mode Gelap (Dark)", "🗺️ Mode Dasar (Street)"],
    index=0
)
show_heatmap = st.sidebar.checkbox("🔥 Tampilkan Heatmap", value=True)
show_markers = st.sidebar.checkbox("📍 Tampilkan Marker", value=True)
show_epicenter_rings = st.sidebar.checkbox("🎯 Tampilkan Lingkaran Episenter", value=True)
# ==========================================
# APPLY FILTER
# ==========================================
hasil = df.copy()
hasil = hasil[(hasil["Magnitude"] >= min_mag) & (hasil["Magnitude"] <= max_mag)]
def parse_kedalaman(k):
    try:
        return float(str(k).replace(" km", "").replace("km", "").strip())
    except:
        return None
if kedalaman_filter != "Semua":
    hasil["_kedalaman_num"] = hasil["Kedalaman"].apply(parse_kedalaman)
    if kedalaman_filter == "Dangkal (< 70 km)":
        hasil = hasil[hasil["_kedalaman_num"] < 70]
    elif kedalaman_filter == "Menengah (70-300 km)":
        hasil = hasil[(hasil["_kedalaman_num"] >= 70) & (hasil["_kedalaman_num"] <= 300)]
    elif kedalaman_filter == "Dalam (> 300 km)":
        hasil = hasil[hasil["_kedalaman_num"] > 300]
    if "_kedalaman_num" in hasil.columns:
        hasil = hasil.drop(columns=["_kedalaman_num"])
if provinsi_pilihan != "Semua Provinsi":
    keywords = KEYWORD_WILAYAH.get(provinsi_pilihan, [provinsi_pilihan.lower()])
    mask = pd.Series([False] * len(hasil), index=hasil.index)
    for kw in keywords:
        mask = mask | hasil["Wilayah"].str.contains(kw, case=False, na=False)
    hasil = hasil[mask]
if kota_input:
    kota_keywords = [k.strip() for k in kota_input.split(",")]
    mask = pd.Series([False] * len(hasil), index=hasil.index)
    for kw in kota_keywords:
        if kw:
            mask = mask | hasil["Wilayah"].str.contains(kw, case=False, na=False)
    hasil = hasil[mask]
if use_radius and len(hasil) > 0:
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    def check_radius(coord_str):
        try:
            parts = str(coord_str).split(",")
            lat = float(parts[0])
            lon = float(parts[1])
            dist = haversine(radius_lat, radius_lon, lat, lon)
            return dist <= radius_km
        except:
            return False
    hasil = hasil[hasil["Koordinat"].apply(check_radius)]
# ==========================================
# SISTEM NOTIFIKASI & ALARM PERINGATAN
# ==========================================
st.markdown('<div class="section-header"><h3>🔔 Notifikasi Peringatan Gempa</h3></div>', unsafe_allow_html=True)
if len(hasil) > 0:
    gempa_bahaya = hasil[hasil["Magnitude"] >= notif_threshold]
    if len(gempa_bahaya) > 0:
        event_terbesar = gempa_bahaya.loc[gempa_bahaya["Magnitude"].idxmax()]
        mag_terbesar = float(event_terbesar["Magnitude"])
        if mag_terbesar >= 6.0 and enable_visual:
            st.markdown(f"""
            <div class="gempa-alert">
                <h2 style="position:relative;z-index:2;">🚨 PERINGATAN GEMPA BESAR!</h2>
                <p style="position:relative;z-index:2;"><b>📍 Lokasi:</b> {event_terbesar['Wilayah']}</p>
                <p style="position:relative;z-index:2;"><b>📈 Magnitudo:</b> M {mag_terbesar}</p>
                <p style="position:relative;z-index:2;"><b>📏 Kedalaman:</b> {event_terbesar['Kedalaman']}</p>
                <p style="position:relative;z-index:2;"><b>📅 Waktu:</b> {event_terbesar['Tanggal']} {event_terbesar['Jam']}</p>
                <p style="position:relative;z-index:2;"><b>🔊 Dirasakan:</b> {event_terbesar['Dirasakan']}</p>
                <p style="position:relative;z-index:2;"><b>⚠️ Potensi:</b> {event_terbesar.get('Potensi', '-')}</p>
                <hr style="position:relative;z-index:2; border-color:rgba(255,255,255,0.2);">
                <p style="position:relative;z-index:2;">⚠️ <b>SEGERA cek informasi resmi BMKG dan ikuti prosedur evakuasi!</b></p>
            </div>
            """, unsafe_allow_html=True)
        elif mag_terbesar >= 5.0 and enable_visual:
            st.markdown(f"""
            <div class="gempa-alert-warning">
                <h2>⚠️ PERINGATAN GEMPA SIGNIFIKAN</h2>
                <p><b>📍 Lokasi:</b> {event_terbesar['Wilayah']}</p>
                <p><b>📈 Magnitudo:</b> M {mag_terbesar}</p>
                <p><b>📏 Kedalaman:</b> {event_terbesar['Kedalaman']}</p>
                <p><b>📅 Waktu:</b> {event_terbesar['Tanggal']} {event_terbesar['Jam']}</p>
                <p><b>🔊 Dirasakan:</b> {event_terbesar['Dirasakan']}</p>
                <hr style="border-color:rgba(255,255,255,0.2);">
                <p>📢 Tetap waspada dan pantau informasi BMKG.</p>
            </div>
            """, unsafe_allow_html=True)
        elif enable_visual:
            st.markdown(f"""
            <div class="gempa-alert-info">
                <h3>ℹ️ Info Gempa Terdeteksi</h3>
                <p><b>📍</b> {event_terbesar['Wilayah']} | <b>M {mag_terbesar}</b> | {event_terbesar['Kedalaman']}</p>
                <p><b>📅</b> {event_terbesar['Tanggal']} {event_terbesar['Jam']}</p>
            </div>
            """, unsafe_allow_html=True)
        # === ALARM SUARA ===
        if enable_sound and mag_terbesar >= notif_threshold:
            if mag_terbesar >= 6.0:
                alarm_type = "danger"
                alarm_label = "🚨 SIREN DARURAT"
            elif mag_terbesar >= 5.0:
                alarm_type = "warning"
                alarm_label = "⚠️ ALARM PERINGATAN"
            else:
                alarm_type = "info"
                alarm_label = "🔔 NOTIFIKASI"
            st.markdown(f"**{alarm_label}** — Magnitudo M {mag_terbesar}")
            alarm_js = f"""
            <div id="alarm-control" style="margin: 10px 0;">
                <button onclick="playAlarm()" style="
                    background: {'#e53935' if alarm_type == 'danger' else '#ff9800' if alarm_type == 'warning' else '#1565C0'};
                    color: white; border: none; padding: 12px 24px; border-radius: 12px;
                    cursor: pointer; font-size: 15px; font-weight: 600;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
                    transition: transform 0.2s, box-shadow 0.2s;
                    font-family: 'Inter', sans-serif;
                " onmouseover="this.style.transform='scale(1.05)';this.style.boxShadow='0 6px 20px rgba(0,0,0,0.4)'" onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 4px 16px rgba(0,0,0,0.3)'">
                    🔊 Putar Alarm
                </button>
                <button onclick="stopAlarm()" style="
                    background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2);
                    padding: 12px 24px; border-radius: 12px; cursor: pointer; font-size: 15px; font-weight: 600;
                    margin-left: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.2);
                    transition: transform 0.2s; font-family: 'Inter', sans-serif;
                    backdrop-filter: blur(10px);
                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    🔇 Stop Alarm
                </button>
            </div>
            <script>
                let audioCtx = null;
                let oscillators = [];
                let gainNode = null;
                let alarmInterval = null;
                function playAlarm() {{
                    stopAlarm();
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    gainNode = audioCtx.createGain();
                    gainNode.connect(audioCtx.destination);
                    gainNode.gain.value = 0.3;
                    let alarmType = "{alarm_type}";
                    if (alarmType === "danger") {{
                        let count = 0;
                        alarmInterval = setInterval(() => {{
                            let osc = audioCtx.createOscillator();
                            osc.type = "sawtooth";
                            osc.frequency.value = count % 2 === 0 ? 800 : 600;
                            osc.connect(gainNode);
                            osc.start();
                            oscillators.push(osc);
                            setTimeout(() => {{ osc.stop(); }}, 400);
                            count++;
                            if (count > 20) stopAlarm();
                        }}, 500);
                    }} else if (alarmType === "warning") {{
                        let count = 0;
                        alarmInterval = setInterval(() => {{
                            let osc = audioCtx.createOscillator();
                            osc.type = "square";
                            osc.frequency.value = 700;
                            osc.connect(gainNode);
                            osc.start();
                            oscillators.push(osc);
                            setTimeout(() => {{ osc.stop(); }}, 200);
                            count++;
                            if (count > 12) stopAlarm();
                        }}, 400);
                    }} else {{
                        let count = 0;
                        alarmInterval = setInterval(() => {{
                            let osc = audioCtx.createOscillator();
                            osc.type = "sine";
                            osc.frequency.value = 880;
                            osc.connect(gainNode);
                            osc.start();
                            oscillators.push(osc);
                            setTimeout(() => {{ osc.stop(); }}, 150);
                            count++;
                            if (count > 6) stopAlarm();
                        }}, 600);
                    }}
                }}
                function stopAlarm() {{
                    if (alarmInterval) clearInterval(alarmInterval);
                    oscillators.forEach(o => {{ try {{ o.stop(); }} catch(e) {{}} }});
                    oscillators = [];
                    if (audioCtx) {{ audioCtx.close(); audioCtx = null; }}
                }}
            </script>
            """
            st.components.v1.html(alarm_js, height=70)
        if len(gempa_bahaya) > 1:
            with st.expander(f"📋 Semua Gempa di Atas M {notif_threshold} ({len(gempa_bahaya)} event)", expanded=False):
                for idx, row in gempa_bahaya.iterrows():
                    emoji = "🔴" if row["Magnitude"] >= 6 else "🟠" if row["Magnitude"] >= 5 else "🟡"
                    st.markdown(f"{emoji} **M {row['Magnitude']}** — {row['Wilayah']} | {row['Tanggal']} {row['Jam']}")
    else:
        st.info(f"✅ Tidak ada gempa di atas M {notif_threshold} dalam data saat ini. Wilayah aman.")
else:
    st.warning("Tidak ada data gempa sesuai filter yang dipilih.")
# ==========================================
# DASHBOARD - Premium Stat Cards
# ==========================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>📊 Dashboard Statistik</h3></div>', unsafe_allow_html=True)
if len(hasil) > 0:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card red">
            <div class="stat-icon">📌</div>
            <div class="stat-value">{len(hasil)}</div>
            <div class="stat-label">Total Event</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card orange">
            <div class="stat-icon">📈</div>
            <div class="stat-value">{round(hasil['Magnitude'].max(), 1)}</div>
            <div class="stat-label">Magnitudo Maks</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card blue">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{round(hasil['Magnitude'].mean(), 1)}</div>
            <div class="stat-label">Rata-rata</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        wilayah_counts = hasil["Wilayah"].value_counts()
        wilayah_aktif = wilayah_counts.index[0][:22] if len(wilayah_counts) > 0 else "-"
        st.markdown(f"""
        <div class="stat-card green">
            <div class="stat-icon">🔥</div>
            <div class="stat-value" style="font-size:1em;">{wilayah_aktif}</div>
            <div class="stat-label">Wilayah Aktif</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("Tidak ada data yang sesuai dengan filter.")
# ==========================================
# PETA GEMPA - ENHANCED SATELLITE
# ==========================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>🛰️ Peta Satelit Gempa Indonesia</h3></div>', unsafe_allow_html=True)
st.caption("Klik marker untuk melihat detail gempa. Gunakan layer control (kanan atas) untuk mengganti mode peta.")
# Determine base tile
TILE_ESRI_SATELLITE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
TILE_ESRI_ATTR = "Esri, Maxar, Earthstar Geographics, CNES/Airbus DS, USDA FSA, USGS, AeroGRID, IGN, GIS User Community"
TILE_GOOGLE_HYBRID = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
TILE_GOOGLE_SAT = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
# Map center
if user_lat is not None and user_lon is not None:
    map_center = [user_lat, user_lon]
    map_zoom = 12
elif use_radius:
    map_center = [radius_lat, radius_lon]
    map_zoom = 7
else:
    map_center = [-2.5, 118]
    map_zoom = 5
# Create map with chosen default tile
if peta_mode == "🛰️ Satelit HD (Esri)":
    peta = folium.Map(location=map_center, zoom_start=map_zoom, tiles=TILE_ESRI_SATELLITE, attr=TILE_ESRI_ATTR)
elif peta_mode == "🛰️ Satelit + Label (Google Hybrid)":
    peta = folium.Map(location=map_center, zoom_start=map_zoom, tiles=TILE_GOOGLE_HYBRID, attr="Google")
elif peta_mode == "🌑 Mode Gelap (Dark)":
    peta = folium.Map(location=map_center, zoom_start=map_zoom, tiles="CartoDB dark_matter")
else:
    peta = folium.Map(location=map_center, zoom_start=map_zoom, tiles="OpenStreetMap")
# ==========================================
# MARKER GPS PENGGUNA
# ==========================================
if user_lat is not None and user_lon is not None:
    folium.Marker(
        location=[user_lat, user_lon],
        popup=f"""
        <b>📍 Lokasi Anda</b><br>
        Latitude : {user_lat:.6f}<br>
        Longitude : {user_lon:.6f}
        """,
        tooltip="📍 Lokasi Saya",
        icon=folium.Icon(
            color="blue",
            icon="user",
            prefix="fa"
        )
    ).add_to(peta)
    # Lingkaran akurasi lokasi
    folium.Circle(
        location=[user_lat, user_lon],
        radius=100,
        color="blue",
        fill=True,
        fill_opacity=0.2
    ).add_to(peta)
# Add ALL tile layers as switchable overlays
folium.TileLayer(
    tiles=TILE_ESRI_SATELLITE,
    attr=TILE_ESRI_ATTR,
    name="🛰️ Satelit HD (Esri)"
).add_to(peta)
folium.TileLayer(
    tiles=TILE_GOOGLE_HYBRID,
    attr="Google",
    name="🛰️ Satelit + Label"
).add_to(peta)
folium.TileLayer(
    tiles=TILE_GOOGLE_SAT,
    attr="Google",
    name="🛰️ Satelit Google"
).add_to(peta)
folium.TileLayer("CartoDB dark_matter", name="🌑 Gelap").add_to(peta)
folium.TileLayer("OpenStreetMap", name="🗺️ Dasar").add_to(peta)
folium.TileLayer(
    tiles="https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}",
    attr="USGS",
    name="🏔️ Topografi"
).add_to(peta)
# Layer control
folium.LayerControl(position="topright", collapsed=False).add_to(peta)
# Prepare markers
cluster = MarkerCluster(name="📍 Marker Gempa").add_to(peta)
heat_data = []
for _, row in hasil.iterrows():
    try:
        coord = str(row["Koordinat"]).split(",")
        if len(coord) != 2:
            continue
        lat = float(coord[0])
        lon = float(coord[1])
        # Calculate distance from user location
        jarak_user = None
        if user_lat is not None and user_lon is not None:
            R = 6371
            dlat = math.radians(lat - user_lat)
            dlon = math.radians(lon - user_lon)
            a = math.sin(dlat/2)**2 + \
                math.cos(math.radians(user_lat)) * \
                math.cos(math.radians(lat)) * \
                math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            jarak_user = R * c
        heat_data.append([lat, lon, row["Magnitude"]])
        mag = row["Magnitude"]
        if mag >= 6:
            warna = "#e53935"
            border_color = "#ffcdd2"
            icon_emoji = "🚨"
        elif mag >= 5:
            warna = "#ff9800"
            border_color = "#ffe0b2"
            icon_emoji = "⚠️"
        elif mag >= 4:
            warna = "#fdd835"
            border_color = "#fff9c4"
            icon_emoji = "📍"
        else:
            warna = "#66bb6a"
            border_color = "#c8e6c9"
            icon_emoji = "📍"
        # Rich popup HTML with satellite link
        popup_html = f"""
        <div style="min-width: 260px; font-family: 'Inter', Arial, sans-serif; background: #0d1117; color: white; padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                <div style="background: {warna}; width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; box-shadow: 0 0 15px {warna}80;">{icon_emoji}</div>
                <div>
                    <div style="font-size: 1.3em; font-weight: 800; color: {warna};">M {mag}</div>
                    <div style="font-size: 0.75em; color: rgba(255,255,255,0.5);">{row['Tanggal']} {row['Jam']}</div>
                </div>
            </div>
            <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
                <div style="margin: 5px 0;"><span style="color: rgba(255,255,255,0.5);">📍 Wilayah</span><br><b>{row['Wilayah']}</b></div>
                <div style="margin: 5px 0;"><span style="color: rgba(255,255,255,0.5);">📏 Kedalaman</span><br><b>{row['Kedalaman']}</b></div>
                <div style="margin: 5px 0;"><span style="color: rgba(255,255,255,0.5);">🔊 Dirasakan</span><br><b>{row['Dirasakan']}</b></div>
                <div style="margin: 5px 0;"><span style="color: rgba(255,255,255,0.5);">🌐 Koordinat</span><br><b>{row['Koordinat']}</b></div>
            </div>
            <div style="margin: 5px 0;">
                <span style="color: rgba(255,255,255,0.5);">📍 Jarak dari Anda</span><br>
                <b>{round(jarak_user, 1) if jarak_user is not None else '-'} km</b>
            </div>
            <div style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
                <a href="https://www.google.com/maps/@{lat},{lon},14z/data=!3m1!1e1" target="_blank"
                   style="display: inline-block; background: #1565C0; color: white; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.82em; font-weight: 600;">
                    🛰️ Buka di Google Maps
                </a>
            </div>
        </div>
        """
        if show_markers:
            # Main circle marker with glow effect
            folium.CircleMarker(
                location=[lat, lon],
                radius=mag * 3,
                color=warna,
                fill=True,
                fill_color=warna,
                fill_opacity=0.75,
                weight=2,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"M {mag} — {row['Wilayah'][:35]}"
            ).add_to(cluster)
        # Animated epicenter rings for significant quakes
        if show_epicenter_rings and mag >= 4.0:
            ring_color = warna
            # Outer pulsing ring (larger, semi-transparent)
            folium.Circle(
                location=[lat, lon],
                radius=mag * 8000,  # Scale with magnitude
                color=ring_color,
                fill=False,
                weight=1.5,
                opacity=0.4,
                dash_array="8 6",
                tooltip=f"Zona dampak M {mag}"
            ).add_to(peta)
            # Inner solid ring
            folium.Circle(
                location=[lat, lon],
                radius=mag * 3000,
                color=ring_color,
                fill=True,
                fill_color=ring_color,
                fill_opacity=0.08,
                weight=1,
                opacity=0.6
            ).add_to(peta)
    except Exception:
        continue
# Heatmap
if show_heatmap and len(heat_data) > 0:
    HeatMap(
        heat_data,
        radius=22,
        blur=18,
        gradient={0.15: '#0d47a1', 0.3: '#1565c0', 0.45: '#43a047', 0.6: '#fdd835', 0.75: '#ff9800', 0.9: '#e53935', 1: '#b71c1c'},
        name="🔥 Heatmap Intensitas",
        min_opacity=0.35
    ).add_to(peta)
# Radius circle
if use_radius:
    folium.Circle(
        location=[radius_lat, radius_lon],
        radius=radius_km * 1000,
        color="#00bfff",
        fill=True,
        fill_opacity=0.06,
        weight=2,
        dash_array="10 5",
        popup=f"Radius pencarian: {radius_km} km",
        tooltip=f"Radius: {radius_km} km"
    ).add_to(peta)
    folium.Marker(
        location=[radius_lat, radius_lon],
        icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa"),
        popup="Pusat pencarian",
        tooltip="Pusat Radius"
    ).add_to(peta)
# Render map
st.markdown('<div class="map-container">', unsafe_allow_html=True)
st_folium(peta, width=None, height=700)
st.markdown('</div>', unsafe_allow_html=True)
# ==========================================
# DETAIL EVENT + SATELLITE ZOOM VIEW
# ==========================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>🔍 Detail Event & Peta Satelit Titik Sumber</h3></div>', unsafe_allow_html=True)
if len(hasil) > 0:
    pilih_options = [f"M {row['Magnitude']} — {row['Wilayah'][:45]} ({row['Tanggal']})" for _, row in hasil.iterrows()]
    pilih_idx = st.selectbox("Pilih Event untuk Detail Satelit", range(len(pilih_options)), format_func=lambda x: pilih_options[x])
    selected_event = hasil.iloc[pilih_idx]
    col_info, col_sat = st.columns([1, 2])
    with col_info:
        mag_color = "#e53935" if selected_event['Magnitude'] >= 6 else "#ff9800" if selected_event['Magnitude'] >= 5 else "#1565C0"
        st.markdown(f"""
        <div class="satellite-detail-card">
            <h3>🎯 Informasi Episenter</h3>
            <div style="text-align: center; margin: 15px 0;">
                <div style="display: inline-block; background: {mag_color}; width: 80px; height: 80px; border-radius: 50%;
                     display: flex; align-items: center; justify-content: center; margin: 0 auto;
                     box-shadow: 0 0 30px {mag_color}80; font-size: 1.6em; font-weight: 800; color: white;">
                    M {selected_event['Magnitude']}
                </div>
            </div>
            <div class="detail-row">
                <span class="label">📍 Wilayah</span>
                <span class="value">{selected_event['Wilayah'][:35]}</span>
            </div>
            <div class="detail-row">
                <span class="label">📏 Kedalaman</span>
                <span class="value">{selected_event['Kedalaman']}</span>
            </div>
            <div class="detail-row">
                <span class="label">📅 Tanggal</span>
                <span class="value">{selected_event['Tanggal']}</span>
            </div>
            <div class="detail-row">
                <span class="label">🕐 Jam</span>
                <span class="value">{selected_event['Jam']}</span>
            </div>
            <div class="detail-row">
                <span class="label">🌐 Koordinat</span>
                <span class="value">{selected_event['Koordinat']}</span>
            </div>
            <div class="detail-row">
                <span class="label">🔊 Dirasakan</span>
                <span class="value">{selected_event['Dirasakan']}</span>
            </div>
            <div class="detail-row" style="border-bottom: none;">
                <span class="label">⚠️ Potensi</span>
                <span class="value">{selected_event.get('Potensi', '-')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_sat:
        # Create a zoomed-in satellite map centered on the selected epicenter
        try:
            coord_parts = str(selected_event["Koordinat"]).split(",")
            ep_lat = float(coord_parts[0])
            ep_lon = float(coord_parts[1])
            sat_map = folium.Map(
                location=[ep_lat, ep_lon],
                zoom_start=10,
                tiles=TILE_ESRI_SATELLITE,
                attr=TILE_ESRI_ATTR
            )
            # Add Google Hybrid as alternative
            folium.TileLayer(tiles=TILE_GOOGLE_HYBRID, attr="Google", name="🛰️ Satelit + Label").add_to(sat_map)
            folium.TileLayer("OpenStreetMap", name="🗺️ Dasar").add_to(sat_map)
            folium.LayerControl(position="topright").add_to(sat_map)
            # Epicenter marker with dramatic styling
            mag_val = selected_event['Magnitude']
            ep_color = "#e53935" if mag_val >= 6 else "#ff9800" if mag_val >= 5 else "#fdd835" if mag_val >= 4 else "#66bb6a"
            # Outer glow ring
            folium.Circle(
                location=[ep_lat, ep_lon],
                radius=mag_val * 6000,
                color=ep_color,
                fill=True,
                fill_color=ep_color,
                fill_opacity=0.08,
                weight=2,
                opacity=0.5,
                dash_array="12 6"
            ).add_to(sat_map)
            # Mid ring
            folium.Circle(
                location=[ep_lat, ep_lon],
                radius=mag_val * 3000,
                color=ep_color,
                fill=True,
                fill_color=ep_color,
                fill_opacity=0.12,
                weight=1.5,
                opacity=0.7
            ).add_to(sat_map)
            # Center marker
            ep_icon_html = f"""
            <div style="
                background: {ep_color};
                width: 36px; height: 36px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 0 20px {ep_color}, 0 0 40px {ep_color}80;
                display: flex; align-items: center; justify-content: center;
                font-weight: 800; color: white; font-size: 11px;
                font-family: 'Inter', sans-serif;
            ">M{mag_val}</div>
            """
            folium.Marker(
                location=[ep_lat, ep_lon],
                icon=folium.DivIcon(
                    html=ep_icon_html,
                    icon_size=(36, 36),
                    icon_anchor=(18, 18)
                ),
                tooltip=f"Episenter M {mag_val} — {selected_event['Wilayah'][:30]}"
            ).add_to(sat_map)
            # Crosshair lines
            line_len = 0.15  # degrees
            folium.PolyLine(
                locations=[[ep_lat - line_len, ep_lon], [ep_lat + line_len, ep_lon]],
                color=ep_color, weight=1.5, opacity=0.6, dash_array="6 4"
            ).add_to(sat_map)
            folium.PolyLine(
                locations=[[ep_lat, ep_lon - line_len], [ep_lat, ep_lon + line_len]],
                color=ep_color, weight=1.5, opacity=0.6, dash_array="6 4"
            ).add_to(sat_map)
            st.markdown("**🛰️ Peta Satelit — Titik Sumber Gempa (Zoom In)**")
            st_folium(sat_map, width=None, height=500, key="detail_sat_map")
        except Exception as e:
            st.warning(f"Tidak dapat menampilkan peta satelit detail: {e}")
    with st.expander("📄 Data JSON Lengkap"):
        st.json(selected_event.to_dict())
# ==========================================
# GRAFIK MAGNITUDO
# ==========================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>📈 Grafik Magnitudo</h3></div>', unsafe_allow_html=True)
if len(hasil) > 0:
    grafik = hasil[["Wilayah", "Magnitude"]].copy()
    grafik["Wilayah"] = grafik["Wilayah"].str[:40]
    grafik = grafik.set_index("Wilayah")
    st.bar_chart(grafik)
# ==========================================
# WILAYAH PALING AKTIF
# ==========================================
st.markdown('<div class="section-header"><h3>🔥 Wilayah Paling Aktif</h3></div>', unsafe_allow_html=True)
if len(hasil) > 0:
    st.bar_chart(hasil["Wilayah"].value_counts().head(10))
# ==========================================
# DISTRIBUSI KEDALAMAN
# ==========================================
st.markdown('<div class="section-header"><h3>📏 Distribusi Kedalaman Gempa</h3></div>', unsafe_allow_html=True)
if len(hasil) > 0:
    depth_data = hasil.copy()
    depth_data["Kedalaman_num"] = depth_data["Kedalaman"].apply(parse_kedalaman)
    depth_data = depth_data.dropna(subset=["Kedalaman_num"])
    if len(depth_data) > 0:
        depth_chart = depth_data[["Wilayah", "Kedalaman_num"]].copy()
        depth_chart.columns = ["Wilayah", "Kedalaman (km)"]
        depth_chart["Wilayah"] = depth_chart["Wilayah"].str[:40]
        depth_chart = depth_chart.set_index("Wilayah")
        st.bar_chart(depth_chart)
# ==========================================
# DATA GEMPA TABLE
# ==========================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>📋 Data Gempa</h3></div>', unsafe_allow_html=True)
filter_info = []
if provinsi_pilihan != "Semua Provinsi":
    filter_info.append(f"📍 Provinsi: {provinsi_pilihan}")
if kota_input:
    filter_info.append(f"🔍 Kota: {kota_input}")
if min_mag > 0:
    filter_info.append(f"📈 Min M: {min_mag}")
if max_mag < 10:
    filter_info.append(f"📉 Max M: {max_mag}")
if kedalaman_filter != "Semua":
    filter_info.append(f"📏 Kedalaman: {kedalaman_filter}")
if use_radius:
    filter_info.append(f"📐 Radius: {radius_km}km dari ({radius_lat}, {radius_lon})")
if filter_info:
    st.caption("Filter aktif: " + " | ".join(filter_info))
st.dataframe(hasil, use_container_width=True, height=400)
# ==========================================
# DOWNLOAD
# ==========================================
st.markdown("---")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    csv = hasil.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "gempa_bmkg.csv", "text/csv")
with col_dl2:
    json_data = hasil.to_json(orient="records", force_ascii=False).encode("utf-8")
    st.download_button("📥 Download JSON", json_data, "gempa_bmkg.json", "application/json")
# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px 0; color: rgba(255,255,255,0.4); font-size: 0.85em;">
    <p style="margin: 0;">🌍 <b>SeismoTrack Indonesia</b> — Sistem Monitoring Gempa Bumi Real-Time</p>
    <p style="margin: 5px 0 0 0;">Data bersumber dari <a href="https://data.bmkg.go.id/" target="_blank" style="color: #58a6ff;">BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)</a></p>
    <p style="margin: 5px 0 0 0; font-size: 0.9em;">⚠️ Aplikasi ini bukan pengganti informasi resmi BMKG. Selalu ikuti arahan resmi saat terjadi gempa.</p>
</div>
""", unsafe_allow_html=True)
