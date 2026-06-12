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
                dash_array="8 6"
            ).add_to(sat_map)

            # Central marker
            folium.CircleMarker(
                location=[ep_lat, ep_lon],
                radius=10,
                color=ep_color,
                fill=True,
                fill_color="#ffffff",
                fill_opacity=0.9,
                weight=3,
                popup=folium.Popup(f"<b>{selected_event['Wilayah']}</b>", max_width=200)
            ).add_to(sat_map)

            st_folium(sat_map, width=None, height=400, key="detail_sat_map")
        except Exception as e:
            st.error(f"Gagal menampilkan peta satelit zoom: {e}")
