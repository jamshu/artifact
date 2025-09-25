#!/usr/bin/env python3
"""
Simple Web Interface for PDF to PNG Conversion and PNG Compression
Provides an easy-to-use web interface for uploading and compressing files
"""

import os
import tempfile
import shutil
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid

# Import functions from existing scripts
from PIL import Image
from pdf2image import convert_from_path

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Create necessary directories
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_kb(file_path):
    """Get file size in KB"""
    return os.path.getsize(file_path) / 1024

def compress_png_image(image, target_size_kb=3.0, min_dimension=50):
    """
    Compress PNG image to target size - adapted from compress_png.py
    """
    print(f"Starting compression (target: {target_size_kb}KB)")
    
    # Convert to RGB if needed (but preserve transparency if it's important)
    if image.mode in ('CMYK',):
        image = image.convert('RGB')
    elif image.mode == 'P':
        image = image.convert('RGBA')
    
    best_image = None
    best_size = float('inf')
    
    # Try different dimension reductions
    dimension_steps = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2]
    color_steps = [256, 128, 64, 32, 16, 8]
    
    original_width, original_height = image.size
    
    for scale in dimension_steps:
        # Calculate new dimensions
        new_width = max(min_dimension, int(original_width * scale))
        new_height = max(min_dimension, int(original_height * scale))
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Try different color reductions
        for colors in color_steps:
            try:
                temp_path = f"temp_compress_{uuid.uuid4().hex}.png"
                
                if colors <= 256:
                    # Convert to palette mode with limited colors
                    if resized_image.mode == 'RGBA':
                        # For RGBA images, use FASTOCTREE method
                        palette_image = resized_image.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
                    else:
                        palette_image = resized_image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
                else:
                    palette_image = resized_image
                
                # Save with maximum PNG optimization
                palette_image.save(temp_path, format='PNG', optimize=True)
                
                current_size = get_file_size_kb(temp_path)
                
                if current_size <= target_size_kb:
                    best_image = Image.open(temp_path)
                    best_image.load()
                    os.remove(temp_path)
                    return best_image
                
                if current_size < best_size:
                    best_size = current_size
                    if best_image:
                        best_image.close()
                    best_image = Image.open(temp_path)
                    best_image.load()
                
                os.remove(temp_path)
                
            except Exception as e:
                print(f"Error with {colors} colors: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                continue
        
        # If we found something acceptable, break early
        if best_size <= target_size_kb:
            break
    
    # If still too large, try extreme compression (black & white)
    if best_size > target_size_kb:
        print("Applying extreme compression (B&W)...")
        
        extreme_scales = [0.3, 0.25, 0.2, 0.15, 0.1]
        
        for scale in extreme_scales:
            try:
                new_width = max(min_dimension, int(original_width * scale))
                new_height = max(min_dimension, int(original_height * scale))
                
                # Very small image
                extreme_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to 1-bit (black and white)
                bw_image = extreme_image.convert('1')
                
                temp_path = f"temp_extreme_{uuid.uuid4().hex}.png"
                bw_image.save(temp_path, format='PNG', optimize=True)
                
                current_size = get_file_size_kb(temp_path)
                
                if current_size <= target_size_kb:
                    final_image = Image.open(temp_path)
                    final_image.load()
                    os.remove(temp_path)
                    return final_image
                
                if current_size < best_size:
                    best_size = current_size
                    if best_image:
                        best_image.close()
                    best_image = Image.open(temp_path)
                    best_image.load()
                
                os.remove(temp_path)
                
            except Exception as e:
                print(f"Error with B&W compression: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                continue
    
    return best_image if best_image else image

def convert_pdf_to_compressed_png(pdf_path, output_path):
    """
    Convert PDF to compressed PNG - adapted from convert_pdf_to_png.py
    """
    try:
        # Convert PDF to images (using first page only)
        pages = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
        
        if not pages:
            return False, "Could not convert PDF"
        
        # Get the first page
        image = pages[0]
        
        # Compress the image
        compressed_image = compress_png_image(image, target_size_kb=3.0)
        
        if compressed_image is None:
            return False, "Compression failed"
        
        # Save the final compressed image
        compressed_image.save(output_path, format='PNG', optimize=True)
        
        final_size = get_file_size_kb(output_path)
        success = final_size <= 3.6
        
        return success, f"Converted to PNG ({final_size:.2f} KB)"
        
    except Exception as e:
        return False, f"Error converting PDF: {str(e)}"

def compress_existing_png(input_path, output_path):
    """
    Compress existing PNG file - adapted from compress_png.py
    """
    try:
        # Get original file size
        original_size = get_file_size_kb(input_path)
        
        # If already under target, just copy it
        if original_size <= 3.6:
            shutil.copy2(input_path, output_path)
            return True, f"Already compressed ({original_size:.2f} KB)"
        
        # Load the image
        image = Image.open(input_path)
        
        # Compress the image
        compressed_image = compress_png_image(image, target_size_kb=3.0)
        
        if compressed_image is None:
            return False, "Compression failed"
        
        # Save compressed image
        compressed_image.save(output_path, format='PNG', optimize=True)
        
        final_size = get_file_size_kb(output_path)
        compression_ratio = ((original_size - final_size) / original_size * 100)
        success = final_size <= 3.6
        
        return success, f"Compressed from {original_size:.2f} KB to {final_size:.2f} KB ({compression_ratio:.1f}% reduction)"
        
    except Exception as e:
        return False, f"Error compressing PNG: {str(e)}"

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Generate unique filenames
        unique_id = uuid.uuid4().hex
        input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
        
        # Save uploaded file
        file.save(input_path)
        
        # Determine output filename
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_compressed.png"
        output_path = os.path.join(OUTPUT_FOLDER, f"{unique_id}_{output_filename}")
        
        # Process the file based on its type
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'pdf':
            success, message = convert_pdf_to_compressed_png(input_path, output_path)
        elif file_extension == 'png':
            success, message = compress_existing_png(input_path, output_path)
        
        # Clean up uploaded file
        os.remove(input_path)
        
        if success:
            file_size = get_file_size_kb(output_path)
            flash(f'Success! {message}')
            return render_template('download.html', 
                                 filename=output_filename, 
                                 filepath=f"{unique_id}_{output_filename}",
                                 filesize=f"{file_size:.2f}")
        else:
            flash(f'Error: {message}')
            return redirect(url_for('index'))
    
    else:
        flash('Invalid file type. Please upload PDF or PNG files only.')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download the compressed file"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename.split('_', 1)[1])
    else:
        flash('File not found or expired')
        return redirect(url_for('index'))

@app.route('/cleanup')
def cleanup():
    """Clean up old files (optional endpoint for maintenance)"""
    try:
        # Remove files older than 1 hour
        import time
        current_time = time.time()
        
        for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
        
        return "Cleanup completed"
    except Exception as e:
        return f"Cleanup error: {str(e)}"

if __name__ == '__main__':
    print("PDF/PNG Compression Web Interface")
    print("=" * 40)
    print("Access the web interface at: http://localhost:5000")
    print("Upload PDF or PNG files and download compressed PNG files")
    print("Target file size: Under 3.6 KB")
    print("=" * 40)
    
    app.run(debug=True, host='0.0.0.0', port=8090)