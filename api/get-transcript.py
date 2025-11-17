# Python Serverless Function for Vercel
# Extracts YouTube transcripts using youtube_transcript_api

import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import the necessary library (must be listed in requirements.txt)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError as e:
    print(f"Import error: {e}")
    YouTubeTranscriptApi = None

# Simple in-memory cache to reduce API calls
# Format: {video_id: {'data': transcript, 'timestamp': time}}
CACHE = {}
CACHE_DURATION = 300  # 5 minutes in seconds

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

        # Check cache first to reduce API calls and avoid rate limiting
        current_time = time.time()
        if video_id in CACHE:
            cached_entry = CACHE[video_id]
            # Check if cache is still valid
            if current_time - cached_entry['timestamp'] < CACHE_DURATION:
                # Return cached data
                response_data = cached_entry['data']
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                return

        try:
            # Extract the transcript from YouTube using the NEW API
            # Initialize the API client
            ytt_api = YouTubeTranscriptApi()

            # Strategy: Try multiple language options to maximize success
            # 1. Try English first (most common)
            # 2. If that fails, list all available transcripts and get the first one

            transcript_data = None

            try:
                # Try to fetch English transcript (manual or auto-generated)
                # The fetch() method will automatically handle both types
                transcript_data = ytt_api.fetch(video_id, languages=['en'])
            except Exception as en_error:
                # If English fails, try to get any available transcript
                try:
                    # List all available transcripts
                    transcript_list = ytt_api.list(video_id)

                    # Try to find any transcript (manual or generated)
                    found_transcript = None

                    # First, try to find ANY English variant
                    try:
                        found_transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'en-CA', 'en-AU'])
                    except:
                        # Try to get manually created transcript in any language
                        try:
                            found_transcript = transcript_list.find_manually_created_transcript()
                        except:
                            # Try to get auto-generated transcript in any language
                            try:
                                found_transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
                            except:
                                # Get the first available transcript
                                for trans in transcript_list:
                                    found_transcript = trans
                                    break

                    if found_transcript:
                        # Fetch the actual transcript data
                        transcript_data = found_transcript.fetch()
                    else:
                        raise Exception("No transcript found for this video")

                except Exception as list_error:
                    # Re-raise the original error if everything fails
                    raise en_error

            if not transcript_data:
                raise Exception("No transcript data available for this video")

            # Convert the FetchedTranscript object to a list of dictionaries
            # The transcript_data should already be iterable based on the API docs
            response_data = list(transcript_data)

            # Cache the successful response
            CACHE[video_id] = {
                'data': response_data,
                'timestamp': current_time
            }

        except Exception as e:
            # Handle various error cases
            error_message = str(e)
            error_type = type(e).__name__
            original_error = str(e)

            # Provide user-friendly error messages
            error_lower = error_message.lower()

            if 'transcript' in error_lower and 'disabled' in error_lower:
                error_message = 'Transcript is disabled for this video. The video owner needs to enable captions.'
            elif 'no transcript' in error_lower or 'could not retrieve' in error_lower:
                error_message = 'No transcript available for this video. Please ensure the video has captions/subtitles enabled.'
            elif 'unavailable' in error_lower or 'not found' in error_lower or 'invalid' in error_lower:
                error_message = 'Video not found or unavailable. Please check the URL and try again.'
            elif 'too many' in error_lower or 'rate limit' in error_lower or '429' in error_lower:
                error_message = 'YouTube rate limit reached. Please wait 60-90 seconds before trying again. (Caching enabled to prevent this in the future)'

            response_data = {
                'error': error_message,
                'details': original_error,
                'error_type': error_type,
                'video_id': video_id
            }

        self.wfile.write(json.dumps(response_data).encode('utf-8'))
