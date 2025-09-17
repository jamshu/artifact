#!/usr/bin/env python3
"""
PNG File Compressor
Compresses existing PNG files to under 3.6KB while maintaining acceptable quality
"""

import os
import sys
from PIL import Image
import glob
import shutil
from pathlib import Path

def get_file_size_kb(file_path):
    """Get file size in KB"""
    return os.path.getsize(file_path) / 1024

def compress_png_file(image, target_size_kb=3.5, min_dimension=50):
    """
    Compress PNG image to target size
    """
    print(f"    Starting compression (target: {target_size_kb}KB)")
    
    # Convert to RGB if needed (but preserve transparency if it's important)
    original_mode = image.mode
    if image.mode in ('CMYK',):
        image = image.convert('RGB')
    elif image.mode == 'P':
        # Convert palette to RGBA to preserve transparency
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
        
        print(f"      Trying dimensions: {new_width}x{new_height} (scale: {scale:.2f})")
        
        # Try different color reductions
        for colors in color_steps:
            try:
                temp_path = "temp_compress_png.png"
                
                if colors <= 256:
                    # Convert to palette mode with limited colors
                    if resized_image.mode == 'RGBA':
                        # Handle transparency
                        palette_image = resized_image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
                    else:
                        palette_image = resized_image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
                else:
                    palette_image = resized_image
                
                # Save with maximum PNG optimization
                palette_image.save(temp_path, format='PNG', optimize=True)
                
                current_size = get_file_size_kb(temp_path)
                
                if current_size <= target_size_kb:
                    print(f"        ✅ Success! Colors: {colors}, Size: {current_size:.2f} KB")
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
                print(f"        Error with {colors} colors: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                continue
        
        # If we found something acceptable, break early
        if best_size <= target_size_kb:
            break
    
    # If still too large, try extreme compression (black & white)
    if best_size > target_size_kb:
        print("      Applying extreme compression (B&W)...")
        
        extreme_scales = [0.3, 0.25, 0.2, 0.15, 0.1]
        
        for scale in extreme_scales:
            try:
                new_width = max(min_dimension, int(original_width * scale))
                new_height = max(min_dimension, int(original_height * scale))
                
                # Very small image
                extreme_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to 1-bit (black and white)
                bw_image = extreme_image.convert('1')
                
                temp_path = "temp_extreme_png.png"
                bw_image.save(temp_path, format='PNG', optimize=True)
                
                current_size = get_file_size_kb(temp_path)
                print(f"        B&W {new_width}x{new_height}: {current_size:.2f} KB")
                
                if current_size <= target_size_kb:
                    print(f"        ✅ Success with B&W compression!")
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
                print(f"        Error with B&W compression: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                continue
    
    print(f"      Best achieved: {best_size:.2f} KB")
    return best_image if best_image else image

def compress_png(png_path, output_dir="compressed_pngs", backup=True):
    """Compress a PNG file"""
    print(f"\nProcessing: {os.path.basename(png_path)}")
    
    try:
        # Get original file size
        original_size = get_file_size_kb(png_path)
        print(f"  Original size: {original_size:.2f} KB")
        
        # If already under target, just copy it
        if original_size <= 3.6:
            print("  ✅ Already under 3.6 KB - copying as is")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(png_path))
            shutil.copy2(png_path, output_path)
            return True
        
        # Load the image
        image = Image.open(png_path)
        print(f"  Original dimensions: {image.size}")
        print(f"  Original mode: {image.mode}")
        
        # Compress the image
        compressed_image = compress_png_file(image, target_size_kb=3.5)
        
        if compressed_image is None:
            print("  ❌ Compression failed")
            return False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create backup if requested
        if backup:
            backup_dir = os.path.join(output_dir, "originals")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, os.path.basename(png_path))
            shutil.copy2(png_path, backup_path)
            print(f"  📋 Backup saved: {backup_path}")
        
        # Save compressed image
        output_path = os.path.join(output_dir, os.path.basename(png_path))
        compressed_image.save(output_path, format='PNG', optimize=True)
        
        final_size = get_file_size_kb(output_path)
        print(f"  Final size: {final_size:.2f} KB")
        print(f"  Compression ratio: {((original_size - final_size) / original_size * 100):.1f}%")
        
        if final_size <= 3.6:
            print("  ✅ Success: File size is under 3.6 KB")
            return True
        else:
            print("  ⚠️  Warning: File size is still over 3.6 KB")
            return False
        
    except Exception as e:
        print(f"  ❌ Error processing {png_path}: {str(e)}")
        return False

def main():
    """Main function to process PNG files"""
    print("PNG File Compressor (Max 3.6KB)")
    print("=" * 40)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Process specific files mentioned in command line
        png_files = []
        for arg in sys.argv[1:]:
            if os.path.isfile(arg) and arg.lower().endswith('.png'):
                png_files.append(arg)
            elif os.path.isfile(arg + '.png'):
                png_files.append(arg + '.png')
        
        if not png_files:
            print("No valid PNG files found in arguments.")
            print("Usage: python3 compress_png.py [file1.png] [file2.png] ...")
            return
    else:
        # Find all PNG files in current directory
        png_files = glob.glob("*.png")
    
    if not png_files:
        print("No PNG files found.")
        print("Usage: python3 compress_png.py [file1.png] [file2.png] ...")
        return
    
    print(f"Found {len(png_files)} PNG file(s)")
    
    success_count = 0
    for png_file in png_files:
        if compress_png(png_file):
            success_count += 1
    
    print(f"\n" + "=" * 40)
    print(f"Compression complete!")
    print(f"Successfully processed: {success_count}/{len(png_files)} files")
    print("Check the 'compressed_pngs' directory for output files.")
    print("Original files are backed up in 'compressed_pngs/originals'")
    
    # List the compressed files with their sizes
    if os.path.exists("compressed_pngs"):
        print("\nFinal file sizes:")
        for png_file in glob.glob("compressed_pngs/*.png"):
            if os.path.exists(png_file):
                file_size = get_file_size_kb(png_file)
                status = "✅" if file_size <= 3.6 else "⚠️"
                print(f"  {status} {os.path.basename(png_file)}: {file_size:.2f} KB")

if __name__ == "__main__":
    main()
