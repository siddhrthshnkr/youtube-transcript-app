# YouTube Transcript Extractor

A modern React-based web application that extracts structured transcripts from YouTube videos with timestamps. Built with Vite, React, and Tailwind CSS, powered by a Python serverless backend.

## Features

- Extract transcripts from any YouTube video with captions enabled
- Clean, formatted output with timestamps and speaker labels
- One-click copy to clipboard functionality
- Comprehensive error handling with helpful suggestions
- Responsive design that works on all devices
- Fast and lightweight

## Tech Stack

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library

### Backend
- **Python 3.9** - Serverless functions
- **youtube-transcript-api** - YouTube transcript extraction
- **Vercel** - Hosting and serverless deployment

## Project Structure

```
youtube-transcript-app/
├── api/
│   └── get-transcript.py      # Python serverless function
├── src/
│   ├── App.jsx                # Main React component
│   ├── main.jsx               # React entry point
│   └── index.css              # Tailwind CSS imports
├── index.html                 # HTML entry point
├── package.json               # Node.js dependencies
├── requirements.txt           # Python dependencies
├── vercel.json                # Vercel configuration
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── postcss.config.js          # PostCSS configuration
└── README.md                  # This file
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Git
- Vercel account (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   cd youtube-transcript-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**

   The app will automatically open at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Deployment to Vercel

### Option 1: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

### Option 2: Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your Git repository
4. Vercel will automatically detect the configuration
5. Click "Deploy"

### Environment Configuration

No environment variables are required for basic functionality. The app works out of the box.

## Usage

1. **Enter a YouTube URL**

   Paste any YouTube video URL in the input field. Supported formats:
   - `https://www.youtube.com/watch?v=VIDEO_ID`
   - `https://youtu.be/VIDEO_ID`
   - `https://www.youtube.com/shorts/VIDEO_ID`

2. **Extract Transcript**

   Click "Get Transcript" or press Enter

3. **Copy the Results**

   Use the "Copy Text" button to copy the formatted transcript

### Output Format

The transcript is formatted as:
```
00:02.50
Speaker 1
Never gonna give you up

00:04.30
Speaker 1
Never gonna let you down
```

## Error Handling

The app provides detailed error messages for common issues:

- **No Transcript Available** - Video doesn't have captions enabled
- **Video Not Accessible** - Private, deleted, or unavailable video
- **Network Error** - Connection issues
- **Rate Limit Exceeded** - Too many requests
- **Invalid YouTube URL** - Malformed URL

Each error includes helpful suggestions for resolution.

## API Endpoint

### GET `/api/get-transcript`

Extracts the transcript for a YouTube video.

**Query Parameters:**
- `videoId` (required) - YouTube video ID

**Response:**
```json
[
  {
    "text": "Video transcript text",
    "start": 2.5,
    "duration": 1.8
  },
  ...
]
```

**Error Response:**
```json
{
  "error": "Error message",
  "details": "Detailed error information"
}
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

### Code Structure

- **src/App.jsx** - Main application component with state management and UI logic
- **api/get-transcript.py** - Serverless function that handles YouTube transcript extraction
- **src/index.css** - Tailwind CSS imports
- **src/main.jsx** - React app initialization

## Troubleshooting

### Development Server Won't Start

1. Delete `node_modules/` and `package-lock.json`
2. Run `npm install` again
3. Try `npm run dev`

### API Not Working Locally

The Python serverless functions only work when deployed to Vercel. For local testing:
1. Deploy to Vercel
2. Test the production URL

### Build Errors

1. Ensure all dependencies are installed: `npm install`
2. Check Node.js version (should be 16+)
3. Clear build cache: `rm -rf dist/`

## License

MIT License - feel free to use this project for any purpose.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions:
1. Check the error message and suggestions provided by the app
2. Review this README
3. Open an issue on GitHub
