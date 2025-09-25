# PDF/PNG Web Compression Interface

A simple, user-friendly web interface for uploading PDF or PNG files and downloading compressed PNG files under 3.6 KB.

## Features

- 🌐 **Web-based interface** - No command line needed
- 📱 **Responsive design** - Works on desktop and mobile
- 🖱️ **Drag & drop support** - Easy file uploading
- 📄 **PDF to PNG conversion** - Automatic conversion of PDF files
- 🗜️ **Smart compression** - Advanced algorithms to keep files under 3.6 KB
- ⚡ **Real-time processing** - See progress as files are processed
- 🔒 **Auto-cleanup** - Files automatically deleted after 1 hour
- 💾 **Instant download** - Automatic download with 5-second countdown

## Quick Start

### 1. Install Dependencies

First, make sure you have the required system dependencies:

```bash
# On macOS
brew install poppler ghostscript

# Install Python packages
pip3 install -r requirements.txt
```

### 2. Run the Web Server

```bash
python3 app.py
```

### 3. Access the Interface

Open your web browser and go to:
```
http://localhost:5000
```

## Usage Instructions

### For PDF Files:
1. **Upload**: Click the upload area or drag & drop your PDF file
2. **Process**: The system will automatically convert the first page to PNG and compress it
3. **Download**: Your compressed PNG file will be ready for download in seconds

### For PNG Files:
1. **Upload**: Click the upload area or drag & drop your PNG file
2. **Compress**: The system will compress your PNG to under 3.6 KB
3. **Download**: Get your compressed file ready for bank upload

## File Requirements

- **Supported formats**: PDF, PNG
- **Maximum file size**: 50 MB
- **Output format**: PNG (always)
- **Target size**: Under 3.6 KB (3,686 bytes)

## How It Works

### PDF Processing:
1. Converts first page of PDF to image (150 DPI)
2. Applies progressive compression:
   - Dimension scaling (100% → 20%)
   - Color reduction (256 → 8 colors)
   - Black & white conversion (if needed)
3. Optimizes PNG encoding

### PNG Processing:
1. Analyzes current file size
2. If already under 3.6 KB, copies as-is
3. If larger, applies compression:
   - Smart resizing with quality preservation
   - Color palette reduction
   - Extreme compression for large files

## Web Interface Features

### Upload Page (`/`)
- Modern, responsive design
- Drag & drop file upload
- File type validation
- File size preview
- Progress indicators

### Download Page (`/download/<filename>`)
- File details display
- Auto-download countdown (5 seconds)
- Manual download button
- "Compress another file" option
- Bank upload tips

### Additional Features
- Flash messages for success/error feedback
- Automatic file cleanup (`/cleanup` endpoint)
- Secure filename handling
- Unique file IDs to prevent conflicts

## Configuration

### Change Port (default: 5000):
Edit `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Change to desired port
```

### Change File Size Limits:
Edit `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
```

### Change Target Compression Size:
Edit compression functions in `app.py`:
```python
compressed_image = compress_png_image(image, target_size_kb=2.5)  # Smaller target
```

## Security Features

- **File type validation**: Only PDF and PNG files accepted
- **Secure filenames**: Werkzeug secure_filename() used
- **Unique IDs**: UUID-based file naming prevents conflicts
- **Auto-cleanup**: Files deleted after 1 hour
- **Size limits**: 50MB max upload size
- **Local processing**: All processing happens locally

## Troubleshooting

### Common Issues:

**Error: "No module named 'flask'"**
```bash
pip3 install flask
```

**Error: "pdf2image not found"**
```bash
pip3 install pdf2image
brew install poppler  # macOS
```

**Error: "PIL not found"**
```bash
pip3 install pillow
```

**Port already in use:**
- Change the port number in `app.py`
- Or kill the existing process: `lsof -ti:5000 | xargs kill -9`

### File Processing Issues:

**PDF conversion fails:**
- Ensure poppler is installed: `brew install poppler`
- Check PDF is not corrupted or password-protected

**Compression not achieving target size:**
- Very complex images may not compress to 3.6 KB
- Try the original command-line scripts for more control
- Consider reducing the target size in the code

**Files not downloading:**
- Check browser security settings
- Try a different browser
- Ensure popup blocker isn't interfering

## Comparison with Command Line Tools

| Feature | Web Interface | Command Line |
|---------|---------------|--------------|
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Batch processing | ❌ | ✅ |
| Customization | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| File management | ⭐⭐⭐⭐ | ⭐⭐ |
| Remote access | ✅ | ❌ |
| Mobile friendly | ✅ | ❌ |

## Technical Details

### Framework: Flask (Python)
- Lightweight web framework
- Template rendering with Jinja2
- File upload handling
- Session management for flash messages

### Frontend: HTML5/CSS3/JavaScript
- Modern responsive design
- CSS Grid and Flexbox layouts
- Drag & drop API
- Progress indicators and animations

### Image Processing: PIL (Pillow)
- High-quality image manipulation
- Multiple compression algorithms
- Color space conversions
- Format optimization

### PDF Processing: pdf2image
- Converts PDF pages to images
- Configurable DPI settings
- First page extraction
- Cross-platform compatibility

## API Endpoints

- `GET /` - Main upload page
- `POST /upload` - Handle file upload and processing
- `GET /download/<filename>` - Download compressed file
- `GET /cleanup` - Manual cleanup of old files

## File Structure

```
pdf_to_png/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html        # Upload page template
│   └── download.html     # Download page template
├── uploads/              # Temporary upload storage (auto-created)
├── outputs/              # Processed files storage (auto-created)
├── README.md            # Original CLI documentation
└── WEB_INTERFACE.md     # This file
```

## Production Deployment

For production use, consider:

1. **Use a WSGI server** (Gunicorn, uWSGI)
2. **Add HTTPS** (SSL certificate)
3. **Set up reverse proxy** (nginx, Apache)
4. **Configure monitoring** (logs, performance)
5. **Add rate limiting** (prevent abuse)
6. **Set up backup** (for critical files)

Example production command:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Support

If you encounter any issues:

1. Check the console output for error messages
2. Verify all dependencies are installed
3. Test with a simple, small file first
4. Check file permissions in upload/output directories
5. Try the original command-line tools to isolate the issue

---

**Created for bank document upload requirements**  
**Maximum file size: 3.6 KB**  
**Optimized for signature and form compression**