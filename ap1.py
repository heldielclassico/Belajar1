import streamlit as st
from PIL import Image
import PIL.ExifTags as ExifTags
import folium
from streamlit_folium import folium_static
from datetime import datetime
import pandas as pd
import io

st.set_page_config(page_title="Geotagging Viewer", layout="wide")

st.title("📍 Geotagging Viewer dari Gambar")
st.write("Unggah gambar untuk mengekstrak dan menampilkan informasi geotagging (GPS)")

# Fungsi untuk konversi koordinat DMS ke derajat desimal
def dms_to_decimal(degrees, minutes, seconds, direction):
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

# Fungsi untuk mengekstrak data GPS dari EXIF
def extract_gps_info(image):
    try:
        exif_data = image._getexif()
        if not exif_data:
            return None
        
        gps_info = {}
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for key in value:
                    sub_tag = ExifTags.GPSTAGS.get(key, key)
                    gps_info[sub_tag] = value[key]
        
        if not gps_info:
            return None
        
        # Ekstrak latitude dan longitude
        gps_latitude = gps_info.get('GPSLatitude')
        gps_latitude_ref = gps_info.get('GPSLatitudeRef', 'N')
        gps_longitude = gps_info.get('GPSLongitude')
        gps_longitude_ref = gps_info.get('GPSLongitudeRef', 'E')
        
        if not (gps_latitude and gps_longitude):
            return None
        
        # Konversi ke derajat desimal
        lat_deg = dms_to_decimal(gps_latitude[0], gps_latitude[1], gps_latitude[2], gps_latitude_ref)
        lon_deg = dms_to_decimal(gps_longitude[0], gps_longitude[1], gps_longitude[2], gps_longitude_ref)
        
        # Informasi tambahan
        altitude = gps_info.get('GPSAltitude')
        altitude_ref = gps_info.get('GPSAltitudeRef', 0)  # 0 = above sea level, 1 = below sea level
        
        gps_data = {
            'latitude': lat_deg,
            'longitude': lon_deg,
            'latitude_ref': gps_latitude_ref,
            'longitude_ref': gps_longitude_ref,
            'altitude': altitude[0] / altitude[1] if altitude else None,
            'altitude_ref': "Diatas permukaan laut" if altitude_ref == 0 else "Dibawah permukaan laut",
            'timestamp': gps_info.get('GPSTimeStamp'),
            'date': gps_info.get('GPSDateStamp'),
            'map_direction': gps_info.get('GPSImgDirection')
        }
        
        return gps_data
    except Exception as e:
        st.error(f"Error membaca data GPS: {e}")
        return None

# Fungsi untuk membuat peta dengan marker
def create_map(latitude, longitude, zoom=15):
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom)
    
    # Tambahkan marker
    folium.Marker(
        [latitude, longitude],
        popup=f"Lokasi Foto<br>Lat: {latitude:.6f}<br>Lon: {longitude:.6f}",
        tooltip="Klik untuk detail",
        icon=folium.Icon(color='red', icon='camera', prefix='fa')
    ).add_to(m)
    
    # Tambahkan circle marker
    folium.CircleMarker(
        location=[latitude, longitude],
        radius=10,
        color='#3186cc',
        fill=True,
        fill_color='#3186cc'
    ).add_to(m)
    
    return m

# Sidebar untuk upload
with st.sidebar:
    st.header("📤 Upload Gambar")
    uploaded_file = st.file_uploader(
        "Pilih gambar (JPG/JPEG/PNG)",
        type=['jpg', 'jpeg', 'png', 'heic'],
        help="Pilih gambar yang mengandung data EXIF/GPS"
    )
    
    st.divider()
    st.info("""
    **Tips:**
    - Gunakan gambar dari kamera smartphone
    - Pastikan GPS aktif saat mengambil foto
    - Format JPG/JPEG biasanya menyimpan data GPS
    """)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📷 Preview Gambar")
    
    if uploaded_file is not None:
        try:
            # Buka gambar
            image = Image.open(uploaded_file)
            
            # Tampilkan gambar
            st.image(image, caption="Gambar yang diunggah", use_column_width=True)
            
            # Tampilkan info dasar
            img_format = image.format
            img_mode = image.mode
            img_size = image.size
            
            st.write(f"**Format:** {img_format}")
            st.write(f"**Mode:** {img_mode}")
            st.write(f"**Dimensi:** {img_size[0]} x {img_size[1]} pixel")
            
        except Exception as e:
            st.error(f"Error membaca gambar: {e}")

