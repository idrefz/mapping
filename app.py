import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import io
import json
from streamlit_folium import st_folium
import folium

# Konfigurasi halaman
st.set_page_config(
    page_title="Form Survey ODP/ODC + Telegram",
    page_icon="📤",
    layout="wide"
)

# Konfigurasi bot Telegram
TELEGRAM_BOT_TOKEN = "8254431453:AAHKeJBQUKimm8ZRsAXBJLKpNZ2w2VIcZ64"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
TELEGRAM_CHAT_ID = "-4884449649"  # Grup chat ID

# Fungsi untuk mengirim pesan ke Telegram
def send_telegram_message(chat_id, message):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None

# Fungsi untuk mengirim foto ke Telegram
def send_telegram_photo(chat_id, photo_path, caption=""):
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    with open(photo_path, "rb") as photo:
        files = {"photo": photo}
        data = {"chat_id": chat_id, "caption": caption}
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            st.error(f"Error sending photo: {str(e)}")
            return None

# Fungsi untuk mengirim dokumen ke Telegram
def send_telegram_document(chat_id, document_path, caption=""):
    url = f"{TELEGRAM_API_URL}/sendDocument"
    with open(document_path, "rb") as document:
        files = {"document": document}
        data = {"chat_id": chat_id, "caption": caption}
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            st.error(f"Error sending document: {str(e)}")
            return None

# Fungsi untuk mendapatkan updates dari bot
def get_bot_updates():
    url = f"{TELEGRAM_API_URL}/getUpdates"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        st.error(f"Error getting updates: {str(e)}")
        return None

# Fungsi untuk menyimpan data
def save_data(data):
    # Cek apakah file sudah ada
    file_exists = os.path.isfile('data_survey_odp.csv')
    
    # Buat DataFrame dari data
    df = pd.DataFrame([data])
    
    # Simpan ke CSV
    if file_exists:
        df.to_csv('data_survey_odp.csv', mode='a', header=False, index=False)
    else:
        df.to_csv('data_survey_odp.csv', index=False)
    
    return True

# Fungsi untuk mengelola unggahan gambar
def handle_image_upload(uploaded_files, odp_name):
    saved_paths = []
    folder = "uploaded_images"
    
    # Buat folder jika belum ada
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        st.error(f"Gagal membuat folder '{folder}': {str(e)}")
        return []
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            image = Image.open(uploaded_file)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(folder, f"{odp_name}_{timestamp}_{i}.jpg")
            image.save(filename)
            saved_paths.append(filename)
        except Exception as e:
            st.error(f"Gagal menyimpan gambar: {str(e)}")
    
    return saved_paths

# Fungsi untuk menguji koneksi ke bot Telegram
def test_telegram_connection():
    try:
        # Coba dapatkan info bot
        url = f"{TELEGRAM_API_URL}/getMe"
        response = requests.get(url)
        bot_info = response.json()
        
        if bot_info.get("ok"):
            # Coba kirim pesan test
            test_message = "✅ Bot Telegram terhubung dengan baik. Form Survey ODP/ODC siap digunakan."
            message_result = send_telegram_message(TELEGRAM_CHAT_ID, test_message)
            
            if message_result and message_result.get("ok"):
                return True, "Bot terhubung dan berhasil mengirim pesan test"
            else:
                return False, "Bot terhubung tetapi gagal mengirim pesan test"
        else:
            return False, "Token bot tidak valid"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Judul aplikasi
st.title("📤 Form Survey ODP/ODC dengan Telegram Integration")
st.markdown("---")

# Sidebar untuk konfigurasi Telegram
with st.sidebar:
    st.header("Konfigurasi Telegram")
    
    st.info(f"""
    **Konfigurasi Saat Ini:**
    - Bot Token: `{TELEGRAM_BOT_TOKEN}`
    - Chat ID: `{TELEGRAM_CHAT_ID}`
    - Tipe: Grup Chat
    """)
    
    # Tombol untuk test koneksi
    if st.button("Test Koneksi Telegram"):
        with st.spinner("Menguji koneksi ke Telegram..."):
            success, message = test_telegram_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    st.markdown("---")
    st.info("""
    **Cara Penggunaan:**
    1. Isi form survey di halaman utama
    2. Upload foto dokumentasi
    3. Klik 'Simpan & Kirim ke Telegram'
    4. Data akan dikirim ke grup Telegram
    """)

