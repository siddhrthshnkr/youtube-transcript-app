# Python Serverless Function for Vercel
# Extracts YouTube transcripts using youtube_transcript_api

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import the necessary library (must be listed in requirements.txt)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("YouTubeTranscriptApi not found. Ensure it is in requirements.txt")
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to extract YouTube transcripts"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS
        self.end_headers()

        # Get video ID from query string
        query = urlparse(self.path).query
        params = parse_qs(query)
        video_id = params.get('videoId', [''])[0]

        # Validate inputs
        if not video_id:
            response_data = {
                'error': 'Missing videoId parameter',
                'details': 'Please provide a valid YouTube video ID'
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        if not YouTubeTranscriptApi:
            response_data = {
                'error': 'Python library not installed',
                'details': 'youtube_transcript_api is not available on the server'
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        try:
            # Extract the transcript from YouTube
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

            # Return the list of transcript segments as JSON
            response_data = transcript_list

        except Exception as e:
            # Handle various error cases
            error_message = str(e)

            # Provide more specific error messages
            if 'Transcript' in error_message and 'disabled' in error_message:
                error_message = 'Transcript is disabled for this video. The video owner needs to enable captions.'
            elif 'Could not retrieve' in error_message:
                error_message = 'Could not retrieve transcript. The video may be private, deleted, or have no available captions.'
            elif 'Video unavailable' in error_message:
                error_message = 'Video is unavailable. It may be private, deleted, or region-restricted.'

            response_data = {
                'error': error_message,
                'details': str(e)
            }

        self.wfile.write(json.dumps(response_data).encode('utf-8'))
