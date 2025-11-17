#!/usr/bin/env python3
"""
Test script to verify the youtube-transcript-api works locally
Run this to check if the API is working outside of Vercel
"""

from youtube_transcript_api import YouTubeTranscriptApi

# Test video ID (the one you're having trouble with)
video_id = 'pS3WktUIiYw'

print(f"Testing YouTube Transcript API for video: {video_id}")
print("=" * 60)

try:
    # Create API instance
    ytt_api = YouTubeTranscriptApi()

    print("\n1. Attempting to fetch transcript...")
    transcript = ytt_api.fetch(video_id, languages=['en'])

    print(f"✓ Success! Found {len(transcript)} segments")
    print("\nFirst 3 segments:")
    for i, segment in enumerate(list(transcript)[:3]):
        print(f"  [{segment['start']:.2f}s] {segment['text']}")

except Exception as e:
    print(f"✗ Error: {type(e).__name__}")
    print(f"  Message: {str(e)}")

    # Try listing available transcripts
    print("\n2. Attempting to list available transcripts...")
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        print("Available transcripts:")
        for transcript in transcript_list:
            print(f"  - {transcript.language_code} ({transcript.language})")
            print(f"    Generated: {transcript.is_generated}")
            print(f"    Translatable: {transcript.is_translatable}")
    except Exception as e2:
        print(f"✗ Listing also failed: {str(e2)}")

print("\n" + "=" * 60)
print("Test complete")
