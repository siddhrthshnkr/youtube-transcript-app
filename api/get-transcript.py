# Python Serverless Function for Vercel
# Extracts YouTube transcripts using youtube_transcript_api

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import the necessary library (must be listed in requirements.txt)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
        TooManyRequests,
        YouTubeRequestFailed
    )
except ImportError as e:
    print(f"Import error: {e}")
    YouTubeTranscriptApi = None
    TranscriptsDisabled = None
    NoTranscriptFound = None
    VideoUnavailable = None
    TooManyRequests = None
    YouTubeRequestFailed = None

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
            # First, list all available transcripts to find what's available
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to find a transcript in this order:
            # 1. Try to get English transcript (manual or auto-generated)
            # 2. Try to get any manually created transcript
            # 3. Try to get any auto-generated transcript
            # 4. Get the first available transcript

            transcript = None

            try:
                # Try English first (most common)
                transcript = transcript_list_obj.find_transcript(['en'])
            except:
                try:
                    # Try to get any manually created transcript
                    transcript = transcript_list_obj.find_manually_created_transcript()
                except:
                    try:
                        # Try to get any auto-generated transcript
                        transcript = transcript_list_obj.find_generated_transcript(['en', 'en-US', 'en-GB'])
                    except:
                        # Get the first available transcript in any language
                        for t in transcript_list_obj:
                            transcript = t
                            break

            if transcript is None:
                raise NoTranscriptFound(video_id, [], None)

            # Fetch the actual transcript data
            transcript_list = transcript.fetch()

            # Return the list of transcript segments as JSON
            response_data = transcript_list

        except Exception as e:
            # Handle various error cases with specific exceptions
            error_message = str(e)
            error_type = type(e).__name__

            # Check for specific exception types if imports succeeded
            if TranscriptsDisabled and isinstance(e, TranscriptsDisabled):
                error_message = 'Transcript is disabled for this video. The video owner needs to enable captions.'
            elif NoTranscriptFound and isinstance(e, NoTranscriptFound):
                error_message = 'No transcript found for this video. Captions may not be available in any language.'
            elif VideoUnavailable and isinstance(e, VideoUnavailable):
                error_message = 'Video is unavailable. It may be private, deleted, or region-restricted.'
            elif TooManyRequests and isinstance(e, TooManyRequests):
                error_message = 'Too many requests. Please try again in a few moments.'
            elif YouTubeRequestFailed and isinstance(e, YouTubeRequestFailed):
                error_message = 'Failed to connect to YouTube. Please try again later.'
            else:
                # Fallback to string matching for better error messages
                error_lower = error_message.lower()
                if 'transcript' in error_lower and 'disabled' in error_lower:
                    error_message = 'Transcript is disabled for this video. The video owner needs to enable captions.'
                elif 'could not retrieve' in error_lower or 'no transcripts' in error_lower:
                    error_message = 'No transcript available for this video. Please ensure the video has captions/subtitles enabled.'
                elif 'unavailable' in error_lower or 'not found' in error_lower:
                    error_message = 'Video not found or unavailable. Please check the URL and try again.'

            response_data = {
                'error': error_message,
                'details': str(e),
                'error_type': error_type
            }

        self.wfile.write(json.dumps(response_data).encode('utf-8'))
