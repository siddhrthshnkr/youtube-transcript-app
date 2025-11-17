# Python Serverless Function for Vercel
# Extracts YouTube transcripts using youtube_transcript_api

import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import the necessary library (must be listed in requirements.txt)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    import youtube_transcript_api
    print(f"youtube_transcript_api version: {youtube_transcript_api.__version__ if hasattr(youtube_transcript_api, '__version__') else 'unknown'}")
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
            # Note: You can add cookies here if needed for authentication
            ytt_api = YouTubeTranscriptApi()

            # Add some delay to avoid triggering rate limits
            import time
            time.sleep(0.5)  # 500ms delay

            # Strategy: Try multiple language options to maximize success
            # 1. Try English first (most common)
            # 2. If that fails, list all available transcripts and get the first one

            transcript_data = None

            try:
                # Try to fetch English transcript (manual or auto-generated)
                # The fetch() method will automatically handle both types
                print(f"Attempting to fetch transcript for {video_id} with language ['en']")
                transcript_data = ytt_api.fetch(video_id, languages=['en'])
                print(f"Successfully fetched transcript with {len(list(transcript_data))} segments")
            except Exception as en_error:
                print(f"Failed to fetch with ['en'], error: {type(en_error).__name__}: {str(en_error)}")
                # If English fails, try to get any available transcript
                try:
                    # List all available transcripts
                    print(f"Listing all available transcripts for {video_id}")
                    transcript_list = ytt_api.list(video_id)

                    # Log available transcripts
                    available = []
                    for t in transcript_list:
                        available.append(f"{t.language_code} (generated={t.is_generated})")
                    print(f"Available transcripts: {', '.join(available)}")

                    # Try to find any transcript (manual or generated)
                    found_transcript = None

                    # First, try to find ANY English variant
                    try:
                        print("Trying to find English transcript variants...")
                        found_transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'en-CA', 'en-AU'])
                        print(f"Found English transcript: {found_transcript.language_code}")
                    except Exception as e:
                        print(f"No English variants found: {e}")
                        # Try to get manually created transcript in any language
                        try:
                            print("Trying to find manually created transcript...")
                            found_transcript = transcript_list.find_manually_created_transcript()
                            print(f"Found manual transcript: {found_transcript.language_code}")
                        except Exception as e2:
                            print(f"No manual transcript found: {e2}")
                            # Try to get auto-generated transcript in any language
                            try:
                                print("Trying to find auto-generated transcript...")
                                found_transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
                                print(f"Found generated transcript: {found_transcript.language_code}")
                            except Exception as e3:
                                print(f"No generated transcript found: {e3}")
                                # Get the first available transcript
                                print("Trying to get first available transcript...")
                                for trans in transcript_list:
                                    found_transcript = trans
                                    print(f"Using first available: {trans.language_code}")
                                    break

                    if found_transcript:
                        # Fetch the actual transcript data
                        print(f"Fetching transcript data for {found_transcript.language_code}...")
                        transcript_data = found_transcript.fetch()
                        print(f"Successfully fetched {len(list(transcript_data))} segments")
                    else:
                        print("ERROR: No transcript could be found for this video")
                        raise Exception("No transcript found for this video")

                except Exception as list_error:
                    print(f"Fallback method failed: {type(list_error).__name__}: {str(list_error)}")
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

            # Log the full error for debugging in Vercel logs
            print(f"ERROR fetching transcript for {video_id}:")
            print(f"  Type: {error_type}")
            print(f"  Message: {error_message}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")

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
