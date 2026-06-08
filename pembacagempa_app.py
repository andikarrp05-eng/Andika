/* ============================================
   INDONESIA EARTHQUAKE MONITORING SYSTEM
   Main Application Script
   ============================================ */
// ===== CONFIGURATION =====
const CONFIG = {
    API: {
        AUTO_GEMPA: 'https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json',
        GEMPA_TERKINI: 'https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json',
        GEMPA_DIRASAKAN: 'https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json',
        SHAKEMAP_BASE: 'https://data.bmkg.go.id/DataMKG/TEWS/',
    },
    REFRESH_INTERVAL: 30000, // 30 seconds
    MAP: {
        CENTER: [-2.5, 118.0],
        ZOOM: 5,
        MIN_ZOOM: 4,
        MAX_ZOOM: 12,
    },
    REGIONS: {
        'all': { center: [-2.5, 118.0], zoom: 5, name: 'Seluruh Indonesia' },
        'sumatra': { center: [0.5, 101.5], zoom: 6, name: 'Sumatra' },
        'jawa': { center: [-7.0, 110.0], zoom: 7, name: 'Jawa' },
        'bali': { center: [-8.3, 115.2], zoom: 9, name: 'Bali' },
        'nusa-tenggara': { center: [-9.0, 119.0], zoom: 7, name: 'Nusa Tenggara' },
        'kalimantan': { center: [0.5, 116.0], zoom: 6, name: 'Kalimantan' },
        'sulawesi': { center: [-2.0, 121.0], zoom: 6, name: 'Sulawesi' },
        'maluku': { center: [-3.0, 129.5], zoom: 7, name: 'Maluku' },
        'papua': { center: [-4.0, 138.5], zoom: 7, name: 'Papua' },
    },
    ALARM: {
        WARNING_THRESHOLD: 5.0,
        DANGER_THRESHOLD: 6.0,
        EMERGENCY_THRESHOLD: 7.0,
    }
};
// ===== STATE =====
const state = {
    autoGempa: null,
    gempaTerkini: [],
    gempaDirasakan: [],
    allEarthquakes: [],
    lastKnownQuakeId: null,
    isMuted: false,
    alarmVolume: 0.7,
    refreshTimer: null,
    countdownTimer: null,
    countdown: 30,
    charts: {},
    miniMap: null,
    mainMap: null,
    miniMapMarkers: [],
    mainMapMarkers: [],
    alertLog: [],
    activeTab: 'dashboard',
    historyPeriod: 'today',
    isOnline: navigator.onLine,
    audioContext: null,
};
// ===== AUDIO ENGINE =====
class AudioEngine {
    constructor() {
        this.ctx = null;
        this.initialized = false;
    }
    init() {
        if (this.initialized) return;
        try {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
            this.initialized = true;
        } catch (e) {
            console.warn('AudioContext not available:', e);
        }
    }
    playTone(frequency, duration, type = 'sine', volume = 0.5) {
        if (!this.initialized || state.isMuted) return;
        this.init();
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.type = type;
        osc.frequency.setValueAtTime(frequency, this.ctx.currentTime);
        gain.gain.setValueAtTime(volume * state.alarmVolume, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
        osc.start(this.ctx.currentTime);
        osc.stop(this.ctx.currentTime + duration);
    }
    playWarning() {
        this.init();
        [0, 0.3, 0.6].forEach(delay => {
            setTimeout(() => this.playTone(880, 0.25, 'sine', 0.4), delay * 1000);
        });
    }
    playDanger() {
        this.init();
        for (let i = 0; i < 6; i++) {
            setTimeout(() => this.playTone(i % 2 ? 1200 : 800, 0.2, 'square', 0.5), i * 200);
        }
    }
    playEmergency() {
        this.init();
        const play = () => {
            for (let i = 0; i < 10; i++) {
                setTimeout(() => {
                    this.playTone(i % 2 ? 1500 : 600, 0.15, 'sawtooth', 0.6);
                }, i * 150);
            }
        };
        play();
        setTimeout(play, 1600);
        setTimeout(play, 3200);
    }
}
const audio = new AudioEngine();
// ===== UTILITY FUNCTIONS =====
function parseMagnitude(str) {
    return parseFloat(str) || 0;
}
function parseDepth(str) {
    return parseInt(str) || 0;
}
function parseCoordinates(str) {
    const parts = str.split(',');
    return {
        lat: parseFloat(parts[0]) || 0,
        lng: parseFloat(parts[1]) || 0,
    };
}
function getMagnitudeColor(mag) {
    if (mag < 3) return { bg: '#22c55e', cls: 'mag-low', label: 'green' };
    if (mag < 5) return { bg: '#eab308', cls: 'mag-medium', label: 'yellow' };
    if (mag < 6) return { bg: '#f97316', cls: 'mag-high', label: 'orange' };
    return { bg: '#ef4444', cls: 'mag-extreme', label: 'red' };
}
function formatTimeAgo(dateStr) {
    const now = new Date();
    const then = new Date(dateStr);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffMins < 1) return 'Baru saja';
    if (diffMins < 60) return `${diffMins} menit lalu`;
    if (diffHours < 24) return `${diffHours} jam lalu`;
    return `${diffDays} hari lalu`;
}
function generateQuakeId(quake) {
    return `${quake.DateTime}_${quake.Coordinates}_${quake.Magnitude}`;
}
function isTodayQuake(dateStr) {
    const quakeDate = new Date(dateStr);
    const today = new Date();
    return quakeDate.toDateString() === today.toDateString();
}
function isWithinDays(dateStr, days) {
    const quakeDate = new Date(dateStr);
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    return quakeDate >= cutoff;
}
function hasTsunamiPotential(quake) {
    const potensi = (quake.Potensi || '').toLowerCase();
    return potensi.includes('berpotensi tsunami') && !potensi.includes('tidak berpotensi');
}
function getRegionFromWilayah(wilayah) {
    const w = wilayah.toUpperCase();
    if (w.includes('SUMUT') || w.includes('SUMBAR') || w.includes('SUMSEL') || w.includes('ACEH') || w.includes('RIAU') || w.includes('JAMBI') || w.includes('BENGKULU') || w.includes('LAMPUNG') || w.includes('BABEL') || w.includes('KEPRI') || w.includes('SUMATERA') || w.includes('NIAS') || w.includes('MENTAWAI') || w.includes('PADANG') || w.includes('MEDAN') || w.includes('MANDAILING') || w.includes('SIMEULUE') || w.includes('SINABANG') || w.includes('BENER MERIAH') || w.includes('TAKENGON') || w.includes('TANGGAMUS')) return 'sumatra';
    if (w.includes('JABAR') || w.includes('JATENG') || w.includes('JATIM') || w.includes('DKI') || w.includes('BANTEN') || w.includes('DIY') || w.includes('JAWA') || w.includes('CIANJUR') || w.includes('PANGANDARAN') || w.includes('SUKABUMI')) return 'jawa';
    if (w.includes('BALI') || w.includes('DENPASAR')) return 'bali';
    if (w.includes('NTT') || w.includes('NTB') || w.includes('LOMBOK') || w.includes('FLORES') || w.includes('SUMBA') || w.includes('TIMOR') || w.includes('LABUANBAJO') || w.includes('NUSA TENGGARA')) return 'nusa-tenggara';
    if (w.includes('KALBAR') || w.includes('KALTENG') || w.includes('KALSEL') || w.includes('KALTIM') || w.includes('KALTARA') || w.includes('KALIMANTAN')) return 'kalimantan';
    if (w.includes('SULUT') || w.includes('SULTENG') || w.includes('SULSEL') || w.includes('SULTRA') || w.includes('GORONTALO') || w.includes('SULBAR') || w.includes('SULAWESI') || w.includes('MANADO') || w.includes('PALU') || w.includes('BITUNG') || w.includes('SANGIHE') || w.includes('TAHUNA') || w.includes('KARATUNG') || w.includes('MONGONDOW') || w.includes('MINAHASA') || w.includes('TUTUYAN') || w.includes('BOLTIM') || w.includes('TOLI-TOLI') || w.includes('PARIGI MOUTONG')) return 'sulawesi';
    if (w.includes('MALUKU') || w.includes('AMBON') || w.includes('HALMAHERA') || w.includes('TERNATE') || w.includes('TIAKUR') || w.includes('MOROTAI') || w.includes('TALIABU') || w.includes('BOBONG') || w.includes('BATANG DUA')) return 'maluku';
    if (w.includes('PAPUA') || w.includes('JAYAPURA') || w.includes('SORONG') || w.includes('MANOKWARI') || w.includes('MERAUKE')) return 'papua';
    return 'all';
}
// ===== CLOCK =====
function updateClock() {
    const now = new Date();
    const wib = new Date(now.getTime() + (7 * 60 - now.getTimezoneOffset()) * 60000);
    const h = String(wib.getUTCHours()).padStart(2, '0');
    const m = String(wib.getUTCMinutes()).padStart(2, '0');
    const s = String(wib.getUTCSeconds()).padStart(2, '0');
    document.getElementById('header-clock').textContent = `${h}:${m}:${s} WIB`;
}
// ===== API FETCHING =====
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch ${url}:`, error);
        return null;
    }
}
async function loadAllData() {
    updateConnectionStatus(true);
    const [autoData, terkiniData, dirasakanData] = await Promise.all([
        fetchData(CONFIG.API.AUTO_GEMPA),
        fetchData(CONFIG.API.GEMPA_TERKINI),
        fetchData(CONFIG.API.GEMPA_DIRASAKAN),
    ]);
    let dataLoaded = false;
    if (autoData?.Infogempa?.gempa) {
        state.autoGempa = autoData.Infogempa.gempa;
        dataLoaded = true;
    }
    if (terkiniData?.Infogempa?.gempa) {
        state.gempaTerkini = terkiniData.Infogempa.gempa;
        dataLoaded = true;
    }
    if (dirasakanData?.Infogempa?.gempa) {
        state.gempaDirasakan = dirasakanData.Infogempa.gempa;
        dataLoaded = true;
    }
    if (dataLoaded) {
        // Merge all earthquakes (deduplicate by DateTime+Coordinates)
        const allQuakes = new Map();
        if (state.autoGempa) {
            const id = generateQuakeId(state.autoGempa);
            allQuakes.set(id, { ...state.autoGempa, source: 'auto' });
        }
        state.gempaTerkini.forEach(q => {
            const id = generateQuakeId(q);
            if (!allQuakes.has(id)) allQuakes.set(id, { ...q, source: 'terkini' });
        });
        state.gempaDirasakan.forEach(q => {
            const id = generateQuakeId(q);
            if (!allQuakes.has(id)) {
                allQuakes.set(id, { ...q, source: 'dirasakan' });
            } else {
                // Merge Dirasakan info
                const existing = allQuakes.get(id);
                if (q.Dirasakan) existing.Dirasakan = q.Dirasakan;
            }
        });
        state.allEarthquakes = Array.from(allQuakes.values())
            .sort((a, b) => new Date(b.DateTime) - new Date(a.DateTime));
        // Check for new earthquake alerts
        checkAlerts();
        // Update all views
        updateDashboard();
        updateMaps();
        updateAlertCenter();
        updateStatistics();
        updateHistory();
        // Update timestamp
        const now = new Date();
        const timeStr = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        document.getElementById('last-update').textContent = timeStr;
        document.getElementById('alert-last-update').textContent = timeStr;
    } else {
        updateConnectionStatus(false);
    }
}
// ===== CONNECTION STATUS =====
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    const dot = statusEl.querySelector('.conn-dot');
    const text = statusEl.querySelector('.conn-text');
    if (connected) {
        dot.className = 'conn-dot connected';
        text.textContent = 'BMKG Connected';
    } else {
        dot.className = 'conn-dot disconnected';
        text.textContent = 'Disconnected';
    }
}
// ===== ALERT CHECKING =====
function checkAlerts() {
    if (!state.autoGempa) return;
    const currentId = generateQuakeId(state.autoGempa);
    if (currentId === state.lastKnownQuakeId) return;
    state.lastKnownQuakeId = currentId;
    const mag = parseMagnitude(state.autoGempa.Magnitude);
    if (mag >= CONFIG.ALARM.EMERGENCY_THRESHOLD) {
        triggerEmergency(state.autoGempa);
    } else if (mag >= CONFIG.ALARM.DANGER_THRESHOLD) {
        triggerDangerAlarm(state.autoGempa);
    } else if (mag >= CONFIG.ALARM.WARNING_THRESHOLD) {
        triggerWarning(state.autoGempa);
    }
}
function triggerWarning(quake) {
    audio.playWarning();
    addAlertLog('warning', `⚠️ Gempa M${quake.Magnitude} — ${quake.Wilayah}`);
    updateAlarmStatus('PERINGATAN', 'warning');
    // Show notification
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('⚠️ Peringatan Gempa', {
            body: `Gempa M${quake.Magnitude} — ${quake.Wilayah}`,
            icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">⚠️</text></svg>',
        });
    }
}
function triggerDangerAlarm(quake) {
    audio.playDanger();
    addAlertLog('danger', `🔊 ALARM: Gempa M${quake.Magnitude} — ${quake.Wilayah}`);
    updateAlarmStatus('ALARM AKTIF', 'danger');
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('🔊 ALARM Gempa Besar!', {
            body: `Gempa M${quake.Magnitude} — ${quake.Wilayah}`,
            requireInteraction: true,
        });
    }
}
function triggerEmergency(quake) {
    audio.playEmergency();
    addAlertLog('emergency', `🚨 DARURAT: Gempa M${quake.Magnitude} — ${quake.Wilayah}`);
    updateAlarmStatus('DARURAT', 'emergency');
    // Show emergency overlay
    const overlay = document.getElementById('emergency-overlay');
    const details = document.getElementById('emergency-details');
    details.innerHTML = `
        <p><strong>Magnitudo:</strong> ${quake.Magnitude}</p>
        <p><strong>Kedalaman:</strong> ${quake.Kedalaman}</p>
        <p><strong>Wilayah:</strong> ${quake.Wilayah}</p>
        <p><strong>Waktu:</strong> ${quake.Tanggal} ${quake.Jam}</p>
        <p><strong>Tsunami:</strong> ${quake.Potensi || '-'}</p>
    `;
    overlay.classList.remove('hidden');
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('🚨 DARURAT — Gempa Sangat Besar!', {
            body: `Gempa M${quake.Magnitude} — ${quake.Wilayah}`,
            requireInteraction: true,
        });
    }
}
function updateAlarmStatus(text, level) {
    const el = document.getElementById('alarm-status');
    el.textContent = text;
    el.className = `status-value ${level}`;
    // Auto-reset after 60 seconds
    setTimeout(() => {
        el.textContent = 'NORMAL';
        el.className = 'status-value';
    }, 60000);
}
function addAlertLog(level, message) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
    state.alertLog.unshift({ time: timeStr, message, level });
    if (state.alertLog.length > 50) state.alertLog.pop();
    renderAlertLog();
}
function renderAlertLog() {
    const container = document.getElementById('alert-log');
    if (state.alertLog.length === 0) {
        container.innerHTML = '<p class="empty-log">Belum ada peringatan</p>';
        return;
    }
    container.innerHTML = state.alertLog.map(log => `
        <div class="alert-log-item level-${log.level}">
            <span class="alert-log-time">${log.time}</span>
            <span class="alert-log-msg">${log.message}</span>
        </div>
    `).join('');
}
// ===== DASHBOARD UPDATE =====
function updateDashboard() {
    // Summary cards
    const todayQuakes = state.allEarthquakes.filter(q => isTodayQuake(q.DateTime));
    document.getElementById('total-today').textContent = todayQuakes.length;
    const biggestToday = todayQuakes.reduce((max, q) => {
        const mag = parseMagnitude(q.Magnitude);
        return mag > max ? mag : max;
    }, 0);
    document.getElementById('biggest-today').textContent = biggestToday > 0 ? `M ${biggestToday.toFixed(1)}` : '-';
    if (state.autoGempa) {
        document.getElementById('latest-quake').textContent = `M ${state.autoGempa.Magnitude}`;
    }
    const tsunamiQuakes = state.allEarthquakes.filter(q => hasTsunamiPotential(q));
    const tsunamiEl = document.getElementById('tsunami-status');
    if (tsunamiQuakes.length > 0) {
        tsunamiEl.textContent = `${tsunamiQuakes.length} PERINGATAN`;
        tsunamiEl.style.color = '#ef4444';
    } else {
        tsunamiEl.textContent = 'AMAN';
        tsunamiEl.style.color = '#22c55e';
    }
    // Latest earthquake detail
    if (state.autoGempa) {
        renderLatestDetail(state.autoGempa);
    }
    // Recent earthquakes list
    renderQuakeList('recent-list', state.gempaTerkini, 'recent-count');
    // Felt earthquakes list
    renderQuakeList('felt-list', state.gempaDirasakan, 'felt-count');
}
function renderLatestDetail(quake) {
    const mag = parseMagnitude(quake.Magnitude);
    const magColor = getMagnitudeColor(mag);
    const coords = parseCoordinates(quake.Coordinates);
    const isTsunami = hasTsunamiPotential(quake);
    document.getElementById('latest-detail').innerHTML = `
        <div class="quake-detail">
            <div class="quake-magnitude-display">
                <div class="magnitude-circle ${magColor.cls}">${mag.toFixed(1)}</div>
                <div class="quake-location-info">
                    <h3>${quake.Wilayah}</h3>
                    <p>${quake.Tanggal} — ${quake.Jam}</p>
                    <p>${formatTimeAgo(quake.DateTime)}</p>
                </div>
            </div>
            <div class="quake-meta-grid">
                <div class="meta-item">
                    <span class="meta-label">Magnitudo</span>
                    <span class="meta-value">${quake.Magnitude} SR</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Kedalaman</span>
                    <span class="meta-value">${quake.Kedalaman}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Latitude</span>
                    <span class="meta-value">${coords.lat.toFixed(4)}°</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Longitude</span>
                    <span class="meta-value">${coords.lng.toFixed(4)}°</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Lintang</span>
                    <span class="meta-value">${quake.Lintang}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Bujur</span>
                    <span class="meta-value">${quake.Bujur}</span>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <span class="meta-label" style="display:block; margin-bottom:4px;">Potensi Tsunami</span>
                <span class="tsunami-badge ${isTsunami ? 'tsunami-danger' : 'tsunami-safe'}">
                    ${isTsunami ? '⚠️ BERPOTENSI TSUNAMI' : '✅ Tidak berpotensi tsunami'}
                </span>
            </div>
            ${quake.Dirasakan && quake.Dirasakan !== '-' ? `
                <div style="margin-top: 8px;">
                    <span class="meta-label" style="display:block; margin-bottom:4px;">Dirasakan</span>
                    <span class="meta-value" style="font-size:0.72rem; line-height:1.5; font-family:var(--font-main);">${quake.Dirasakan}</span>
                </div>
            ` : ''}
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-color);">
                <span class="meta-label">Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)</span>
            </div>
        </div>
    `;
}
function renderQuakeList(containerId, quakes, counterId) {
    const container = document.getElementById(containerId);
    const counter = document.getElementById(counterId);
    if (!quakes || quakes.length === 0) {
        container.innerHTML = '<div class="quake-detail-placeholder">Tidak ada data</div>';
        counter.textContent = '0';
        return;
    }
    counter.textContent = quakes.length;
    container.innerHTML = quakes.map(q => {
        const mag = parseMagnitude(q.Magnitude);
        const magColor = getMagnitudeColor(mag);
        const timeAgo = formatTimeAgo(q.DateTime);
        return `
            <div class="quake-list-item">
                <div class="quake-list-mag" style="background:${magColor.bg}">${mag.toFixed(1)}</div>
                <div class="quake-list-info">
                    <div class="quake-list-location">${q.Wilayah}</div>
                    <div class="quake-list-meta">${q.Kedalaman} • ${q.Tanggal}${q.Dirasakan && q.Dirasakan !== '-' ? ' • Dirasakan' : ''}</div>
                </div>
                <div class="quake-list-time">${timeAgo}</div>
            </div>
        `;
    }).join('');
}
// ===== MAP =====
function initMaps() {
    // Dark tile layer
    const tileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    const tileAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';
    // Mini Map
    state.miniMap = L.map('mini-map', {
        center: CONFIG.MAP.CENTER,
        zoom: CONFIG.MAP.ZOOM,
        zoomControl: false,
        attributionControl: false,
        dragging: true,
        scrollWheelZoom: false,
    });
    L.tileLayer(tileUrl, { attribution: tileAttribution }).addTo(state.miniMap);
    // Main Map
    state.mainMap = L.map('main-map', {
        center: CONFIG.MAP.CENTER,
        zoom: CONFIG.MAP.ZOOM,
        zoomControl: true,
        minZoom: CONFIG.MAP.MIN_ZOOM,
        maxZoom: CONFIG.MAP.MAX_ZOOM,
    });
    L.tileLayer(tileUrl, {
        attribution: tileAttribution + ' | Data: BMKG',
    }).addTo(state.mainMap);
}
function updateMaps() {
    updateMapMarkers(state.miniMap, state.miniMapMarkers, false);
    updateMapMarkers(state.mainMap, state.mainMapMarkers, true);
}
function updateMapMarkers(map, markerArray, withPopup) {
    // Clear existing markers
    markerArray.forEach(m => map.removeLayer(m));
    markerArray.length = 0;
    const selectedRegion = document.getElementById('region-select').value;
    state.allEarthquakes.forEach(quake => {
        const coords = parseCoordinates(quake.Coordinates);
        const mag = parseMagnitude(quake.Magnitude);
        const magColor = getMagnitudeColor(mag);
        // Region filter
        if (selectedRegion !== 'all') {
            const quakeRegion = getRegionFromWilayah(quake.Wilayah);
            if (quakeRegion !== selectedRegion) return;
        }
        // Circle marker size based on magnitude
        const radius = Math.max(4, mag * 2.5);
        const marker = L.circleMarker([coords.lat, coords.lng], {
            radius: radius,
            fillColor: magColor.bg,
            color: magColor.bg,
            weight: 1.5,
            opacity: 0.8,
            fillOpacity: 0.5,
        }).addTo(map);
        if (withPopup) {
            const isTsunami = hasTsunamiPotential(quake);
            const popupContent = `
                <div class="popup-title">
                    <span class="popup-mag" style="background:${magColor.bg}">M ${mag.toFixed(1)}</span>
                    ${quake.Kedalaman}
                </div>
                <div style="margin-bottom:6px; color: #94a3b8; font-size: 0.72rem;">${quake.Wilayah}</div>
                <div class="popup-row"><span class="popup-label">Waktu</span><span class="popup-value">${quake.Tanggal} ${quake.Jam}</span></div>
                <div class="popup-row"><span class="popup-label">Koordinat</span><span class="popup-value">${coords.lat.toFixed(4)}, ${coords.lng.toFixed(4)}</span></div>
                <div class="popup-row"><span class="popup-label">Kedalaman</span><span class="popup-value">${quake.Kedalaman}</span></div>
                <div class="popup-row"><span class="popup-label">Tsunami</span><span class="popup-value" style="color:${isTsunami ? '#ef4444' : '#22c55e'}">${isTsunami ? '⚠️ BERPOTENSI' : '✅ Aman'}</span></div>
                <div style="margin-top:6px; font-size:0.65rem; color: #64748b;">Sumber: BMKG</div>
            `;
            marker.bindPopup(popupContent, { maxWidth: 280 });
        }
        markerArray.push(marker);
    });
}
// ===== ALERT CENTER =====
function updateAlertCenter() {
    // Latest quake card
    if (state.autoGempa) {
        const q = state.autoGempa;
        const mag = parseMagnitude(q.Magnitude);
        const magColor = getMagnitudeColor(mag);
        const coords = parseCoordinates(q.Coordinates);
        document.getElementById('alert-latest-quake').innerHTML = `
            <div style="display:flex; align-items:center; gap:14px; margin-bottom:12px;">
                <div class="magnitude-circle ${magColor.cls}" style="width:56px;height:56px;font-size:1.4rem;">${mag.toFixed(1)}</div>
                <div>
                    <div style="font-weight:600; font-size:0.85rem; color:var(--text-bright);">${q.Wilayah}</div>
                    <div style="font-size:0.72rem; color:var(--text-muted);">${q.Tanggal} ${q.Jam}</div>
                </div>
            </div>
            <div class="quake-meta-grid">
                <div class="meta-item"><span class="meta-label">Kedalaman</span><span class="meta-value">${q.Kedalaman}</span></div>
                <div class="meta-item"><span class="meta-label">Koordinat</span><span class="meta-value">${coords.lat.toFixed(2)}, ${coords.lng.toFixed(2)}</span></div>
            </div>
        `;
    }
    // Biggest quake card
    if (state.allEarthquakes.length > 0) {
        const biggest = state.allEarthquakes.reduce((max, q) => parseMagnitude(q.Magnitude) > parseMagnitude(max.Magnitude) ? q : max);
        const mag = parseMagnitude(biggest.Magnitude);
        const magColor = getMagnitudeColor(mag);
        const coords = parseCoordinates(biggest.Coordinates);
        document.getElementById('alert-biggest-quake').innerHTML = `
            <div style="display:flex; align-items:center; gap:14px; margin-bottom:12px;">
                <div class="magnitude-circle ${magColor.cls}" style="width:56px;height:56px;font-size:1.4rem;">${mag.toFixed(1)}</div>
                <div>
                    <div style="font-weight:600; font-size:0.85rem; color:var(--text-bright);">${biggest.Wilayah}</div>
                    <div style="font-size:0.72rem; color:var(--text-muted);">${biggest.Tanggal} ${biggest.Jam}</div>
                </div>
            </div>
            <div class="quake-meta-grid">
                <div class="meta-item"><span class="meta-label">Kedalaman</span><span class="meta-value">${biggest.Kedalaman}</span></div>
                <div class="meta-item"><span class="meta-label">Koordinat</span><span class="meta-value">${coords.lat.toFixed(2)}, ${coords.lng.toFixed(2)}</span></div>
            </div>
        `;
    }
    // Tsunami status
    const tsunamiQuakes = state.allEarthquakes.filter(q => hasTsunamiPotential(q));
    const tsunamiStatusEl = document.getElementById('alert-tsunami-status');
    if (tsunamiQuakes.length > 0) {
        tsunamiStatusEl.textContent = 'PERINGATAN AKTIF';
        tsunamiStatusEl.className = 'status-value emergency';
    } else {
        tsunamiStatusEl.textContent = 'AMAN';
        tsunamiStatusEl.className = 'status-value';
    }
}
// ===== STATISTICS =====
function updateStatistics() {
    const quakes = state.allEarthquakes;
    if (quakes.length === 0) return;
    // Chart defaults
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(59, 130, 246, 0.1)';
    Chart.defaults.font.family = "'Inter', sans-serif";
    updateDailyChart(quakes);
    updateMagnitudeChart(quakes);
    updateDepthChart(quakes);
    updateWeeklyChart(quakes);
}
function updateDailyChart(quakes) {
    const canvas = document.getElementById('chart-daily');
    if (state.charts.daily) state.charts.daily.destroy();
    // Group by date (last 7 days)
    const days = {};
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const key = d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });
        days[key] = 0;
    }
    quakes.forEach(q => {
        const d = new Date(q.DateTime);
        const key = d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });
        if (key in days) days[key]++;
    });
    state.charts.daily = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: Object.keys(days),
            datasets: [{
                label: 'Jumlah Gempa',
                data: Object.values(days),
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: '#3b82f6',
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: 'rgba(59, 130, 246, 0.06)' },
                },
                x: {
                    grid: { display: false },
                },
            },
        },
    });
}
function updateMagnitudeChart(quakes) {
    const canvas = document.getElementById('chart-magnitude');
    if (state.charts.magnitude) state.charts.magnitude.destroy();
    const ranges = { '< 3.0': 0, '3.0-4.0': 0, '4.0-5.0': 0, '5.0-6.0': 0, '6.0-7.0': 0, '> 7.0': 0 };
    quakes.forEach(q => {
        const mag = parseMagnitude(q.Magnitude);
        if (mag < 3) ranges['< 3.0']++;
        else if (mag < 4) ranges['3.0-4.0']++;
        else if (mag < 5) ranges['4.0-5.0']++;
        else if (mag < 6) ranges['5.0-6.0']++;
        else if (mag < 7) ranges['6.0-7.0']++;
        else ranges['> 7.0']++;
    });
    state.charts.magnitude = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: Object.keys(ranges),
            datasets: [{
                data: Object.values(ranges),
                backgroundColor: [
                    '#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444', '#991b1b'
                ],
                borderWidth: 0,
                hoverOffset: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 12,
                        usePointStyle: true,
                        pointStyleWidth: 10,
                        font: { size: 11 },
                    },
                },
            },
        },
    });
}
function updateDepthChart(quakes) {
    const canvas = document.getElementById('chart-depth');
    if (state.charts.depth) state.charts.depth.destroy();
    const ranges = { '0-30 km': 0, '30-70 km': 0, '70-150 km': 0, '150-300 km': 0, '> 300 km': 0 };
    quakes.forEach(q => {
        const depth = parseDepth(q.Kedalaman);
        if (depth <= 30) ranges['0-30 km']++;
        else if (depth <= 70) ranges['30-70 km']++;
        else if (depth <= 150) ranges['70-150 km']++;
        else if (depth <= 300) ranges['150-300 km']++;
        else ranges['> 300 km']++;
    });
    state.charts.depth = new Chart(canvas, {
        type: 'polarArea',
        data: {
            labels: Object.keys(ranges),
            datasets: [{
                data: Object.values(ranges),
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(6, 182, 212, 0.7)',
                    'rgba(34, 197, 94, 0.7)',
                    'rgba(234, 179, 8, 0.7)',
                    'rgba(239, 68, 68, 0.7)',
                ],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 12,
                        usePointStyle: true,
                        pointStyleWidth: 10,
                        font: { size: 11 },
                    },
                },
            },
            scales: {
                r: {
                    ticks: { display: false },
                    grid: { color: 'rgba(59, 130, 246, 0.1)' },
                },
            },
        },
    });
}
function updateWeeklyChart(quakes) {
    const canvas = document.getElementById('chart-weekly');
    if (state.charts.weekly) state.charts.weekly.destroy();
    // Magnitude over time scatter-like line
    const dataPoints = quakes.slice(0, 30).reverse().map((q, i) => ({
        x: i,
        y: parseMagnitude(q.Magnitude),
    }));
    const labels = quakes.slice(0, 30).reverse().map(q => {
        const d = new Date(q.DateTime);
        return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });
    });
    state.charts.weekly = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Magnitudo',
                data: dataPoints.map(p => p.y),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.3,
                pointBackgroundColor: dataPoints.map(p => {
                    if (p.y >= 6) return '#ef4444';
                    if (p.y >= 5) return '#f97316';
                    if (p.y >= 3) return '#eab308';
                    return '#22c55e';
                }),
                pointRadius: 5,
                pointHoverRadius: 7,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `M ${ctx.parsed.y.toFixed(1)}`,
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 10,
                    grid: { color: 'rgba(59, 130, 246, 0.06)' },
                    title: { display: true, text: 'Magnitudo', font: { size: 11 } },
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 10,
                        font: { size: 10 },
                    },
                },
            },
        },
    });
}
// ===== HISTORY =====
function updateHistory() {
    const period = state.historyPeriod;
    let filtered = [];
    switch (period) {
        case 'today':
            filtered = state.allEarthquakes.filter(q => isTodayQuake(q.DateTime));
            break;
        case '7days':
            filtered = state.allEarthquakes.filter(q => isWithinDays(q.DateTime, 7));
            break;
        case '30days':
            filtered = state.allEarthquakes.filter(q => isWithinDays(q.DateTime, 30));
            break;
        default:
            filtered = state.allEarthquakes;
    }
    // Search filter
    const search = document.getElementById('search-input')?.value?.toLowerCase() || '';
    if (search) {
        filtered = filtered.filter(q =>
            (q.Wilayah || '').toLowerCase().includes(search) ||
            (q.Magnitude || '').includes(search) ||
            (q.Tanggal || '').toLowerCase().includes(search) ||
            (q.Kedalaman || '').toLowerCase().includes(search)
        );
    }
    renderHistoryTable(filtered);
}
function renderHistoryTable(quakes) {
    const tbody = document.getElementById('history-table-body');
    if (quakes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-row">Tidak ada data untuk periode ini</td></tr>';
        return;
    }
    tbody.innerHTML = quakes.map((q, i) => {
        const mag = parseMagnitude(q.Magnitude);
        const magColor = getMagnitudeColor(mag);
        const coords = parseCoordinates(q.Coordinates);
        const isTsunami = hasTsunamiPotential(q);
        return `
            <tr>
                <td>${i + 1}</td>
                <td>${q.Tanggal}</td>
                <td style="font-family:var(--font-mono)">${q.Jam}</td>
                <td><span class="mag-cell" style="background:${magColor.bg}">${mag.toFixed(1)}</span></td>
                <td style="font-family:var(--font-mono)">${q.Kedalaman}</td>
                <td style="font-family:var(--font-mono); font-size:0.72rem;">${coords.lat.toFixed(3)}, ${coords.lng.toFixed(3)}</td>
                <td style="max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${q.Wilayah}">${q.Wilayah}</td>
                <td><span class="tsunami-badge ${isTsunami ? 'tsunami-danger' : 'tsunami-safe'}" style="font-size:0.65rem;">${isTsunami ? '⚠️ Ya' : '✅ Tidak'}</span></td>
            </tr>
        `;
    }).join('');
}
// ===== EXPORT FUNCTIONS =====
function exportCSV() {
    const quakes = getFilteredHistoryData();
    if (quakes.length === 0) {
        alert('Tidak ada data untuk diexport.');
        return;
    }
    const headers = ['No', 'Tanggal', 'Jam', 'Magnitudo', 'Kedalaman', 'Latitude', 'Longitude', 'Wilayah', 'Potensi Tsunami', 'Sumber'];
    const rows = quakes.map((q, i) => {
        const coords = parseCoordinates(q.Coordinates);
        return [
            i + 1,
            q.Tanggal,
            q.Jam,
            q.Magnitude,
            q.Kedalaman,
            coords.lat,
            coords.lng,
            `"${q.Wilayah}"`,
            q.Potensi || '-',
            'BMKG',
        ].join(',');
    });
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gempa_indonesia_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}
function exportPDF() {
    const quakes = getFilteredHistoryData();
    if (quakes.length === 0) {
        alert('Tidak ada data untuk diexport.');
        return;
    }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('landscape');
    doc.setFontSize(16);
    doc.text('Laporan Gempa Bumi Indonesia', 14, 18);
    doc.setFontSize(9);
    doc.text(`Sumber: BMKG | Diunduh: ${new Date().toLocaleString('id-ID')}`, 14, 24);
    let y = 32;
    const headers = ['No', 'Tanggal', 'Jam', 'Mag', 'Kedalaman', 'Lat', 'Lng', 'Wilayah', 'Tsunami'];
    const colX = [14, 24, 54, 82, 94, 118, 138, 158, 248];
    doc.setFontSize(8);
    doc.setFont(undefined, 'bold');
    headers.forEach((h, i) => doc.text(h, colX[i], y));
    doc.setFont(undefined, 'normal');
    y += 6;
    quakes.slice(0, 40).forEach((q, i) => {
        const coords = parseCoordinates(q.Coordinates);
        const row = [
            String(i + 1),
            q.Tanggal,
            q.Jam,
            q.Magnitude,
            q.Kedalaman,
            coords.lat.toFixed(2),
            coords.lng.toFixed(2),
            q.Wilayah.substring(0, 50),
            hasTsunamiPotential(q) ? 'Ya' : 'Tidak',
        ];
        row.forEach((val, j) => doc.text(val, colX[j], y));
        y += 5;
        if (y > 190) {
            doc.addPage();
            y = 20;
        }
    });
    doc.save(`laporan_gempa_${new Date().toISOString().split('T')[0]}.pdf`);
}
function getFilteredHistoryData() {
    const period = state.historyPeriod;
    let filtered = [];
    switch (period) {
        case 'today': filtered = state.allEarthquakes.filter(q => isTodayQuake(q.DateTime)); break;
        case '7days': filtered = state.allEarthquakes.filter(q => isWithinDays(q.DateTime, 7)); break;
        case '30days': filtered = state.allEarthquakes.filter(q => isWithinDays(q.DateTime, 30)); break;
        default: filtered = state.allEarthquakes;
    }
    const search = document.getElementById('search-input')?.value?.toLowerCase() || '';
    if (search) {
        filtered = filtered.filter(q =>
            (q.Wilayah || '').toLowerCase().includes(search) ||
            (q.Magnitude || '').includes(search)
        );
    }
    return filtered;
}
// ===== MAP SCREENSHOT =====
async function takeMapScreenshot() {
    const mapEl = document.getElementById('main-map');
    try {
        const canvas = await html2canvas(mapEl, { useCORS: true, allowTaint: true });
        const link = document.createElement('a');
        link.download = `peta_gempa_${new Date().toISOString().split('T')[0]}.png`;
        link.href = canvas.toDataURL();
        link.click();
    } catch (e) {
        console.error('Screenshot failed:', e);
        alert('Screenshot gagal. Silakan coba lagi.');
    }
}
// ===== AUTO REFRESH =====
function startAutoRefresh() {
    state.countdown = CONFIG.REFRESH_INTERVAL / 1000;
    // Countdown timer
    state.countdownTimer = setInterval(() => {
        state.countdown--;
        const countdownEl = document.getElementById('countdown');
        const fillEl = document.getElementById('refresh-bar-fill');
        if (countdownEl) countdownEl.textContent = state.countdown;
        if (fillEl) {
            const pct = ((CONFIG.REFRESH_INTERVAL / 1000 - state.countdown) / (CONFIG.REFRESH_INTERVAL / 1000)) * 100;
            fillEl.style.width = `${pct}%`;
        }
        if (state.countdown <= 0) {
            state.countdown = CONFIG.REFRESH_INTERVAL / 1000;
        }
    }, 1000);
    // Data refresh
    state.refreshTimer = setInterval(() => {
        loadAllData();
        state.countdown = CONFIG.REFRESH_INTERVAL / 1000;
    }, CONFIG.REFRESH_INTERVAL);
}
// ===== TAB NAVIGATION =====
function switchTab(tabName) {
    state.activeTab = tabName;
    // Update nav
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    // Update panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `tab-${tabName}`);
    });
    // Invalidate map size when switching to map tab
    if (tabName === 'map') {
        setTimeout(() => {
            state.mainMap?.invalidateSize();
        }, 100);
    }
    // Invalidate minimap when switching to dashboard
    if (tabName === 'dashboard') {
        setTimeout(() => {
            state.miniMap?.invalidateSize();
        }, 100);
    }
}
// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    // Open map from dashboard
    document.getElementById('btn-open-map').addEventListener('click', () => switchTab('map'));
    // Region filter
    document.getElementById('region-select').addEventListener('change', (e) => {
        const region = CONFIG.REGIONS[e.target.value];
        if (region) {
            state.mainMap.flyTo(region.center, region.zoom, { duration: 1.2 });
        }
        updateMaps();
    });
    // Fullscreen
    document.getElementById('btn-fullscreen').addEventListener('click', () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    });
    // Refresh
    document.getElementById('btn-refresh').addEventListener('click', () => {
        loadAllData();
        state.countdown = CONFIG.REFRESH_INTERVAL / 1000;
        // Spin animation
        const btn = document.getElementById('btn-refresh');
        btn.style.transition = 'transform 0.5s ease';
        btn.style.transform = 'rotate(360deg)';
        setTimeout(() => { btn.style.transform = 'rotate(0deg)'; }, 600);
    });
    // Map screenshot
    document.getElementById('btn-screenshot').addEventListener('click', takeMapScreenshot);
    // Map fullscreen
    document.getElementById('btn-map-fullscreen').addEventListener('click', () => {
        const container = document.querySelector('.map-container');
        container.classList.toggle('map-fullscreen');
        setTimeout(() => state.mainMap?.invalidateSize(), 200);
    });
    // Alarm volume
    document.getElementById('alarm-volume').addEventListener('input', (e) => {
        state.alarmVolume = e.target.value / 100;
        document.getElementById('volume-display').textContent = `${e.target.value}%`;
    });
    // Mute button
    document.getElementById('btn-mute').addEventListener('click', () => {
        state.isMuted = !state.isMuted;
        const btn = document.getElementById('btn-mute');
        btn.classList.toggle('muted', state.isMuted);
        btn.innerHTML = state.isMuted
            ? `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> UNMUTE`
            : `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg> MUTE`;
    });
    // Test alarm
    document.getElementById('btn-test-alarm').addEventListener('click', () => {
        audio.init();
        audio.playWarning();
        addAlertLog('warning', '🔔 Test alarm diaktifkan');
    });
    // Dismiss emergency
    document.getElementById('dismiss-emergency').addEventListener('click', () => {
        document.getElementById('emergency-overlay').classList.add('hidden');
    });
    // History period filter
    document.querySelectorAll('.btn-filter').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.historyPeriod = btn.dataset.period;
            updateHistory();
        });
    });
    // History search
    document.getElementById('search-input').addEventListener('input', () => {
        updateHistory();
    });
    // Export buttons
    document.getElementById('btn-export-csv').addEventListener('click', exportCSV);
    document.getElementById('btn-export-pdf').addEventListener('click', exportPDF);
    // Online/offline detection
    window.addEventListener('online', () => {
        state.isOnline = true;
        document.getElementById('offline-banner').classList.add('hidden');
        updateConnectionStatus(true);
        loadAllData();
    });
    window.addEventListener('offline', () => {
        state.isOnline = false;
        document.getElementById('offline-banner').classList.remove('hidden');
        updateConnectionStatus(false);
    });
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        // We'll request on user interaction
        document.addEventListener('click', function requestNotif() {
            Notification.requestPermission();
            document.removeEventListener('click', requestNotif);
        }, { once: true });
    }
}
// ===== SERVICE WORKER (PWA) =====
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js').catch(err => {
            console.log('SW registration failed:', err);
        });
    }
}
// ===== INITIALIZATION =====
async function init() {
    console.log('🌋 Indonesia Earthquake Monitoring System initializing...');
    // Setup events
    setupEventListeners();
    // Init maps
    initMaps();
    // Start clock
    updateClock();
    setInterval(updateClock, 1000);
    // Load data
    await loadAllData();
    // Start auto-refresh
    startAutoRefresh();
    // Register PWA
    registerServiceWorker();
    // Hide loading screen
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        loadingScreen.classList.add('fade-out');
        document.getElementById('app').classList.remove('hidden');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
            // Fix map sizing
            state.miniMap?.invalidateSize();
        }, 600);
    }, 2800);
    console.log('✅ IEMS initialized successfully');
}
// Start the app
document.addEventListener('DOMContentLoaded', init);
