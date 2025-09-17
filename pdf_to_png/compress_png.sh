#!/bin/bash

# PNG File Compressor using ImageMagick
# Compresses PNG files to under 3.6KB

echo "PNG File Compressor (ImageMagick)"
echo "================================="

# Check if ImageMagick is installed
if ! command -v magick &> /dev/null && ! command -v convert &> /dev/null; then
    echo "ImageMagick not found. Please install it first:"
    echo "brew install imagemagick"
    exit 1
fi

# Create output directory
mkdir -p compressed_pngs
mkdir -p compressed_pngs/originals

# Counter for successful conversions
success_count=0
total_count=0

# Function to compress a single PNG file
compress_png() {
    local input_file="$1"
    local base_name=$(basename "$input_file" .png)
    local output_file="compressed_pngs/${base_name}.png"
    local backup_file="compressed_pngs/originals/${base_name}.png"
    
    echo ""
    echo "Processing: $input_file"
    
    # Get original size
    original_size=$(stat -f%z "$input_file" 2>/dev/null || stat -c%s "$input_file" 2>/dev/null)
    original_size_kb=$((original_size / 1024))
    echo "  Original size: ${original_size_kb} KB"
    
    # If already small enough, just copy
    if [ $original_size -le 3686 ]; then
        echo "  ✅ Already under 3.6 KB - copying as is"
        cp "$input_file" "$output_file"
        cp "$input_file" "$backup_file"
        return 0
    fi
    
    # Create backup
    cp "$input_file" "$backup_file"
    echo "  📋 Backup created"
    
    # Try progressive compression
    local attempt=1
    local max_attempts=8
    
    while [ $attempt -le $max_attempts ]; do
        case $attempt in
            1) 
                # Light compression - 80% size, 256 colors
                magick "$input_file" -resize 80%x80% -colors 256 -strip -quality 90 "$output_file" 2>/dev/null
                ;;
            2) 
                # Medium compression - 70% size, 128 colors
                magick "$input_file" -resize 70%x70% -colors 128 -strip -quality 80 "$output_file" 2>/dev/null
                ;;
            3) 
                # Heavy compression - 60% size, 64 colors
                magick "$input_file" -resize 60%x60% -colors 64 -strip -quality 70 "$output_file" 2>/dev/null
                ;;
            4) 
                # Aggressive compression - 50% size, 32 colors
                magick "$input_file" -resize 50%x50% -colors 32 -strip -quality 60 "$output_file" 2>/dev/null
                ;;
            5) 
                # Very aggressive - 40% size, 16 colors
                magick "$input_file" -resize 40%x40% -colors 16 -strip -quality 50 "$output_file" 2>/dev/null
                ;;
            6) 
                # Ultra aggressive - 30% size, 8 colors
                magick "$input_file" -resize 30%x30% -colors 8 -strip -quality 40 "$output_file" 2>/dev/null
                ;;
            7) 
                # Extreme - 25% size, 4 colors
                magick "$input_file" -resize 25%x25% -colors 4 -strip -quality 30 "$output_file" 2>/dev/null
                ;;
            8) 
                # Last resort - 20% size, monochrome
                magick "$input_file" -resize 20%x20% -monochrome -strip "$output_file" 2>/dev/null
                ;;
        esac
        
        if [ -f "$output_file" ]; then
            file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
            file_size_kb=$((file_size / 1024))
            echo "  Attempt $attempt: ${file_size_kb} KB"
            
            if [ $file_size -le 3686 ]; then
                echo "  ✅ Success: Final size ${file_size_kb} KB (under 3.6 KB)"
                local compression_ratio=$(( (original_size - file_size) * 100 / original_size ))
                echo "  Compression ratio: ${compression_ratio}%"
                return 0
            fi
        else
            echo "  ⚠️  Attempt $attempt failed"
        fi
        
        attempt=$((attempt + 1))
    done
    
    if [ -f "$output_file" ]; then
        file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
        file_size_kb=$((file_size / 1024))
        echo "  ⚠️  Warning: Final size ${file_size_kb} KB (still over 3.6 KB)"
        echo "     This is the best compression achievable"
        return 1
    else
        echo "  ❌ Error: Compression failed completely"
        return 1
    fi
}

# Process files based on arguments or find all PNG files
if [ $# -gt 0 ]; then
    # Process specific files from command line
    for file in "$@"; do
        if [ -f "$file" ] && [[ "$file" =~ \\.png$ ]]; then
            if compress_png "$file"; then
                success_count=$((success_count + 1))
            fi
            total_count=$((total_count + 1))
        else
            echo "Warning: '$file' is not a valid PNG file"
        fi
    done
else
    # Process all PNG files in current directory
    png_found=false
    for png_file in *.png; do
        if [ -f "$png_file" ]; then
            png_found=true
            if compress_png "$png_file"; then
                success_count=$((success_count + 1))
            fi
            total_count=$((total_count + 1))
        fi
    done
    
    if [ "$png_found" = false ]; then
        echo "No PNG files found in current directory."
        echo "Usage: $0 [file1.png] [file2.png] ..."
        exit 0
    fi
fi

echo ""
echo "================================="
echo "Compression complete!"
echo "Successfully processed: $success_count/$total_count files"
echo "Compressed files are in the 'compressed_pngs' directory"
echo "Original files are backed up in 'compressed_pngs/originals'"

# List results
if [ $total_count -gt 0 ]; then
    echo ""
    echo "Final file sizes:"
    for png_file in compressed_pngs/*.png; do
        if [ -f "$png_file" ]; then
            file_size=$(stat -f%z "$png_file" 2>/dev/null || stat -c%s "$png_file" 2>/dev/null)
            file_size_kb=$((file_size / 1024))
            if [ $file_size -le 3686 ]; then
                status="✅"
            else
                status="⚠️"
            fi
            echo "  $status $(basename "$png_file"): ${file_size_kb} KB"
        fi
    done
fi