# Form input
with st.form("survey_form"):
    st.header("Informasi Lokasi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sto = st.text_input("STO*", help="Masukkan nama STO")
        odp_name = st.text_input("Nama ODP/ODC*", help="Masukkan nama ODP/ODC")
    
    with col2:
        st.markdown("**Pilih Lokasi di Peta**")
        m = folium.Map(location=[-6.175392, 106.827153], zoom_start=12)
        loc = st_folium(m, width=350, height=250)
        latitude = None
        longitude = None
        if loc and loc["last_clicked"]:
            latitude = loc["last_clicked"]["lat"]
            longitude = loc["last_clicked"]["lng"]
            st.success(f"Lokasi terpilih: {latitude}, {longitude}")
        else:
            st.info("Klik pada peta untuk memilih lokasi.")

    location_address = st.text_area("Alamat Lokasi*", height=100)
    
    st.markdown("---")
    st.header("Spesifikasi Teknis")
    
    col3, col4 = st.columns(2)
    
    with col3:
        specification = st.text_input("Spesifikasi ODP/ODC*")
        capacity = st.selectbox(
            "Kapasitas ODP/ODC*",
            ("", "8 Core", "16 Core", "32 Core")
        )
    
    with col4:
        existing_pole = st.selectbox(
            "Tiang Eksisting",
            ("", "Dapat digunakan", "Perlu perbaikan", "Tidak dapat digunakan", "Tidak ada tiang")
        )
    
    st.markdown("---")
    st.header("Status dan Rekomendasi")
    
    status = st.radio(
        "Status ODP/ODC*",
        ("ODP/ODC Baru", "Update ODP/ODC", "ODP/ODC Tidak Ditemukan")
    )
    
    recommendation = st.selectbox(
        "Rekomendasi*",
        ("", "Insert SW", "Update label dan spek sesuai lapangan", "Delete UIM")
    )
    
    obstacles = st.text_area("Identifikasi Potensi Hambatan", height=100, 
                           placeholder="Gangguan lingkungan, izin, zona terlarang, dll.")
    
    notes = st.text_area("Catatan Tambahan", height=100)
    
    st.markdown("---")
    st.header("Dokumentasi Foto")
    
    uploaded_files = st.file_uploader(
        "Unggah Foto ODP/ODC*",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )
    
    # Tampilkan preview gambar
    if uploaded_files:
        st.subheader("Preview Foto")
        cols = st.columns(3)
        for i, uploaded_file in enumerate(uploaded_files):
            with cols[i % 3]:
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Foto {i+1}", use_column_width=True)
    
    st.markdown("**Wajib diisi*")
    
    # Tombol submit
    submitted = st.form_submit_button("Simpan & Kirim ke Telegram")
    
    # Validasi dan proses data setelah submit
    if submitted:
        error_messages = []
        
        # Validasi field wajib
        if not sto: error_messages.append("STO harus diisi")
        if not odp_name: error_messages.append("Nama ODP/ODC harus diisi")
        if not latitude: error_messages.append("Latitude harus diisi")
        if not longitude: error_messages.append("Longitude harus diisi")
        if not location_address: error_messages.append("Alamat lokasi harus diisi")
        if not specification: error_messages.append("Spesifikasi harus diisi")
        if not capacity: error_messages.append("Kapasitas harus diisi")
        if not recommendation: error_messages.append("Rekomendasi harus diisi")
        if not uploaded_files: error_messages.append("Minimal satu foto harus diunggah")
        
        # Tampilkan error jika ada
        if error_messages:
            for error in error_messages:
                st.error(error)
        else:
            with st.spinner("Menyimpan data dan mengirim ke Telegram..."):
                # Simpan gambar yang diupload
                image_paths = handle_image_upload(uploaded_files, odp_name)
                
                # Siapkan data untuk disimpan
                survey_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sto": sto,
                    "odp_name": odp_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "location_address": location_address,
                    "specification": specification,
                    "capacity": capacity,
                    "existing_pole": existing_pole,
                    "status": status,
                    "recommendation": recommendation,
                    "obstacles": obstacles,
                    "notes": notes,
                    "image_paths": ", ".join(image_paths)
                }
                
                # Simpan data
                if save_data(survey_data):
                    # Format pesan untuk Telegram
                    message = f"""
📋 <b>SURVEY ODP/ODC BARU</b>

🏢 <b>STO:</b> {sto}
📛 <b>Nama ODP/ODC:</b> {odp_name}
📍 <b>Koordinat:</b> {latitude}, {longitude}
🏠 <b>Alamat:</b> {location_address}
🔧 <b>Spesifikasi:</b> {specification}
💾 <b>Kapasitas:</b> {capacity}
⚡ <b>Tiang Eksisting:</b> {existing_pole if existing_pole else 'Tidak ditentukan'}
🔄 <b>Status:</b> {status}
✅ <b>Rekomendasi:</b> {recommendation}
⚠️ <b>Hambatan:</b> {obstacles if obstacles else 'Tidak ada'}
📝 <b>Catatan:</b> {notes if notes else 'Tidak ada'}
🕒 <b>Waktu Survey:</b> {survey_data['timestamp']}
                    """.strip()
                    
                    # Kirim pesan teks ke Telegram
                    message_result = send_telegram_message(TELEGRAM_CHAT_ID, message)
                    
                    # Kirim foto-foto ke Telegram
                    photo_results = []
                    for i, image_path in enumerate(image_paths):
                        caption = f"📸 Foto {i+1} - {odp_name} - {sto}" if i == 0 else ""
                        result = send_telegram_photo(TELEGRAM_CHAT_ID, image_path, caption)
                        photo_results.append(result)
                    
                    if message_result and message_result.get('ok'):
                        st.success("✅ Data survey berhasil disimpan dan dikirim ke Telegram!")
                        
                        # Tampilkan data yang disimpan
                        with st.expander("Lihat Data yang Dikirim"):
                            st.write("**STO:**", sto)
                            st.write("**Nama ODP/ODC:**", odp_name)
                            st.write("**Koordinat:**", latitude + ", " + longitude)
                            st.write("**Alamat:**", location_address)
                            st.write("**Spesifikasi:**", specification)
                            st.write("**Kapasitas:**", capacity)
                            st.write("**Tiang Eksisting:**", existing_pole)
                            st.write("**Status:**", status)
                            st.write("**Rekomendasi:**", recommendation)
                            st.write("**Hambatan:**", obstacles)
                            st.write("**Catatan:**", notes)
                            st.write("**Jumlah Foto:**", len(uploaded_files))
                    else:
                        st.error("❌ Gagal mengirim data ke Telegram. Periksa koneksi internet dan konfigurasi bot.")

