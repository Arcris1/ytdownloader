from flask import Flask, request, jsonify, render_template, send_from_directory
from yt_dlp import YoutubeDL
import os
import json
import subprocess
import shutil
from datetime import datetime

app = Flask(__name__)

# Directory to save downloads
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def check_ffmpeg():
    """Check if FFmpeg is available"""
    return shutil.which("ffmpeg") is not None

def try_download_with_fallback(url, base_opts, format_type):
    """Try downloading with different format options as fallbacks"""
    
    # Define fallback format options
    if format_type == "mp4":
        format_fallbacks = [
            "best[ext=mp4]",
            "best[height<=1080]",
            "best[height<=720]",
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]",
            "bestvideo+bestaudio",
            "best"
        ]
    elif format_type == "mp3":
        format_fallbacks = [
            "bestaudio",
            "best[ext=m4a]",
            "best[ext=webm]", 
            "best"
        ]
    else:
        format_fallbacks = ["best"]
    
    last_error = None
    
    for format_option in format_fallbacks:
        try:
            opts = base_opts.copy()
            opts["format"] = format_option
            
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info, None
                
        except Exception as e:
            last_error = e
            continue
    
    return None, last_error

def download_selected_videos(url, selected_indices, base_opts, format_type):
    """Download specific videos from a playlist by their indices"""
    
    # First, get playlist info to get individual video URLs
    info_opts = {
        "quiet": True,
        "extract_flat": False,  # Get full info for each video
        "no_warnings": True,
        "ignoreerrors": True,
    }
    
    try:
        with YoutubeDL(info_opts) as ydl:
            playlist_info = ydl.extract_info(url, download=False)
            
            if not playlist_info.get("entries"):
                raise Exception("No videos found in playlist")
            
            entries = playlist_info.get("entries", [])
            downloaded_videos = []
            failed_videos = []
            
            # Download each selected video
            for index in selected_indices:
                if index >= len(entries):
                    continue
                    
                video_entry = entries[index]
                if not video_entry:
                    continue
                
                video_url = video_entry.get("webpage_url") or video_entry.get("url")
                if not video_url:
                    continue
                
                try:
                    # Try to download this specific video
                    video_info, error = try_download_with_fallback(video_url, base_opts, format_type)
                    if video_info:
                        downloaded_videos.append({
                            "title": video_info.get("title", "Unknown"),
                            "filename": os.path.basename(YoutubeDL(base_opts).prepare_filename(video_info))
                        })
                    else:
                        failed_videos.append(video_entry.get("title", f"Video {index + 1}"))
                except Exception as e:
                    failed_videos.append(video_entry.get("title", f"Video {index + 1}"))
            
            return downloaded_videos, failed_videos, playlist_info.get("title", "Unknown playlist")
            
    except Exception as e:
        raise Exception(f"Failed to process playlist: {str(e)}")
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
    selected_videos = data.get("selected_videos", [])

    # Configure download options based on format
    if format_type == "mp3":
        # Check if FFmpeg is available for MP3 conversion
        if not check_ffmpeg():
            return jsonify({
                "error": "FFmpeg is required for MP3 conversion but not found. Please install FFmpeg and ensure it's in your system PATH.",
                "help": "macOS: brew install ffmpeg | Windows: Download from ffmpeg.org | Linux: sudo apt install ffmpeg"
            }), 400
        
        # Determine audio quality based on quality setting
        audio_quality = "192"  # Default
        if quality == "best":
            audio_quality = "320"
        elif quality == "medium":
            audio_quality = "192"
        elif quality == "low":
            audio_quality = "128"
        
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(playlist_title)s/%(title)s.%(ext)s") if download_type == "playlist" else os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": audio_quality,
            }],
            "prefer_ffmpeg": True,
            "keepvideo": False,
            "extract_flat": False,
            "writethumbnail": False,
            "writeinfojson": False,
        }
    elif format_type == "mp4":
        # More robust format selection with fallbacks
        if quality == "720p":
            format_selector = "best[height<=720][ext=mp4]/best[height<=720]/best[ext=mp4]/best"
        elif quality == "1080p":
            format_selector = "best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best"
        else:
            format_selector = "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(playlist_title)s/%(title)s.%(ext)s") if download_type == "playlist" else os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": format_selector,
            "merge_output_format": "mp4",
            "extract_flat": False,
            "writethumbnail": False,
            "writeinfojson": False,
        }
    else:
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(playlist_title)s/%(title)s.%(ext)s") if download_type == "playlist" else os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": "best[ext=mp4]/bestvideo+bestaudio/best",
            "extract_flat": False,
            "writethumbnail": False,
            "writeinfojson": False,
        }

    # Add common options for better compatibility
    ydl_opts.update({
        "ignoreerrors": False,
        "no_warnings": False,
        "extractaudio": format_type == "mp3",
        "audioformat": "mp3" if format_type == "mp3" else None,
        "retries": 3,
        "fragment_retries": 3,
    })

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # Get info first
            
            if download_type == "playlist" or info.get("_type") == "playlist":
                # Check if individual videos are selected
                if download_type == "video" and selected_videos:
                    # Download selected individual videos
                    try:
                        downloaded_videos, failed_videos, playlist_title = download_selected_videos(
                            url, selected_videos, ydl_opts, format_type
                        )
                        
                        # Save to history
                        history_entry = {
                            "title": f"Selected from: {playlist_title}",
                            "url": url,
                            "format": format_type,
                            "quality": quality,
                            "type": "selected_videos",
                            "video_count": len(downloaded_videos),
                            "filename": f"Selected videos from {playlist_title}",
                            "timestamp": datetime.now().isoformat()
                        }
                        save_to_history(history_entry)
                        
                        message = f"Downloaded {len(downloaded_videos)} selected videos"
                        if failed_videos:
                            message += f" ({len(failed_videos)} failed: {', '.join(failed_videos[:3])}{'...' if len(failed_videos) > 3 else ''})"
                        
                        return jsonify({
                            "title": f"Selected from: {playlist_title}",
                            "type": "selected_videos",
                            "video_count": len(downloaded_videos),
                            "failed_count": len(failed_videos),
                            "status": "success",
                            "message": message,
                            "downloaded_videos": downloaded_videos[:5]  # Show first 5 for confirmation
                        })
                        
                    except Exception as e:
                        return jsonify({"error": f"Failed to download selected videos: {str(e)}"}), 500
                
                else:
                    # Download entire playlist
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
                
                # Try download with fallback options
                try:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                except Exception as download_error:
                    # Use fallback download method
                    fallback_info, fallback_error = try_download_with_fallback(url, ydl_opts, format_type)
                    if fallback_info:
                        info = fallback_info
                        filename = YoutubeDL(ydl_opts).prepare_filename(fallback_info)
                    else:
                        raise download_error
                
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
        error_message = str(e)
        
        # Handle specific format errors
        if "Requested format is not available" in error_message:
            return jsonify({
                "error": "The requested video quality/format is not available. Try selecting 'Best Available' quality or MP3 format instead.",
                "details": "YouTube has changed their streaming format. Some specific quality options may not be available.",
                "suggestion": "Use 'Best Available' for reliable downloads."
            }), 400
        elif "SABR streaming" in error_message:
            return jsonify({
                "error": "YouTube is using a newer streaming format that may cause issues. Trying with different format options...",
                "details": "This is a temporary YouTube limitation. MP3 downloads usually work better.",
                "suggestion": "Try downloading as MP3 or use 'Best Available' quality."
            }), 400
        else:
            return jsonify({"error": error_message}), 500

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
        "no_warnings": True,
        "ignoreerrors": True,
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

@app.route("/status", methods=["GET"])
def system_status():
    """Check system requirements and status"""
    return jsonify({
        "ffmpeg_available": check_ffmpeg(),
        "download_folder": DOWNLOAD_FOLDER,
        "status": "ready"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
