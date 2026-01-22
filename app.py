import os
import uuid
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import measurements, morphology
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Pastikan folder uploads ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def process_image(image_data, kernel_size=(9, 5), iterations=2, threshold=128):
    """Proses gambar dengan operasi morfologi"""
    try:
        # Buka gambar dan konversi ke array
        if isinstance(image_data, str):
            # Jika berupa path file
            im = np.array(Image.open(image_data).convert('L'))
        else:
            # Jika berupa data gambar langsung
            im = np.array(Image.open(BytesIO(image_data)).convert('L'))
        
        # Binarisasi
        im_binary = (im < threshold).astype(np.uint8) * 255
        
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
        
        # Visualisasi
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Gambar asli
        axes[0, 0].imshow(im, cmap='gray')
        axes[0, 0].set_title('Gambar Asli')
        axes[0, 0].axis('off')
        
        # Gambar biner
        axes[0, 1].imshow(im_binary, cmap='gray')
        axes[0, 1].set_title(f'Biner (Threshold={threshold})')
        axes[0, 1].axis('off')
        
        # Label sebelum opening
        axes[0, 2].imshow(labels_before, cmap='tab20c')
        axes[0, 2].set_title(f'Label Sebelum Opening\n{nbr_objects_before} objek')
        axes[0, 2].axis('off')
        
        # Gambar setelah opening
        axes[1, 0].imshow(im_opened, cmap='gray')
        axes[1, 0].set_title('Setelah Opening')
        axes[1, 0].axis('off')
        
        # Label setelah opening
        axes[1, 1].imshow(labels_after, cmap='tab20c')
        axes[1, 1].set_title(f'Label Setelah Opening\n{nbr_objects_after} objek')
        axes[1, 1].axis('off')
        
        # Perbandingan
        axes[1, 2].bar(['Sebelum', 'Sesudah'], [nbr_objects_before, nbr_objects_after])
        axes[1, 2].set_title('Perbandingan Jumlah Objek')
        axes[1, 2].set_ylabel('Jumlah Objek')
        
        plt.tight_layout()
        
        # Konversi plot ke gambar base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'success': True,
            'image_base64': image_base64,
            'nbr_objects_before': int(nbr_objects_before),
            'nbr_objects_after': int(nbr_objects_after),
            'stats': {
                'threshold': threshold,
                'kernel_size': kernel_size,
                'iterations': iterations
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    """Halaman utama"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """Endpoint untuk memproses gambar"""
    try:
        # Cek apakah file diupload
        if 'image' not in request.files:
            return jsonify({'error': 'Tidak ada file yang diupload'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'Nama file kosong'}), 400
        
        # Validasi ekstensi file
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
        if not '.' in file.filename or \
           not file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
            return jsonify({'error': 'Format file tidak didukung'}), 400
        
        # Baca file
        image_data = file.read()
        
        # Ambil parameter dari form
        try:
            threshold = int(request.form.get('threshold', 128))
            kernel_x = int(request.form.get('kernel_x', 9))
            kernel_y = int(request.form.get('kernel_y', 5))
            iterations = int(request.form.get('iterations', 2))
        except ValueError:
            return jsonify({'error': 'Parameter tidak valid'}), 400
        
        # Proses gambar
        result = process_image(
            image_data, 
            kernel_size=(kernel_x, kernel_y),
            iterations=iterations,
            threshold=threshold
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/demo')
def demo():
    """Endpoint untuk demo dengan gambar contoh"""
    try:
        # Gunakan gambar contoh (atau upload gambar default)
        demo_image_path = 'static/demo_image.png'
        
        # Jika tidak ada gambar demo, buat gambar sederhana
        if not os.path.exists(demo_image_path):
            # Buat gambar demo dengan beberapa lingkaran
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.set_facecolor('white')
            
            # Gambar beberapa lingkaran sebagai objek
            circles = [
                (0.2, 0.2, 0.05),
                (0.4, 0.3, 0.07),
                (0.7, 0.4, 0.06),
                (0.5, 0.7, 0.08),
                (0.8, 0.8, 0.05),
            ]
            
            for x, y, r in circles:
                circle = plt.Circle((x, y), r, color='black', fill=True)
                ax.add_patch(circle)
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            plt.savefig(demo_image_path, dpi=100, bbox_inches='tight', facecolor='white')
            plt.close()
        
        # Proses gambar demo
        result = process_image(demo_image_path)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
