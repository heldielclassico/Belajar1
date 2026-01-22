import streamlit as st
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from scipy.ndimage import measurements, morphology
import io
import base64

# Konfigurasi halaman
st.set_page_config(
    page_title="Morphology Counter",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS kustom
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6c757d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2E86AB;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 5px;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #2E86AB;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header aplikasi
st.markdown('<h1 class="main-header">🔬 Morphology Counter</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Segmentasi & Penghitungan Objek dengan Operasi Morfologi</p>', unsafe_allow_html=True)

# Sidebar untuk parameter
with st.sidebar:
    st.header("⚙️ Parameter Pengolahan")
    
    # Upload gambar
    uploaded_file = st.file_uploader(
        "Unggah gambar",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="Pilih gambar untuk diproses"
    )
    
    # Parameter processing
    st.subheader("Pengaturan Pemrosesan")
    
    threshold = st.slider(
        "Threshold",
        min_value=0,
        max_value=255,
        value=128,
        help="Nilai ambang batas untuk binarisasi"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        kernel_x = st.slider(
            "Kernel X",
            min_value=1,
            max_value=20,
            value=9,
            help="Lebar kernel untuk operasi morfologi"
        )
    with col2:
        kernel_y = st.slider(
            "Kernel Y",
            min_value=1,
            max_value=20,
            value=5,
            help="Tinggi kernel untuk operasi morfologi"
        )
    
    iterations = st.slider(
        "Iterasi",
        min_value=1,
        max_value=5,
        value=2,
        help="Jumlah iterasi untuk operasi opening"
    )
    
    # Tombol proses
    process_button = st.button("🚀 Proses Gambar", type="primary")
    
    # Demo dengan gambar default
    demo_button = st.button("🎮 Coba Demo")
    
    # Informasi aplikasi
    st.markdown("---")
    st.markdown("### ℹ️ Tentang Aplikasi")
    st.markdown("""
    Aplikasi ini menggunakan operasi morfologi untuk:
    - Segmentasi objek dari background
    - Penghitungan objek terhubung
    - Filtering noise dengan binary opening
    
    **Teknologi:**
    - Python
    - Streamlit
    - NumPy & SciPy
    - Pillow (PIL)
    """)

# Fungsi untuk memproses gambar
def process_image(image, threshold=128, kernel_size=(9,5), iterations=2):
    """Proses gambar dengan operasi morfologi"""
    
    # Konversi ke grayscale dan array numpy
    if isinstance(image, Image.Image):
        im_array = np.array(image.convert('L'))
    else:
        im_array = np.array(Image.open(image).convert('L'))
    
    # Binarisasi
    im_binary = (im_array < threshold).astype(np.uint8) * 255
    
    # Hitung objek sebelum opening
    labels_before, nbr_objects_before = measurements.label(im_binary > 0)
    
    # Operasi opening
    kernel = np.ones(kernel_size, dtype=np.uint8)
    im_opened = morphology.binary_opening(
        im_binary > 0, 
        structure=kernel, 
        iterations=iterations
    )
    
    # Hitung objek setelah opening
    labels_after, nbr_objects_after = measurements.label(im_opened)
    
    # Buat visualisasi
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Gambar asli
    axes[0, 0].imshow(im_array, cmap='gray')
    axes[0, 0].set_title('Gambar Asli')
    axes[0, 0].axis('off')
    
    # Gambar biner
    axes[0, 1].imshow(im_binary, cmap='gray')
    axes[0, 1].set_title(f'Biner (Threshold={threshold})')
    axes[0, 1].axis('off')
    
    # Label sebelum opening
    axes[0, 2].imshow(labels_before, cmap='tab20c')
    axes[0, 2].set_title(f'Sebelum Opening\n{nbr_objects_before} objek')
    axes[0, 2].axis('off')
    
    # Gambar setelah opening
    axes[1, 0].imshow(im_opened, cmap='gray')
    axes[1, 0].set_title('Setelah Opening')
    axes[1, 0].axis('off')
    
    # Label setelah opening
    axes[1, 1].imshow(labels_after, cmap='tab20c')
    axes[1, 1].set_title(f'Sesudah Opening\n{nbr_objects_after} objek')
    axes[1, 1].axis('off')
    
    # Perbandingan
    bars = axes[1, 2].bar(['Sebelum', 'Sesudah'], [nbr_objects_before, nbr_objects_after])
    axes[1, 2].set_title('Perbandingan Jumlah Objek')
    axes[1, 2].set_ylabel('Jumlah Objek')
    
    # Warna bar
    bars[0].set_color('#ff6b6b')
    bars[1].set_color('#51cf66')
    
    plt.tight_layout()
    
    return fig, nbr_objects_before, nbr_objects_after

# Fungsi untuk membuat gambar demo
def create_demo_image():
    """Membuat gambar demo dengan beberapa objek"""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor('white')
    
    # Buat beberapa lingkaran sebagai objek demo
    circles = [
        (0.2, 0.2, 0.05),
        (0.4, 0.3, 0.07),
        (0.7, 0.4, 0.06),
        (0.5, 0.7, 0.08),
        (0.8, 0.8, 0.05),
        (0.3, 0.5, 0.04),
        (0.6, 0.2, 0.06),
        (0.9, 0.6, 0.05),
    ]
    
    for x, y, r in circles:
        circle = plt.Circle((x, y), r, color='black', fill=True)
        ax.add_patch(circle)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Simpan ke buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    
    return Image.open(buf)

# Konten utama
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("### 📤 Unggah Gambar")
    
    if uploaded_file is not None:
        # Tampilkan gambar yang diupload
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar yang Diupload", use_column_width=True)
        
        # Simpan gambar di session state
        st.session_state['current_image'] = image
    elif 'demo_image' not in st.session_state:
        # Tampilkan placeholder
        st.info("Silakan upload gambar atau klik 'Coba Demo'")
        st.image("https://via.placeholder.com/600x400/CCCCCC/969696?text=Upload+Gambar", 
                use_column_width=True)

# Proses gambar jika tombol ditekan
if process_button and uploaded_file is not None:
    with st.spinner('Memproses gambar...'):
        # Proses gambar
        fig, nbr_before, nbr_after = process_image(
            uploaded_file,
            threshold=threshold,
            kernel_size=(kernel_x, kernel_y),
            iterations=iterations
        )
        
        # Simpan hasil di session state
        st.session_state['result_fig'] = fig
        st.session_state['nbr_before'] = nbr_before
        st.session_state['nbr_after'] = nbr_after
        st.session_state['params'] = {
            'threshold': threshold,
            'kernel': f"{kernel_x}x{kernel_y}",
            'iterations': iterations
        }

# Coba demo
if demo_button:
    with st.spinner('Membuat gambar demo...'):
        # Buat gambar demo
        demo_img = create_demo_image()
        
        # Proses gambar demo
        fig, nbr_before, nbr_after = process_image(
            demo_img,
            threshold=threshold,
            kernel_size=(kernel_x, kernel_y),
            iterations=iterations
        )
        
        # Simpan hasil
        st.session_state['demo_image'] = demo_img
        st.session_state['result_fig'] = fig
        st.session_state['nbr_before'] = nbr_before
        st.session_state['nbr_after'] = nbr_after
        st.session_state['params'] = {
            'threshold': threshold,
            'kernel': f"{kernel_x}x{kernel_y}",
            'iterations': iterations
        }
        
        # Tampilkan gambar demo
        col1.image(demo_img, caption="Gambar Demo", use_column_width=True)

# Tampilkan hasil jika ada
if 'result_fig' in st.session_state:
    st.markdown("---")
    st.markdown("## 📊 Hasil Segmentasi")
    
    # Metrik
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Sebelum Opening</div>
        </div>
        """.format(st.session_state['nbr_before']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Sesudah Opening</div>
        </div>
        """.format(st.session_state['nbr_after']), unsafe_allow_html=True)
    
    with col3:
        reduction = int(((st.session_state['nbr_before'] - st.session_state['nbr_after']) / 
                        st.session_state['nbr_before']) * 100)
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}%</div>
            <div class="metric-label">Pengurangan</div>
        </div>
        """.format(reduction), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Parameter</div>
            <div>Threshold: {}</div>
            <div>Kernel: {}</div>
            <div>Iterasi: {}</div>
        </div>
        """.format(
            st.session_state['params']['threshold'],
            st.session_state['params']['kernel'],
            st.session_state['params']['iterations']
        ), unsafe_allow_html=True)
    
    # Tampilkan visualisasi
    st.pyplot(st.session_state['result_fig'])
    
    # Penjelasan
    st.markdown("""
    <div class="info-box">
        <h4>📝 Interpretasi Hasil</h4>
        <p><strong>Operasi Opening</strong> (erosi diikuti dilasi) membantu:</p>
        <ul>
            <li><strong>Memisahkan objek</strong> yang saling menempel atau overlapping</li>
            <li><strong>Menghilangkan noise</strong> dan artefak kecil</li>
            <li><strong>Mempertahankan bentuk</strong> objek utama</li>
        </ul>
        <p>Penurunan jumlah objek setelah opening menunjukkan adanya noise atau objek yang terlalu kecil yang berhasil difilter.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tombol download hasil
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Konversi figure ke bytes untuk download
        buf = io.BytesIO()
        st.session_state['result_fig'].savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        st.download_button(
            label="💾 Download Hasil",
            data=buf,
            file_name="hasil_segmentasi.png",
            mime="image/png",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 20px;">
    <p>🔬 <strong>Morphology Counter</strong> - Aplikasi Segmentasi Objek menggunakan Operasi Morfologi</p>
    <p>Dibuat dengan ❤️ menggunakan Python, Streamlit, NumPy, dan SciPy</p>
</div>
""", unsafe_allow_html=True)
