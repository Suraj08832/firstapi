# Advanced YouTube Downloader API

A reliable and feature-rich API for downloading YouTube videos and extracting video information.

## Features

- 🎵 Download audio and video in best quality
- 📊 Get detailed video information
- 🔒 API key authentication
- ⚡ Rate limiting for API protection
- 📝 Comprehensive logging
- 🌐 CORS support
- 🔄 Error handling and validation

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and set your API key and other configurations

## Usage

Start the server:
```bash
python you.py
```

### API Endpoints

1. **Download Video/Audio**
   ```http
   POST /api/download
   Header: X-API-Key: your-api-key
   
   {
     "url": "https://youtube.com/watch?v=...",
     "type": "audio" or "video"
   }
   ```

2. **Get Video Information**
   ```http
   GET /api/info?url=https://youtube.com/watch?v=...
   Header: X-API-Key: your-api-key
   ```

### Rate Limits
- Download: 10 requests per minute
- Info: 20 requests per minute
- Global: 100 requests per day

## Production Deployment

For production:
1. Set `FLASK_ENV=production` in `.env`
2. Use a proper secret API key
3. Consider using Redis for rate limiting
4. Run with gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 you:app
   ```

## Error Handling

The API returns appropriate HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 429: Too Many Requests
- 500: Server Error

Each error response includes a descriptive message. 