"""
transcript.py — Extract transcripts from YouTube URLs.
Compatible with youtube-transcript-api v2.x (new instance-based API).

Breaking change in v2.x:
  OLD: YouTubeTranscriptApi.get_transcript(video_id)       ← removed
  NEW: YouTubeTranscriptApi().fetch(video_id).to_raw_data() ← current
"""

import re


def extract_video_id(url: str) -> str | None:
    """
    Extract YouTube video ID from any URL format:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    url = url.strip()
    match = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


def get_transcript(url: str) -> dict:
    """
    Fetch transcript for a YouTube video.
    Returns dict with: video_id, url, transcript, segments, duration_minutes, word_count
    On error returns: {"error": "message"}
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL. Please provide a valid YouTube link."}

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            NoTranscriptFound,
            TranscriptsDisabled,
            VideoUnavailable,
        )
    except ImportError:
        return {"error": "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"}

    ytt = YouTubeTranscriptApi()

    # ── Try fetching English transcript ──────────────────────────────────────
    raw_data = None

    # Strategy 1: direct fetch with English preference
    try:
        fetched = ytt.fetch(video_id, languages=["en", "en-US", "en-GB"])
        raw_data = fetched.to_raw_data()
    except NoTranscriptFound:
        pass
    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video."}
    except VideoUnavailable:
        return {"error": "This video is unavailable or private."}
    except Exception as e:
        # Could be PoTokenRequired or another error — try listing next
        pass

    # Strategy 2: list all transcripts and pick best available
    if raw_data is None:
        try:
            transcript_list = ytt.list(video_id)
            # Try manually-created first, then generated
            transcript_obj = None
            try:
                transcript_obj = transcript_list.find_manually_created_transcript(
                    ["en", "en-US", "en-GB"]
                )
            except Exception:
                pass

            if transcript_obj is None:
                try:
                    transcript_obj = transcript_list.find_generated_transcript(
                        ["en", "en-US", "en-GB"]
                    )
                except Exception:
                    pass

            # Last resort: take whatever transcript is available (first in list)
            if transcript_obj is None:
                for t in transcript_list:
                    transcript_obj = t
                    break

            if transcript_obj is not None:
                raw_data = transcript_obj.fetch().to_raw_data()
        except TranscriptsDisabled:
            return {"error": "Transcripts are disabled for this video."}
        except VideoUnavailable:
            return {"error": "This video is unavailable or private."}
        except Exception as e:
            return {"error": f"Failed to fetch transcript: {str(e)}"}

    if not raw_data:
        return {"error": "No transcript found for this video. Try a video with captions enabled."}

    # ── Build output ──────────────────────────────────────────────────────────
    # raw_data is a list of dicts: [{"text": ..., "start": ..., "duration": ...}]
    full_text = " ".join(
        seg.get("text", "").strip() for seg in raw_data if seg.get("text")
    )
    full_text = re.sub(r"\s+", " ", full_text).strip()

    # Duration from last segment
    duration_minutes = 0.0
    if raw_data:
        last = raw_data[-1]
        total_seconds = last.get("start", 0) + last.get("duration", 0)
        duration_minutes = round(total_seconds / 60, 1)

    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "transcript": full_text,
        "segments": raw_data,
        "duration_minutes": duration_minutes,
        "word_count": len(full_text.split()),
    }


def get_video_metadata(video_id: str) -> dict:
    """Try to get video metadata using yt-dlp. Falls back gracefully."""
    try:
        import yt_dlp
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            return {
                "title": info.get("title", "Video"),
                "channel": info.get("uploader", "Unknown"),
                "view_count": info.get("view_count", 0),
                "thumbnail": info.get("thumbnail", ""),
                "description": (info.get("description") or "")[:500],
            }
    except Exception:
        return {
            "title": "Video",
            "channel": "Unknown",
            "view_count": 0,
            "thumbnail": "",
            "description": "",
        }


def chunk_transcript(transcript: str, max_chars: int = 12000) -> str:
    """Trim transcript to max_chars, keeping start and end."""
    if len(transcript) <= max_chars:
        return transcript
    half = max_chars // 2
    return transcript[:half] + "\n\n[...middle trimmed for length...]\n\n" + transcript[-half:]