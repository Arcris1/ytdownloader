# 🎵 YouTube Downloader - Modern & Fast

A beautiful, modern YouTube downloader with playlist support built with Flask and Tailwind CSS.

![YouTube Downloader](https://img.shields.io/badge/YouTube-Downloader-red?style=for-the-badge&logo=youtube)
![Flask](https://img.shields.io/badge/Flask-Backend-blue?style=for-the-badge&logo=flask)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=for-the-badge&logo=tailwind-css)

## ✨ Features

### 🎥 **Video & Audio Downloads**
- **High-quality MP4 video** downloads (1080p, 720p, best available)
- **Premium MP3 audio** extraction (320kbps, 192kbps, 128kbps)
- **Smart format detection** and conversion

### 📋 **Playlist Support** 
- **Complete playlist downloads** with organized folder structure
- **Playlist preview** showing video count and first 5 videos
- **Individual video selection** from playlists
- **Batch processing** for multiple videos

### 🎨 **Modern UI**
- **Beautiful dark theme** with gradient backgrounds
- **Glass morphism effects** and smooth animations
- **Fully responsive design** for all devices
- **Real-time progress indicators**

### 📊 **Smart Management**
- **Download history** with metadata tracking
- **File organization** in playlist folders
- **Direct download links** for completed files
- **Error handling** with clear feedback

## 🚀 Installation

### Prerequisites

1. **Python 3.7+** installed on your system
2. **FFmpeg** for audio conversion (required for MP3 downloads)

### Install FFmpeg

#### macOS (using Homebrew):
```bash
brew install ffmpeg
```

#### Windows:
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract and add to PATH

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

### Setup Project

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/ytdownloader.git
cd ytdownloader
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
python server.py
```

5. **Open your browser** and go to `http://localhost:5000`

## 🎯 Usage

### Single Video Download
1. Paste any YouTube video URL
2. Click "Get Video Info" to preview
3. Select format (MP4 or MP3) and quality
4. Click "Download Now"

### Playlist Download
1. Paste a YouTube playlist URL
2. Click "Analyze Playlist" to see contents
3. Choose "Entire Playlist" or "Individual Videos"
4. Select format and quality options
5. Start download and wait for completion

### Supported URLs
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/playlist?list=PLAYLIST_ID`
- `https://youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID`

## 🎵 Audio Quality Options

| Quality | Bitrate | File Size | Use Case |
|---------|---------|-----------|----------|
| **Best** | 320 kbps | Larger | Audiophile quality |
| **Standard** | 192 kbps | Medium | Balanced quality/size |
| **Compact** | 128 kbps | Smaller | Space-saving |

## 🎥 Video Quality Options

| Quality | Resolution | Use Case |
|---------|------------|----------|
| **Best Available** | Highest | Maximum quality |
| **1080p** | 1920×1080 | Full HD |
| **720p** | 1280×720 | HD, smaller files |

## ⚠️ Important Notes

### **For MP3 Downloads**
**FFmpeg is required for MP3 conversion!** 

If you get errors when downloading MP3:
1. Install FFmpeg using the instructions above
2. Restart your terminal/command prompt
3. Make sure FFmpeg is in your system PATH

### **For Format Errors**
If you encounter "Requested format is not available" errors:
1. **Try "Best Available" quality** instead of specific resolutions
2. **Use MP3 format** if you only need audio (more reliable)
3. **The app will automatically try fallback formats** if the first choice fails

### **YouTube SABR Streaming**
YouTube has implemented new streaming formats that may cause some downloads to fail. The app includes:
- **Automatic fallback options** for different format types
- **Smart error handling** with helpful suggestions
- **Multiple format attempts** to ensure successful downloads

## 📄 License

This project is for educational and personal use only. Please respect YouTube's Terms of Service and copyright laws.

---

**Made with ❤️ - Enhanced MP3 Support Ready! 🎵**
