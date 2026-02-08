---
name: youtube-transcript
description: Download YouTube video transcripts/subtitles. Supports multiple languages and outputs in various formats (text, SRT, JSON). Use /youtube-transcript <url> to fetch captions.
---

# YouTube Transcript Download

## Overview

Download transcripts (subtitles/captions) from YouTube videos. Supports auto-generated and manual captions in multiple languages.

## Usage

```
/youtube-transcript <youtube_url> [options]
```

### Options
- `--lang <code>`: Language code (default: ko, en)
- `--format <type>`: Output format - text, srt, json (default: text)
- `--output <path>`: Save to file instead of displaying

## Workflow

1. **Extract Video ID**
   - Parse the YouTube URL to extract the video ID
   - Supports formats: `youtube.com/watch?v=ID`, `youtu.be/ID`, `youtube.com/shorts/ID`

2. **Fetch Transcript**
   - Use `yt-dlp` to download subtitles:
   ```bash
   yt-dlp --write-auto-sub --sub-lang ko,en --skip-download --sub-format srt -o "%(title)s.%(ext)s" "<url>"
   ```

   - Or use Python `youtube-transcript-api`:
   ```python
   from youtube_transcript_api import YouTubeTranscriptApi
   transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
   ```

3. **Format Output**
   - **text**: Plain text with timestamps removed
   - **srt**: Standard subtitle format with timing
   - **json**: Raw transcript data with start time and duration

4. **Save or Display**
   - Display in terminal if no output path specified
   - Save to file if `--output` is provided

## Examples

```bash
# Basic usage - get Korean/English transcript
/youtube-transcript https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Get Japanese transcript
/youtube-transcript https://youtu.be/dQw4w9WgXcQ --lang ja

# Save as SRT file
/youtube-transcript https://youtube.com/watch?v=xyz --format srt --output transcript.srt

# Get raw JSON data
/youtube-transcript https://youtube.com/watch?v=xyz --format json
```

## Dependencies

Install one of these tools:

```bash
# Option 1: yt-dlp (recommended)
pip install yt-dlp

# Option 2: youtube-transcript-api (Python only, faster)
pip install youtube-transcript-api
```

## Implementation

When executing this skill, Claude should:

1. Parse the YouTube URL and extract video ID
2. Check if required tools are installed
3. Attempt to fetch transcript using available tool
4. Format and display/save the result
5. Handle errors gracefully (no captions available, video not found, etc.)

### Python Script Template

```python
import sys
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter, SRTFormatter, JSONFormatter

def extract_video_id(url):
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([^&?/]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id, languages=['ko', 'en'], format='text'):
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)

    if format == 'text':
        return TextFormatter().format_transcript(transcript)
    elif format == 'srt':
        return SRTFormatter().format_transcript(transcript)
    elif format == 'json':
        return JSONFormatter().format_transcript(transcript)

    return '\n'.join([item['text'] for item in transcript])

if __name__ == '__main__':
    url = sys.argv[1]
    video_id = extract_video_id(url)
    print(get_transcript(video_id))
```

## Error Handling

- **No transcript available**: Some videos don't have captions
- **Language not available**: Fall back to available languages
- **Video not found**: Invalid URL or private video
- **Rate limiting**: Add delays between requests if processing multiple videos
