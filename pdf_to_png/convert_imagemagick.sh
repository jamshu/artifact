#!/bin/bash

# PDF to PNG Converter using ImageMagick
# Converts PDFs to PNG files under 3.6KB

echo "PDF to PNG Converter (ImageMagick)"
echo "=================================="

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick not found. Installing with Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew not found. Please install ImageMagick manually."
        exit 1
    fi
    brew install imagemagick
fi

# Create output directory
mkdir -p converted_pngs

# Counter for successful conversions
success_count=0
total_count=0

# Process each PDF file
for pdf_file in *.pdf; do
    if [ ! -f "$pdf_file" ]; then
        echo "No PDF files found in current directory."
        exit 0
    fi
    
    echo ""
    echo "Processing: $pdf_file"
    
    # Get base filename without extension
    base_name=$(basename "$pdf_file" .pdf)
    output_file="converted_pngs/${base_name}.png"
    
    # Convert with aggressive compression settings
    # Start with low resolution and high compression
    convert "$pdf_file[0]" \
        -density 100 \
        -quality 60 \
        -colors 64 \
        -depth 8 \
        -strip \
        -resize 600x600\> \
        -compress PNG \
        "$output_file"
    
    if [ $? -eq 0 ]; then
        # Check file size
        file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
        file_size_kb=$((file_size / 1024))
        
        echo "  Initial size: ${file_size_kb} KB"
        
        # If still too large, apply more aggressive compression
        attempt=1
        max_attempts=5
        
        while [ $file_size -gt 3686 ] && [ $attempt -le $max_attempts ]; do
            echo "  Attempt $attempt: Reducing size further..."
            
            # Calculate new dimensions (reduce by 20% each time)
            reduction_factor=$(echo "scale=2; 0.8^$attempt" | bc -l)
            
            convert "$pdf_file[0]" \
                -density $((80 - attempt * 10)) \
                -quality $((50 - attempt * 5)) \
                -colors $((48 - attempt * 8)) \
                -depth 8 \
                -strip \
                -resize $(echo "600*$reduction_factor/1" | bc)x$(echo "600*$reduction_factor/1" | bc)\> \
                -compress PNG \
                "$output_file"
            
            file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
            file_size_kb=$((file_size / 1024))
            echo "    New size: ${file_size_kb} KB"
            
            attempt=$((attempt + 1))
        done
        
        # Final size check
        if [ $file_size -le 3686 ]; then
            echo "  ✅ Success: Final size ${file_size_kb} KB (under 3.6 KB)"
            success_count=$((success_count + 1))
        else
            echo "  ⚠️  Warning: Final size ${file_size_kb} KB (still over 3.6 KB)"
            echo "     You may need to manually compress this file further"
        fi
    else
        echo "  ❌ Error: Failed to convert $pdf_file"
    fi
    
    total_count=$((total_count + 1))
done

echo ""
echo "=================================="
echo "Conversion complete!"
echo "Successfully converted: $success_count/$total_count files"
echo "Output files are in the 'converted_pngs' directory"

# List the converted files with their sizes
if [ $success_count -gt 0 ]; then
    echo ""
    echo "Converted files:"
    for png_file in converted_pngs/*.png; do
        if [ -f "$png_file" ]; then
            file_size=$(stat -f%z "$png_file" 2>/dev/null || stat -c%s "$png_file" 2>/dev/null)
            file_size_kb=$((file_size / 1024))
            echo "  $(basename "$png_file"): ${file_size_kb} KB"
        fi
    done
fi
