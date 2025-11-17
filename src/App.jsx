import React, { useState, useMemo } from 'react';
import { Loader2, Zap, AlertTriangle, Copy, CheckCircle2 } from 'lucide-react';

// Helper function to extract the Video ID from various YouTube URL formats
const extractVideoId = (url) => {
    // Regex that covers watch?v=, youtu.be/, embed/, and shorts/ links
    const regex = /(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/|youtube-nocookie\.com\/embed\/)([a-zA-Z0-9_-]{11})|[?&]v=([a-zA-Z0-9_-]{11})/;
    const match = url.match(regex);
    return match ? (match[1] || match[2]) : null;
};

// Helper function to categorize errors for better user feedback
const categorizeError = (errorMessage) => {
    const lowerError = errorMessage.toLowerCase();

    if (lowerError.includes('transcript') && (lowerError.includes('disabled') || lowerError.includes('not available'))) {
        return {
            type: 'no_transcript',
            title: 'No Transcript Available',
            message: 'This video does not have captions/subtitles enabled. The video owner needs to add captions for transcripts to be available.',
            suggestions: [
                'Check if the video has manually added or auto-generated captions',
                'Try another video with captions enabled',
                'Contact the video owner to request captions'
            ]
        };
    }

    if (lowerError.includes('private') || lowerError.includes('unavailable') || lowerError.includes('deleted')) {
        return {
            type: 'access_denied',
            title: 'Video Not Accessible',
            message: 'This video is private, deleted, or otherwise unavailable.',
            suggestions: [
                'Verify the video URL is correct',
                'Check if the video is set to public',
                'Ensure the video has not been deleted'
            ]
        };
    }

    if (lowerError.includes('network') || lowerError.includes('fetch') || lowerError.includes('timeout')) {
        return {
            type: 'network',
            title: 'Network Error',
            message: 'Unable to connect to the server. Please check your internet connection.',
            suggestions: [
                'Check your internet connection',
                'Try again in a few moments',
                'Disable any VPN or proxy if enabled'
            ]
        };
    }

    if (lowerError.includes('rate limit') || lowerError.includes('too many requests')) {
        return {
            type: 'rate_limit',
            title: 'Rate Limit Exceeded',
            message: 'Too many requests. Please wait a moment before trying again.',
            suggestions: [
                'Wait 30-60 seconds before trying again',
                'Avoid making multiple rapid requests'
            ]
        };
    }

    if (lowerError.includes('invalid') && lowerError.includes('url')) {
        return {
            type: 'invalid_url',
            title: 'Invalid YouTube URL',
            message: 'The URL you entered is not a valid YouTube video link.',
            suggestions: [
                'Make sure you copied the full URL',
                'Try using the share button on YouTube to get the URL',
                'Supported formats: youtube.com/watch?v=..., youtu.be/..., youtube.com/shorts/...'
            ]
        };
    }

    // Generic error fallback
    return {
        type: 'unknown',
        title: 'Error Extracting Transcript',
        message: errorMessage,
        suggestions: [
            'Verify the YouTube video URL is correct',
            'Ensure the video has captions/subtitles enabled',
            'Try again in a few moments'
        ]
    };
};

