"""
transcript.py — Extract transcripts from YouTube URLs.
Uses youtube-transcript-api (no API key needed).
"""

import re
from urllib.parse import parse_qs, urlparse


def extract_video_id(url: str) -> str | None:
    """
    Extract YouTube video ID from any valid YouTube URL format:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://youtube.com/shorts/VIDEO_ID
    """
    url = url.strip()
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(url: str) -> dict:
    """
    Fetch transcript for a YouTube video.
    Returns dict with: video_id, transcript (full text), segments (list), duration_minutes
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL. Please provide a valid YouTube video link."}

    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        except NoTranscriptFound:
            # Try auto-generated
            try:
                transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript_obj = transcripts.find_generated_transcript(["en"])
                transcript_list = transcript_obj.fetch()
            except Exception:
                return {"error": "No English transcript available for this video. Try a video with English captions."}
        except TranscriptsDisabled:
            return {"error": "Transcripts are disabled for this video."}

        # Build full text
        full_text = " ".join(seg["text"].strip() for seg in transcript_list)
        full_text = re.sub(r"\s+", " ", full_text).strip()

        # Total duration
        if transcript_list:
            last = transcript_list[-1]
            total_seconds = last["start"] + last.get("duration", 0)
            duration_minutes = round(total_seconds / 60, 1)
        else:
            duration_minutes = 0

        return {
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "transcript": full_text,
            "segments": transcript_list,
            "duration_minutes": duration_minutes,
            "word_count": len(full_text.split()),
        }

    except ImportError:
        return {"error": "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"}
    except Exception as e:
        return {"error": f"Failed to fetch transcript: {str(e)}"}


def get_video_metadata(video_id: str) -> dict:
    """
    Try to get basic video metadata using yt-dlp (optional).
    Falls back gracefully if not available.
    """
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return {
                "title": info.get("title", "Unknown"),
                "channel": info.get("uploader", "Unknown"),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "thumbnail": info.get("thumbnail", ""),
                "description": (info.get("description") or "")[:500],
            }
    except Exception:
        return {
            "title": "Video",
            "channel": "Unknown",
            "view_count": 0,
            "like_count": 0,
            "thumbnail": "",
            "description": "",
        }


def chunk_transcript(transcript: str, max_chars: int = 12000) -> str:
    """
    Trim transcript to max_chars for API calls.
    Keeps the beginning and end (most content-rich parts).
    """
    if len(transcript) <= max_chars:
        return transcript
    half = max_chars // 2
    return transcript[:half] + "\n\n[...middle trimmed for length...]\n\n" + transcript[-half:]
