#!/usr/bin/env python3
"""
Ultra-Aggressive PDF to PNG Converter
Converts PDF files to PNG format while keeping file size UNDER 3.6KB
Uses multiple compression strategies including dimension reduction, color reduction, and quality optimization
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

def ultra_compress_image(image, target_size_kb=3.5, min_dimension=80):
    """
    Ultra-aggressive compression to meet 3.6KB target
    """
    print(f"  Starting ultra compression (target: {target_size_kb}KB)")
    
    # Convert to RGB if needed
    if image.mode in ('CMYK', 'P', 'RGBA'):
        image = image.convert('RGB')
    
    # Start with very aggressive settings
    max_dimension = 400  # Start smaller
    quality_steps = [90, 80, 70, 60, 50, 40, 30, 20, 10]
    color_steps = [256, 128, 64, 32, 16, 8]
    
    best_image = None
    best_size = float('inf')
    
    for max_dim in [400, 300, 250, 200, 150, 120, 100]:
        # Resize image
        width, height = image.size
        if width > max_dim or height > max_dim:
            ratio = min(max_dim/width, max_dim/height)
            new_width = max(min_dimension, int(width * ratio))
            new_height = max(min_dimension, int(height * ratio))
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized_image = image.copy()
        
        print(f"    Trying dimensions: {resized_image.size}")
        
        # Try different color reductions
        for colors in color_steps:
            try:
                # Convert to palette mode with limited colors
                if colors <= 256:
                    palette_image = resized_image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
                else:
                    palette_image = resized_image
                
                # Save with PNG optimization
                temp_path = "temp_ultra.png"
                palette_image.save(temp_path, format='PNG', optimize=True)
                
                current_size = get_file_size_kb(temp_path)
                print(f"      Colors: {colors}, Size: {current_size:.2f} KB")
                
                if current_size <= target_size_kb:
                    print(f"    ✅ Success with {colors} colors!")
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
                print(f"      Error with {colors} colors: {e}")
                continue
        
        # If we found something under target, use it
        if best_size <= target_size_kb:
            break
    
    # If still too large, try even more extreme measures
    if best_size > target_size_kb:
        print("    Applying extreme compression...")
        
        # Use the smallest acceptable dimensions
        extreme_sizes = [100, 80, 60, 50, 40]
        
        for size in extreme_sizes:
            try:
                # Very small image
                extreme_image = image.resize((size, int(size * image.size[1] / image.size[0])), Image.Resampling.LANCZOS)
                
                # Convert to 1-bit (black and white)
                bw_image = extreme_image.convert('1')
                
                temp_path = "temp_extreme.png"
                bw_image.save(temp_path, format='PNG', optimize=True)
                
                current_size = get_file_size_kb(temp_path)
                print(f"      Extreme {size}px B&W: {current_size:.2f} KB")
                
                if current_size <= target_size_kb:
                    print(f"    ✅ Success with extreme compression!")
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
                print(f"      Error with extreme compression: {e}")
                continue
    
    print(f"    Best achieved: {best_size:.2f} KB")
    return best_image if best_image else image

def convert_pdf_to_png(pdf_path, output_dir="converted_pngs"):
    """Convert a PDF file to ultra-compressed PNG"""
    print(f"\nProcessing: {os.path.basename(pdf_path)}")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images (using first page only, lower DPI for smaller initial size)
        pages = convert_from_path(pdf_path, dpi=100, first_page=1, last_page=1)
        
        if not pages:
            print(f"  Error: Could not convert {pdf_path}")
            return False
        
        # Get the first page
        image = pages[0]
        print(f"  Original image size: {image.size}")
        
        # Ultra compress the image
        compressed_image = ultra_compress_image(image, target_size_kb=3.5)
        
        if compressed_image is None:
            print("  Error: Compression failed")
            return False
        
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
            return True
        else:
            print("  ⚠️  Warning: File size is still over 3.6 KB")
            return False
        
    except Exception as e:
        print(f"  Error converting {pdf_path}: {str(e)}")
        return False

def main():
    """Main function to process all PDF files"""
    print("Ultra-Aggressive PDF to PNG Converter (Max 3.6KB)")
    print("=" * 50)
    
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
    
    print(f"\n" + "=" * 50)
    print(f"Conversion complete!")
    print(f"Successfully converted: {success_count}/{len(pdf_files)} files")
    print("Check the 'converted_pngs' directory for output files.")
    
    # List the converted files with their sizes
    if success_count > 0 or os.path.exists("converted_pngs"):
        print("\nFile sizes:")
        for png_file in glob.glob("converted_pngs/*.png"):
            if os.path.exists(png_file):
                file_size = get_file_size_kb(png_file)
                status = "✅" if file_size <= 3.6 else "⚠️"
                print(f"  {status} {os.path.basename(png_file)}: {file_size:.2f} KB")

if __name__ == "__main__":
    main()