const App = () => {
    const [url, setUrl] = useState('');
    const [transcript, setTranscript] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [copyStatus, setCopyStatus] = useState('');

    // Formats seconds into MM:SS.ss format for display
    const formatTime = (seconds) => {
        const totalMs = Math.floor(seconds * 100);
        const sec = Math.floor(totalMs / 100);
        const ms = totalMs % 100;

        const minutes = Math.floor(sec / 60);
        const remainingSeconds = sec % 60;

        const pad = (num) => num.toString().padStart(2, '0');

        return `${pad(minutes)}:${pad(remainingSeconds)}.${pad(ms)}`;
    };

    // Generates the single, entire string for the output textarea
    const fullTranscriptText = useMemo(() => {
        if (!transcript || transcript.length === 0) return '';

        let fullText = '';
        const speakerName = "Speaker 1";

        transcript.forEach(segment => {
            const startFormatted = formatTime(segment.start);

            // Output format: Timestamp \n Speaker \n Text \n \n
            fullText += `${startFormatted}\n`;
            fullText += `${speakerName}\n`;
            fullText += `${segment.text}\n`;
            fullText += `\n`;
        });

        return fullText.trim();
    }, [transcript]);

    const copyToClipboard = () => {
        if (fullTranscriptText) {
            const textarea = document.createElement('textarea');
            textarea.value = fullTranscriptText;
            document.body.appendChild(textarea);
            textarea.select();

            try {
                document.execCommand('copy');
                setCopyStatus('success');
            } catch (err) {
                console.error('Failed to copy text:', err);
                setCopyStatus('failed');
            } finally {
                document.body.removeChild(textarea);
                setTimeout(() => setCopyStatus(''), 3000);
            }
        }
    };

    const fetchTranscript = async () => {
        setError(null);
        setTranscript(null);
        setCopyStatus('');

        // Validate URL before making request
        const trimmedUrl = url.trim();
        if (!trimmedUrl) {
            setError(categorizeError('Invalid URL'));
            return;
        }

        const videoId = extractVideoId(trimmedUrl);

        if (!videoId) {
            setError(categorizeError('Invalid YouTube URL. Please check the link and try again.'));
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(`/api/get-transcript?videoId=${videoId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `Server error (${response.status})`;

                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || errorJson.details || errorMessage;
                } catch {
                    errorMessage = errorText || errorMessage;
                }

                throw new Error(errorMessage);
            }

            const data = await response.json();

            if (data.error) {
                // Log full error details for debugging
                console.error('API Error Details:', {
                    error: data.error,
                    details: data.details,
                    error_type: data.error_type,
                    video_id: data.video_id
                });

                // Include detailed error info in the error message
                let fullError = data.error;
                if (data.details && data.details !== data.error) {
                    fullError += ` (Details: ${data.details})`;
                }
                throw new Error(fullError);
            }

            if (!data || data.length === 0) {
                throw new Error('No transcript data returned. The video may not have captions available.');
            }

            setTranscript(data);

        } catch (err) {
            console.error('Transcript extraction error:', err);
            console.error('Full error object:', err);
            setError(categorizeError(err.message));
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !loading && url.trim() !== '') {
            fetchTranscript();
        }
    };

    const renderOutput = () => {
        if (loading) {
            return (
                <div className="text-center py-12 animate-fade-in">
                    <div className="relative">
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-16 h-16 bg-gradient-to-r from-red-400 to-rose-400 rounded-full animate-ping opacity-20"></div>
                        </div>
                        <Loader2 className="mx-auto h-12 w-12 text-red-500 animate-spin mb-4 relative z-10" />
                    </div>
                    <p className="text-gray-700 font-medium text-lg">Extracting transcript...</p>
                    <p className="text-gray-500 text-sm mt-2">This may take a few moments</p>
                </div>
            );
        }

        if (transcript && transcript.length > 0) {
            return (
                <div className="animate-fade-in">
                    <div className="flex justify-between items-center mb-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200">
                        <p className="text-sm text-gray-700 font-semibold flex items-center">
                            <CheckCircle2 className="w-5 h-5 text-green-600 mr-2" />
                            <span className="font-bold text-green-700 text-lg">{transcript.length}</span>
                            <span className="ml-1">segments extracted successfully!</span>
                        </p>
                        <div className="flex items-center space-x-3">
                            {copyStatus && (
                                <span className={`text-sm font-bold transition-all duration-500 flex items-center ${
                                    copyStatus === 'success' ? 'text-green-600 animate-bounce-short' : 'text-red-500'
                                }`}>
                                    {copyStatus === 'success' ? (
                                        <>
                                            <CheckCircle2 className="w-4 h-4 mr-1" />
                                            Copied!
                                        </>
                                    ) : (
                                        'Failed to copy'
                                    )}
                                </span>
                            )}
                            <button
                                onClick={copyToClipboard}
                                className="px-4 py-2 text-sm bg-gradient-to-r from-gray-700 to-gray-800 text-white rounded-xl hover:from-gray-800 hover:to-gray-900 transition-all duration-300 shadow-lg hover:shadow-xl flex items-center transform hover:scale-105 active:scale-95"
                            >
                                <Copy className="w-4 h-4 mr-2" /> Copy Text
                            </button>
                        </div>
                    </div>
                    <textarea
                        readOnly
                        value={fullTranscriptText}
                        rows={15}
                        className="w-full font-mono text-sm p-5 border-2 border-gray-200 rounded-xl bg-white/90 backdrop-blur-sm resize-none shadow-lg focus:outline-none focus:ring-2 focus:ring-red-300 transition-all duration-300"
                    />
                </div>
            );
        }

        return (
            <div className="text-center text-gray-500 py-16 animate-fade-in">
                <div className="relative mb-4">
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-20 h-20 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full animate-pulse opacity-30"></div>
                    </div>
                    <Zap className="mx-auto h-12 w-12 text-gray-400 relative z-10" />
                </div>
                <p className="text-lg font-medium text-gray-600">Ready to extract transcripts</p>
                <p className="text-sm text-gray-500 mt-2">Enter a YouTube URL above to get started</p>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-red-50 p-4 sm:p-8">
            <div className="max-w-3xl mx-auto">
                <header className="text-center mb-10 p-8 bg-gradient-to-br from-red-500 to-rose-600 rounded-2xl shadow-2xl transform transition-all duration-300 hover:scale-[1.02] hover:shadow-3xl">
                    <h1 className="text-4xl font-extrabold text-white flex items-center justify-center drop-shadow-lg">
                        <Zap className="w-8 h-8 mr-3 animate-pulse" />
                        YouTube Transcript Extractor
                    </h1>
                    <p className="mt-3 text-red-50 font-medium">Extract structured transcripts from YouTube videos with timestamps.</p>
                </header>

                <div className="flex flex-col sm:flex-row gap-3 mb-8 transform transition-all duration-300">
                    <input
                        type="url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Paste your YouTube URL here (e.g., https://youtube.com/watch?v=...)"
                        className="flex-grow p-4 border-2 border-gray-200 rounded-xl shadow-lg bg-white/80 backdrop-blur-sm focus:ring-2 focus:ring-red-400 focus:border-red-400 transition-all duration-300 focus:shadow-xl focus:scale-[1.01]"
                        disabled={loading}
                    />
                    <button
                        onClick={fetchTranscript}
                        disabled={loading || url.trim() === ''}
                        className={`px-8 py-4 font-bold rounded-xl shadow-lg transition-all duration-300 transform
                            ${loading || url.trim() === ''
                                ? 'bg-gradient-to-r from-red-300 to-rose-300 cursor-not-allowed text-white scale-100'
                                : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 text-white hover:shadow-2xl hover:scale-105 active:scale-95'}`
                        }
                    >
                        {loading ? (
                            <span className="flex items-center justify-center">
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                Extracting...
                            </span>
                        ) : (
                            'Get Transcript'
                        )}
                    </button>
                </div>

                {error && (
                    <div className="p-6 mb-6 bg-gradient-to-br from-red-50 to-rose-50 border-2 border-red-300 rounded-2xl shadow-xl animate-slide-in backdrop-blur-sm">
                        <div className="flex items-start mb-3">
                            <AlertTriangle className="h-6 w-6 text-red-600 mr-3 mt-0.5 flex-shrink-0 animate-bounce" />
                            <div className="flex-1">
                                <h3 className="font-bold text-red-900 mb-2 text-lg">{error.title}</h3>
                                <p className="text-red-700 text-sm leading-relaxed">{error.message}</p>
                            </div>
                        </div>
                        {error.suggestions && error.suggestions.length > 0 && (
                            <div className="ml-9 mt-3 p-3 bg-white/50 rounded-lg">
                                <p className="text-xs font-bold text-red-900 mb-2">Suggestions:</p>
                                <ul className="list-disc list-inside text-xs text-red-800 space-y-1">
                                    {error.suggestions.map((suggestion, index) => (
                                        <li key={index} className="leading-relaxed">{suggestion}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                <main className="space-y-4">
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">Results</h2>
                    <div className="bg-gradient-to-br from-gray-50 to-white p-6 rounded-2xl shadow-2xl border border-gray-200 min-h-[200px] backdrop-blur-sm">
                        {renderOutput()}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default App;
