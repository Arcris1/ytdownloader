from flask import Flask, request, jsonify, render_template, send_from_directory
from yt_dlp import YoutubeDL
import os
import json
from datetime import datetime

app = Flask(__name__)

# Directory to save downloads
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
@app.route("/download", methods=["POST"])
def download_video():
    """
    POST /download
    Body: {"url": "...", "format": "mp4|mp3|best", "download_type": "video|playlist"}
    Downloads the video/playlist and returns result.
    """
    data = request.get_json()
    
    if not data or not data.get("url"):
        return jsonify({"error": "Missing 'url' in request body"}), 400

    url = data.get("url")
    format_type = data.get("format", "mp4")
    quality = data.get("quality", "best")
    download_type = data.get("download_type", "video")

    # Configure download options based on format
    if format_type == "mp3":
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(playlist_title)s/%(title)s.%(ext)s") if download_type == "playlist" else os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    elif format_type == "mp4":
        if quality == "720p":
            format_selector = "best[height<=720]"
        elif quality == "1080p":
            format_selector = "best[height<=1080]"
        else:
            format_selector = "bestvideo+bestaudio/best"
            
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(playlist_title)s/%(title)s.%(ext)s") if download_type == "playlist" else os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": format_selector,
            "merge_output_format": "mp4",
        }
    else:
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(playlist_title)s/%(title)s.%(ext)s") if download_type == "playlist" else os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": "bestvideo+bestaudio/best",
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # Get info first
            
            if download_type == "playlist" or info.get("_type") == "playlist":
                # Playlist download
                playlist_title = info.get("title", "Unknown playlist")
                video_count = len(info.get("entries", []))
                
                # Now download the playlist
                ydl.extract_info(url, download=True)
                
                # Save playlist to history
                history_entry = {
                    "title": f"Playlist: {playlist_title}",
                    "url": url,
                    "format": format_type,
                    "quality": quality,
                    "type": "playlist",
                    "video_count": video_count,
                    "filename": f"Playlist folder: {playlist_title}",
                    "timestamp": datetime.now().isoformat()
                }
                save_to_history(history_entry)
                
                return jsonify({
                    "title": playlist_title,
                    "type": "playlist",
                    "video_count": video_count,
                    "status": "success",
                    "message": f"Downloaded {video_count} videos from playlist"
                })
            else:
                # Single video download
                title = info.get("title", "Unknown title")
                duration = info.get("duration", 0)
                thumbnail = info.get("thumbnail", "")
                
                # Now download
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Save download history
                history_entry = {
                    "title": title,
                    "url": url,
                    "format": format_type,
                    "quality": quality,
                    "type": "video",
                    "duration": duration,
                    "thumbnail": thumbnail,
                    "filename": os.path.basename(filename),
                    "timestamp": datetime.now().isoformat()
                }
                save_to_history(history_entry)

                return jsonify({
                    "title": title,
                    "file": os.path.basename(filename),
                    "duration": duration,
                    "thumbnail": thumbnail,
                    "type": "video",
                    "status": "success"
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/info", methods=["POST"])
def get_video_info():
    """Get video or playlist information without downloading"""
    data = request.get_json()
    
    if not data or not data.get("url"):
        return jsonify({"error": "Missing 'url' in request body"}), 400

    url = data.get("url")
    
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,  # For playlists, only get basic info
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist
            if info.get("_type") == "playlist":
                playlist_info = {
                    "type": "playlist",
                    "title": info.get("title", "Unknown playlist"),
                    "uploader": info.get("uploader", "Unknown"),
                    "description": info.get("description", "")[:200] + "..." if info.get("description", "") else "",
                    "video_count": len(info.get("entries", [])),
                    "videos": []
                }
                
                # Get first few videos info for preview
                entries = info.get("entries", [])[:5]  # Show first 5 videos
                for entry in entries:
                    if entry:
                        playlist_info["videos"].append({
                            "title": entry.get("title", "Unknown title"),
                            "duration": entry.get("duration", 0),
                            "url": entry.get("url", "")
                        })
                
                playlist_info["status"] = "success"
                return jsonify(playlist_info)
            else:
                # Single video
                return jsonify({
                    "type": "video",
                    "title": info.get("title", "Unknown title"),
                    "duration": info.get("duration", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "uploader": info.get("uploader", "Unknown"),
                    "view_count": info.get("view_count", 0),
                    "upload_date": info.get("upload_date", ""),
                    "description": info.get("description", "")[:200] + "..." if info.get("description", "") else "",
                    "status": "success"
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def save_to_history(entry):
    """Save download entry to history file"""
    history_file = os.path.join(DOWNLOAD_FOLDER, "history.json")
    history = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    history.insert(0, entry)  # Add to beginning
    history = history[:50]  # Keep only last 50 entries
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

@app.route("/history", methods=["GET"])
def get_history():
    """Get download history"""
    history_file = os.path.join(DOWNLOAD_FOLDER, "history.json")
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            return jsonify({"history": history, "status": "success"})
        except:
            return jsonify({"history": [], "status": "success"})
    
    return jsonify({"history": [], "status": "success"})

@app.route("/downloads/<filename>")
def download_file(filename):
    """Serve downloaded files"""
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route("/downloads/playlist/<playlist_name>")
def list_playlist_files(playlist_name):
    """List files in a playlist folder"""
    playlist_path = os.path.join(DOWNLOAD_FOLDER, playlist_name)
    
    if not os.path.exists(playlist_path):
        return jsonify({"error": "Playlist folder not found"}), 404
    
    files = []
    for filename in os.listdir(playlist_path):
        if os.path.isfile(os.path.join(playlist_path, filename)):
            files.append({
                "name": filename,
                "path": f"/downloads/playlist/{playlist_name}/{filename}"
            })
    
    return jsonify({"files": files, "status": "success"})

@app.route("/downloads/playlist/<playlist_name>/<filename>")
def download_playlist_file(playlist_name, filename):
    """Serve files from playlist folder"""
    playlist_path = os.path.join(DOWNLOAD_FOLDER, playlist_name)
    return send_from_directory(playlist_path, filename, as_attachment=True)


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
