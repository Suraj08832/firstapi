from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL
import logging
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Key for access control (from environment variable)
API_KEY = os.getenv("API_KEY", "mera-secret-key")  # Default key for development

# Common options with more formats and better quality
YDL_COMMON_OPTS = {
    'quiet': True,
    'nocheckcertificate': True,
    'noplaylist': True,
    'extract_flat': False,
    'skip_download': True,
    'format': 'bestvideo+bestaudio/best',  # Prefer best quality
    'geo_bypass': True,
    'ignoreerrors': True,
    'no_warnings': True
}

def extract_info(youtube_url, media_type="audio"):
    ydl_opts = YDL_COMMON_OPTS.copy()
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            if not info:
                raise ValueError("Could not extract video information")

            formats = []
            selected_url = None

            if media_type == "audio":
                # Get best audio format
                for f in info.get("formats", []):
                    if f.get("acodec") != "none" and f.get("vcodec") == "none":
                        formats.append({
                            "format_id": f.get("format_id"),
                            "ext": f.get("ext"),
                            "filesize": f.get("filesize"),
                            "asr": f.get("asr"),
                            "url": f.get("url")
                        })
                if formats:
                    # Select best quality audio
                    best_format = max(formats, key=lambda x: x.get("asr", 0))
                    selected_url = best_format["url"]

            elif media_type == "video":
                # Get best video formats
                for f in info.get("formats", []):
                    if f.get("vcodec") != "none" and f.get("acodec") != "none":
                        formats.append({
                            "format_id": f.get("format_id"),
                            "ext": f.get("ext"),
                            "width": f.get("width"),
                            "height": f.get("height"),
                            "filesize": f.get("filesize"),
                            "fps": f.get("fps"),
                            "url": f.get("url")
                        })
                if formats:
                    # Select best quality video
                    best_format = max(formats, key=lambda x: (x.get("height", 0), x.get("fps", 0)))
                    selected_url = best_format["url"]
            else:
                raise ValueError("Invalid media type")

            if not selected_url:
                raise ValueError(f"No suitable {media_type} format found")

            return {
                "title": info.get("title"),
                "id": info.get("id"),
                "duration": info.get("duration"),
                "duration_string": info.get("duration_string"),
                "uploader": info.get("uploader"),
                "channel_url": info.get("channel_url"),
                "thumbnail": info.get("thumbnail"),
                "description": info.get("description"),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "webpage_url": info.get("webpage_url"),
                "upload_date": info.get("upload_date"),
                "media_type": media_type,
                "stream_url": selected_url,
                "available_formats": formats
            }

    except Exception as e:
        logger.error(f"Error extracting info for URL {youtube_url}: {str(e)}")
        raise

@app.route("/api/download", methods=["POST"])
@limiter.limit("10 per minute")  # Add specific rate limit for download endpoint
def download():
    # 🔐 API Key check
    provided_key = request.headers.get("X-API-Key")
    if provided_key != API_KEY:
        logger.warning(f"Unauthorized access attempt from IP: {get_remote_address()}")
        return jsonify({"error": "Unauthorized. Invalid API Key."}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        url = data.get("url")
        media_type = data.get("type", "audio").lower()  # default = audio

        if not url:
            return jsonify({"error": "Missing 'url' in request"}), 400

        if media_type not in ["audio", "video"]:
            return jsonify({"error": "Invalid 'type'. Use 'audio' or 'video'."}), 400

        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return jsonify({"error": "Invalid URL format"}), 400

        logger.info(f"Processing {media_type} download request for URL: {url}")
        result = extract_info(url, media_type)
        return jsonify(result), 200

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Error during processing")
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

@app.route("/api/info", methods=["GET"])
@limiter.limit("20 per minute")
def get_info():
    """Endpoint to get video information without downloading"""
    provided_key = request.headers.get("X-API-Key")
    if provided_key != API_KEY:
        return jsonify({"error": "Unauthorized. Invalid API Key."}), 401

    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        result = extract_info(url, "video")
        # Remove stream URL for info-only requests
        result.pop("stream_url", None)
        return jsonify(result), 200
    except Exception as e:
        logger.exception("Error fetching video info")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "YouTube Downloader API",
        "version": "2.0",
        "endpoints": {
            "/api/download": {
                "method": "POST",
                "headers": {"X-API-Key": "your-api-key"},
                "body": {
                    "url": "https://youtube.com/watch?v=...",
                    "type": "audio or video"
                }
            },
            "/api/info": {
                "method": "GET",
                "headers": {"X-API-Key": "your-api-key"},
                "query_params": {
                    "url": "https://youtube.com/watch?v=..."
                }
            }
        },
        "rate_limits": {
            "download": "10 per minute",
            "info": "20 per minute",
            "global": "100 per day"
        }
    })

if __name__ == "__main__":
    # Check if running in development mode
    debug_mode = os.getenv("FLASK_ENV") == "development"
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