with col2:
    st.subheader("📍 Data Geotagging")
    
    if uploaded_file is not None:
        try:
            # Ekstrak data GPS
            image = Image.open(uploaded_file)
            gps_data = extract_gps_info(image)
            
            if gps_data:
                st.success("✅ Data GPS ditemukan!")
                
                # Tampilkan data GPS dalam bentuk tabel
                gps_df = pd.DataFrame({
                    'Parameter': [
                        'Latitude', 'Longitude', 'Altitude', 
                        'Referensi Altitude', 'Tanggal GPS', 'Arah Gambar'
                    ],
                    'Nilai': [
                        f"{gps_data['latitude']:.6f}° {gps_data['latitude_ref']}",
                        f"{gps_data['longitude']:.6f}° {gps_data['longitude_ref']}",
                        f"{gps_data['altitude']:.2f} m" if gps_data['altitude'] else "Tidak tersedia",
                        gps_data['altitude_ref'],
                        gps_data['date'] if gps_data['date'] else "Tidak tersedia",
                        f"{gps_data['map_direction'][0]/gps_data['map_direction'][1]:.1f}°" if gps_data['map_direction'] else "Tidak tersedia"
                    ]
                })
                
                st.dataframe(gps_df, use_container_width=True, hide_index=True)
                
                # Tampilkan koordinat dalam format yang mudah disalin
                with st.expander("📋 Salin Koordinat"):
                    st.code(f"Latitude: {gps_data['latitude']:.6f}\nLongitude: {gps_data['longitude']:.6f}")
                
                # Tombol untuk membuka di Google Maps
                google_maps_url = f"https://www.google.com/maps?q={gps_data['latitude']},{gps_data['longitude']}"
                st.link_button("🗺️ Buka di Google Maps", google_maps_url)
                
            else:
                st.warning("⚠️ Tidak ada data GPS yang ditemukan dalam gambar ini.")
                st.info("""
                **Kemungkinan penyebab:**
                1. GPS dimatikan saat mengambil foto
                2. Gambar telah diolah/dikompres
                3. Format gambar tidak mendukung EXIF
                """)
                
        except Exception as e:
            st.error(f"Error memproses gambar: {e}")

# Bagian Peta (full width)
if uploaded_file is not None:
    st.divider()
    st.subheader("🗺️ Peta Lokasi")
    
    try:
        image = Image.open(uploaded_file)
        gps_data = extract_gps_info(image)
        
        if gps_data:
            # Tampilkan peta
            m = create_map(gps_data['latitude'], gps_data['longitude'])
            folium_static(m, width=900, height=500)
            
            # Tampilkan koordinat di bawah peta
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Latitude", f"{gps_data['latitude']:.6f}°")
            with col_b:
                st.metric("Longitude", f"{gps_data['longitude']:.6f}°")
            with col_c:
                if gps_data['altitude']:
                    st.metric("Altitude", f"{gps_data['altitude']:.2f} m")
                else:
                    st.metric("Altitude", "N/A")
        else:
            st.info("Peta tidak dapat ditampilkan karena tidak ada data GPS.")
            
    except Exception as e:
        st.error(f"Error menampilkan peta: {e}")

# Footer
st.divider()
st.caption("""
**Cara kerja:** Aplikasi ini membaca metadata EXIF dari gambar, khususnya data GPS, 
dan menampilkannya dalam bentuk koordinat serta peta interaktif.
""")
