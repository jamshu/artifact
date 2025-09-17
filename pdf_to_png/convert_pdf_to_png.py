#!/usr/bin/env python3
"""
PDF to PNG Converter with Size Compression
Converts PDF files to PNG format while keeping file size under 3.6KB
"""

import os
import sys
from PIL import Image
import glob
from pathlib import Path

try:
    from pdf2image import convert_from_path
except ImportError:
    print("pdf2image library not found. Installing...")
    os.system("pip3 install pdf2image pillow")
    from pdf2image import convert_from_path

def get_file_size_kb(file_path):
    """Get file size in KB"""
    return os.path.getsize(file_path) / 1024

def compress_image(image, target_size_kb=3.6, min_quality=10):
    """
    Compress PIL Image to target size in KB
    Returns the compressed image
    """
    # Start with reasonable dimensions and quality
    quality = 85
    width, height = image.size
    
    # If image is too large, resize it first
    max_dimension = 800
    if width > max_dimension or height > max_dimension:
        ratio = min(max_dimension/width, max_dimension/height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    while quality >= min_quality:
        # Save to temporary location to check size
        temp_path = "temp_compress.png"
        
        # Convert to RGB if necessary (PNG doesn't support CMYK)
        if image.mode in ('CMYK', 'P'):
            image = image.convert('RGB')
        
        # For PNG, we need to optimize and reduce colors
        if image.mode == 'RGBA':
            # Convert to palette mode to reduce file size
            image = image.convert('P', palette=Image.ADAPTIVE, colors=256)
        
        image.save(temp_path, format='PNG', optimize=True)
        
        current_size = get_file_size_kb(temp_path)
        print(f"  Current size: {current_size:.2f} KB (quality: {quality})")
        
        if current_size <= target_size_kb:
            # Load the compressed image and clean up temp file
            compressed_image = Image.open(temp_path)
            compressed_image.load()  # Ensure image data is loaded
            os.remove(temp_path)
            return compressed_image
        
        # If still too large, reduce dimensions further
        if quality <= min_quality + 10:
            width, height = image.size
            new_width = int(width * 0.9)
            new_height = int(height * 0.9)
            if new_width < 100 or new_height < 100:
                print("  Warning: Image dimensions getting very small")
                break
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        quality -= 10
    
    # If we couldn't compress enough, return the last attempt
    if os.path.exists(temp_path):
        compressed_image = Image.open(temp_path)
        compressed_image.load()
        os.remove(temp_path)
        return compressed_image
    
    return image

def convert_pdf_to_png(pdf_path, output_dir="converted_pngs"):
    """Convert a PDF file to PNG with size optimization"""
    print(f"\nProcessing: {os.path.basename(pdf_path)}")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images (using first page only)
        pages = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
        
        if not pages:
            print(f"  Error: Could not convert {pdf_path}")
            return False
        
        # Get the first page
        image = pages[0]
        print(f"  Original image size: {image.size}")
        
        # Compress the image
        print("  Compressing image...")
        compressed_image = compress_image(image, target_size_kb=3.6)
        
        # Generate output filename
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, f"{pdf_name}.png")
        
        # Save the final compressed image
        compressed_image.save(output_path, format='PNG', optimize=True)
        
        final_size = get_file_size_kb(output_path)
        print(f"  Final PNG saved: {output_path}")
        print(f"  Final size: {final_size:.2f} KB")
        
        if final_size <= 3.6:
            print("  ✅ Success: File size is under 3.6 KB")
        else:
            print("  ⚠️  Warning: File size is still over 3.6 KB")
        
        return True
        
    except Exception as e:
        print(f"  Error converting {pdf_path}: {str(e)}")
        return False

def main():
    """Main function to process all PDF files"""
    print("PDF to PNG Converter (Max 3.6KB)")
    print("=" * 40)
    
    # Check if running on macOS and suggest poppler installation
    if sys.platform == "darwin":
        try:
            import subprocess
            result = subprocess.run(["which", "pdftoppm"], capture_output=True)
            if result.returncode != 0:
                print("Installing required dependencies...")
                os.system("brew install poppler")
        except:
            print("Note: If conversion fails, install poppler with: brew install poppler")
    
    # Find all PDF files in current directory
    pdf_files = glob.glob("*.pdf")
    
    if not pdf_files:
        print("No PDF files found in current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    success_count = 0
    for pdf_file in pdf_files:
        if convert_pdf_to_png(pdf_file):
            success_count += 1
    
    print(f"\n" + "=" * 40)
    print(f"Conversion complete!")
    print(f"Successfully converted: {success_count}/{len(pdf_files)} files")
    print("Check the 'converted_pngs' directory for output files.")

if __name__ == "__main__":
    main()