# Bagian untuk melihat data yang sudah disimpan
st.markdown("---")
st.header("Data Survey yang Tersimpan")

if os.path.isfile('data_survey_odp.csv'):
    df = pd.read_csv('data_survey_odp.csv')
    st.dataframe(df)
    
    # Opsi untuk mengirim semua data ke Telegram
    if st.button("Kirim Semua Data ke Telegram"):
        with st.spinner("Mengirim semua data ke Telegram..."):
            # Baca file CSV
            df = pd.read_csv('data_survey_odp.csv')
            
            # Kirim file CSV sebagai dokumen
            result = send_telegram_document(TELEGRAM_CHAT_ID, 'data_survey_odp.csv', "📊 Data Survey ODP/ODC Lengkap")
            
            if result and result.get('ok'):
                st.success("✅ Semua data berhasil dikirim ke Telegram!")
            else:
                st.error("❌ Gagal mengirim data ke Telegram.")
    
    # Opsi untuk menghapus data
    if st.button("Hapus Semua Data"):
        os.remove('data_survey_odp.csv')
        # Hapus juga folder gambar
        import shutil
        if os.path.exists('uploaded_images'):
            shutil.rmtree('uploaded_images')
        st.success("✅ Semua data berhasil dihapus")
        st.experimental_rerun()
else:
    st.info("ℹ️ Belum ada data yang disimpan")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Dibuat dengan Streamlit | Form Survey ODP/ODC dengan Integrasi Telegram</p>
        <p>Chat ID Grup: <code>-4884449649</code></p>
    </div>
    """,
    unsafe_allow_html=True
)
