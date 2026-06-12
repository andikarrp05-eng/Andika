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
# ==========================================
# CONFIG
# ==========================================
st.set_page_config(
    page_title="SeismoTrack Indonesia",
    page_icon="🌍",
    layout="wide"
)
# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    /* Notifikasi gempa styling */
    .gempa-alert {
        background: linear-gradient(135deg, #ff0000, #cc0000);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 6px solid #ffcc00;
        animation: pulse-alert 2s infinite;
        box-shadow: 0 4px 15px rgba(255, 0, 0, 0.4);
    }
    .gempa-alert-warning {
        background: linear-gradient(135deg, #ff8c00, #cc7000);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 6px solid #ffcc00;
        animation: pulse-warning 3s infinite;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3);
    }
    .gempa-alert-info {
        background: linear-gradient(135deg, #2196F3, #1976D2);
        color: white;
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 6px solid #64B5F6;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
    }
    @keyframes pulse-alert {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.01); opacity: 0.9; }
    }
    @keyframes pulse-warning {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.005); opacity: 0.95; }
    }
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
# HEADER
# ==========================================
st.title("🌍 SeismoTrack Indonesia")
st.markdown("""
### Sistem Monitoring Gempa Bumi Indonesia
📡 Data Realtime BMKG | 🔔 Notifikasi & Alarm Peringatan | 🗺️ Multi-Mode Peta
---
""")
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
URL_M5 = "https://data.bmkg.go.id/DataMKG/TEWS/gempa_m5.json"  # Backup M5+ endpoint
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
# Pilihan provinsi
provinsi_pilihan = st.sidebar.selectbox(
    "📍 Pilih Provinsi",
    PROVINSI_INDONESIA,
    index=0
)
# Pencarian kota/daerah spesifik
kota_input = st.sidebar.text_input(
    "🔍 Cari Kota / Daerah",
    "",
    placeholder="Contoh: Padang, Lombok, Ternate..."
)
# Pencarian radius dari koordinat tertentu
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
min_mag = st.sidebar.slider(
    "Minimal Magnitudo",
    0.0, 10.0, 0.0, 0.1
)
max_mag = st.sidebar.slider(
    "Maksimal Magnitudo",
    0.0, 10.0, 10.0, 0.1
)
# Filter kedalaman
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
    "Ambang Magnitudo Alarm",
    3.0, 9.0, 5.0, 0.5,
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
    "Mode Peta",
    ["🌑 Mode Gelap (Dark)", "🗺️ Mode Dasar (Street)", "🛰️ Mode Satelit"],
    index=0
)
show_heatmap = st.sidebar.checkbox("🔥 Tampilkan Heatmap", value=True)
show_markers = st.sidebar.checkbox("📍 Tampilkan Marker", value=True)
# ==========================================
# APPLY FILTER
# ==========================================
hasil = df.copy()
# Filter magnitudo
hasil = hasil[(hasil["Magnitude"] >= min_mag) & (hasil["Magnitude"] <= max_mag)]
# Filter kedalaman
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
# Filter provinsi
if provinsi_pilihan != "Semua Provinsi":
    keywords = KEYWORD_WILAYAH.get(provinsi_pilihan, [provinsi_pilihan.lower()])
    mask = pd.Series([False] * len(hasil), index=hasil.index)
    for kw in keywords:
        mask = mask | hasil["Wilayah"].str.contains(kw, case=False, na=False)
    hasil = hasil[mask]
# Filter kota/daerah
if kota_input:
    kota_keywords = [k.strip() for k in kota_input.split(",")]
    mask = pd.Series([False] * len(hasil), index=hasil.index)
    for kw in kota_keywords:
        if kw:
            mask = mask | hasil["Wilayah"].str.contains(kw, case=False, na=False)
    hasil = hasil[mask]
# Filter radius
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
st.subheader("🔔 Notifikasi Peringatan Gempa")
if len(hasil) > 0:
    # Cek semua gempa yang melebihi ambang
    gempa_bahaya = hasil[hasil["Magnitude"] >= notif_threshold]
    if len(gempa_bahaya) > 0:
        event_terbesar = gempa_bahaya.loc[gempa_bahaya["Magnitude"].idxmax()]
        mag_terbesar = float(event_terbesar["Magnitude"])
        # === ALARM LEVEL: BESAR (M >= 6.0) ===
        if mag_terbesar >= 6.0 and enable_visual:
            st.markdown(f"""
            <div class="gempa-alert">
                <h2>🚨 PERINGATAN GEMPA BESAR!</h2>
                <p><b>📍 Lokasi:</b> {event_terbesar['Wilayah']}</p>
                <p><b>📈 Magnitudo:</b> M {mag_terbesar}</p>
                <p><b>📏 Kedalaman:</b> {event_terbesar['Kedalaman']}</p>
                <p><b>📅 Waktu:</b> {event_terbesar['Tanggal']} {event_terbesar['Jam']}</p>
                <p><b>🔊 Dirasakan:</b> {event_terbesar['Dirasakan']}</p>
                <p><b>⚠️ Potensi:</b> {event_terbesar.get('Potensi', '-')}</p>
                <hr>
                <p>⚠️ <b>SEGERA cek informasi resmi BMKG dan ikuti prosedur evakuasi!</b></p>
            </div>
            """, unsafe_allow_html=True)
        # === ALARM LEVEL: SEDANG (M >= 5.0) ===
        elif mag_terbesar >= 5.0 and enable_visual:
            st.markdown(f"""
            <div class="gempa-alert-warning">
                <h2>⚠️ PERINGATAN GEMPA SIGNIFIKAN</h2>
                <p><b>📍 Lokasi:</b> {event_terbesar['Wilayah']}</p>
                <p><b>📈 Magnitudo:</b> M {mag_terbesar}</p>
                <p><b>📏 Kedalaman:</b> {event_terbesar['Kedalaman']}</p>
                <p><b>📅 Waktu:</b> {event_terbesar['Tanggal']} {event_terbesar['Jam']}</p>
                <p><b>🔊 Dirasakan:</b> {event_terbesar['Dirasakan']}</p>
                <hr>
                <p>📢 Tetap waspada dan pantau informasi BMKG.</p>
            </div>
            """, unsafe_allow_html=True)
        # === ALARM LEVEL: RINGAN (M >= threshold) ===
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
            # Buat alarm suara menggunakan JavaScript audio oscillator
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
            # JavaScript-based alarm sound (no external file needed)
            alarm_js = f"""
            <div id="alarm-control" style="margin: 10px 0;">
                <button onclick="playAlarm()" style="
                    background: {'#ff0000' if alarm_type == 'danger' else '#ff8c00' if alarm_type == 'warning' else '#2196F3'};
                    color: white; border: none; padding: 12px 24px; border-radius: 8px;
                    cursor: pointer; font-size: 16px; font-weight: bold;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    transition: transform 0.2s;
                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    🔊 Putar Alarm
                </button>
                <button onclick="stopAlarm()" style="
                    background: #333; color: white; border: none; padding: 12px 24px;
                    border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold;
                    margin-left: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    transition: transform 0.2s;
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
                        // Siren alternating two-tone
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
                        // Three-beep pattern
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
                        // Simple notification beeps
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
        # Ringkasan semua gempa yang memicu notifikasi
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
# DASHBOARD
# ==========================================
st.markdown("---")
st.subheader("📊 Dashboard")
col1, col2, col3, col4 = st.columns(4)
if len(hasil) > 0:
    col1.metric("📌 Total Event", len(hasil))
    col2.metric("📈 Magnitudo Maks", round(hasil["Magnitude"].max(), 2))
    col3.metric("📊 Rata-rata Magnitudo", round(hasil["Magnitude"].mean(), 2))
    wilayah_counts = hasil["Wilayah"].value_counts()
    wilayah_aktif = wilayah_counts.index[0] if len(wilayah_counts) > 0 else "-"
    col4.metric("🔥 Wilayah Aktif", wilayah_aktif[:25])
else:
    col1.metric("📌 Total Event", 0)
    col2.metric("📈 Magnitudo Maks", "-")
    col3.metric("📊 Rata-rata Magnitudo", "-")
    col4.metric("🔥 Wilayah Aktif", "-")
    st.warning("Tidak ada data yang sesuai dengan filter.")
# ==========================================
# PETA GEMPA MULTI-MODE
# ==========================================
st.markdown("---")
st.subheader("🗺️ Peta Gempa Indonesia")
# Tentukan tile layer berdasarkan pilihan
if peta_mode == "🌑 Mode Gelap (Dark)":
    tile_name = "CartoDB dark_matter"
    tile_url = None
    tile_attr = None
elif peta_mode == "🗺️ Mode Dasar (Street)":
    tile_name = "OpenStreetMap"
    tile_url = None
    tile_attr = None
else:  # Satelit
    tile_name = None
    tile_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    tile_attr = "Esri, Maxar, Earthstar Geographics, CNES/Airbus DS, USDA FSA, USGS, AeroGRID, IGN, GIS User Community"
# Tentukan center peta berdasarkan filter radius
if use_radius:
    map_center = [radius_lat, radius_lon]
    map_zoom = 7
else:
    map_center = [-2.5, 118]
    map_zoom = 5
if tile_url:
    peta = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles=tile_url,
        attr=tile_attr
    )
else:
    peta = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles=tile_name
    )
# Tambahkan layer controls untuk switching mode
folium.TileLayer("OpenStreetMap", name="🗺️ Dasar").add_to(peta)
folium.TileLayer("CartoDB dark_matter", name="🌑 Gelap").add_to(peta)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="🛰️ Satelit"
).add_to(peta)
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attr="Google",
    name="🛰️ Satelit + Label"
).add_to(peta)
# Layer control
folium.LayerControl(position="topright").add_to(peta)
# Marker & Heatmap
cluster = MarkerCluster(name="📍 Marker Gempa").add_to(peta)
heat_data = []
for _, row in hasil.iterrows():
    try:
        coord = str(row["Koordinat"]).split(",")
        if len(coord) != 2:
            continue
        lat = float(coord[0])
        lon = float(coord[1])
        heat_data.append([lat, lon, row["Magnitude"]])
        if row["Magnitude"] >= 6:
            warna = "red"
            ikon = "exclamation-triangle"
        elif row["Magnitude"] >= 5:
            warna = "orange"
            ikon = "warning"
        elif row["Magnitude"] >= 4:
            warna = "beige"
            ikon = "info-sign"
        else:
            warna = "green"
            ikon = "ok-sign"
        popup_html = f"""
        <div style="min-width: 220px; font-family: Arial;">
            <h4 style="margin: 0 0 8px 0; color: {'#ff0000' if row['Magnitude'] >= 6 else '#ff8c00' if row['Magnitude'] >= 5 else '#2196F3'};">
                {'🚨' if row['Magnitude'] >= 6 else '⚠️' if row['Magnitude'] >= 5 else '📍'} M {row['Magnitude']}
            </h4>
            <b>Wilayah:</b> {row['Wilayah']}<br>
            <b>Kedalaman:</b> {row['Kedalaman']}<br>
            <b>Tanggal:</b> {row['Tanggal']}<br>
            <b>Jam:</b> {row['Jam']}<br>
            <b>Dirasakan:</b> {row['Dirasakan']}<br>
            <b>Koordinat:</b> {row['Koordinat']}
        </div>
        """
        if show_markers:
            folium.CircleMarker(
                location=[lat, lon],
                radius=row["Magnitude"] * 2.5,
                color=warna if warna != "beige" else "#DAA520",
                fill=True,
                fill_color=warna if warna != "beige" else "#DAA520",
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"M {row['Magnitude']} - {row['Wilayah'][:30]}"
            ).add_to(cluster)
    except Exception:
        pass
# Tambahkan heatmap
if show_heatmap and len(heat_data) > 0:
    HeatMap(
        heat_data,
        radius=20,
        blur=15,
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'},
        name="🔥 Heatmap"
    ).add_to(peta)
# Tampilkan radius circle jika aktif
if use_radius:
    folium.Circle(
        location=[radius_lat, radius_lon],
        radius=radius_km * 1000,
        color="#00bfff",
        fill=True,
        fill_opacity=0.08,
        popup=f"Radius pencarian: {radius_km} km",
        tooltip=f"Radius: {radius_km} km"
    ).add_to(peta)
    folium.Marker(
        location=[radius_lat, radius_lon],
        icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa"),
        popup="Pusat pencarian",
        tooltip="Pusat Radius"
    ).add_to(peta)
st_folium(peta, width=None, height=650)
# ==========================================
# GRAFIK MAGNITUDO
# ==========================================
st.markdown("---")
st.subheader("📈 Grafik Magnitudo")
if len(hasil) > 0:
    grafik = hasil[["Wilayah", "Magnitude"]].copy()
    grafik["Wilayah"] = grafik["Wilayah"].str[:40]
    grafik = grafik.set_index("Wilayah")
    st.bar_chart(grafik)
# ==========================================
# WILAYAH PALING AKTIF
# ==========================================
st.subheader("🔥 Wilayah Paling Aktif")
if len(hasil) > 0:
    st.bar_chart(
        hasil["Wilayah"].value_counts().head(10)
    )
# ==========================================
# DISTRIBUSI KEDALAMAN
# ==========================================
st.subheader("📏 Distribusi Kedalaman Gempa")
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
# DATA GEMPA
# ==========================================
st.markdown("---")
st.subheader("📋 Data Gempa")
# Info filter aktif
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
st.dataframe(
    hasil,
    use_container_width=True,
    height=400
)
# ==========================================
# DETAIL EVENT
# ==========================================
st.subheader("🔍 Detail Event")
if len(hasil) > 0:
    pilih_options = [f"M {row['Magnitude']} - {row['Wilayah'][:40]} ({row['Tanggal']})" for _, row in hasil.iterrows()]
    pilih_idx = st.selectbox("Pilih Event", range(len(pilih_options)), format_func=lambda x: pilih_options[x])
    selected_event = hasil.iloc[pilih_idx]
    col_detail1, col_detail2 = st.columns(2)
    with col_detail1:
        st.markdown(f"""
        **📍 Wilayah:** {selected_event['Wilayah']}
        **📈 Magnitudo:** M {selected_event['Magnitude']}
        **📏 Kedalaman:** {selected_event['Kedalaman']}
        **🌐 Koordinat:** {selected_event['Koordinat']}
        """)
    with col_detail2:
        st.markdown(f"""
        **📅 Tanggal:** {selected_event['Tanggal']}
        **🕐 Jam:** {selected_event['Jam']}
        **🔊 Dirasakan:** {selected_event['Dirasakan']}
        **⚠️ Potensi:** {selected_event.get('Potensi', '-')}
        """)
    with st.expander("📄 Data JSON Lengkap"):
        st.json(selected_event.to_dict())
# ==========================================
# DOWNLOAD CSV
# ==========================================
st.markdown("---")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    csv = hasil.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download CSV",
        csv,
        "gempa_bmkg.csv",
        "text/csv"
    )
with col_dl2:
    json_data = hasil.to_json(orient="records", force_ascii=False).encode("utf-8")
    st.download_button(
        "📥 Download JSON",
        json_data,
        "gempa_bmkg.json",
        "application/json"
    )
# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption(
    "SeismoTrack Indonesia v3.0 | BMKG Realtime | Notifikasi & Alarm | Multi-Mode Peta | Streamlit"
)
