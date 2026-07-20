import re
from youtube_transcript_api import YouTubeTranscriptApi


def is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url


def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def get_youtube_transcript(url: str) -> str | None:
    video_id = extract_video_id(url)
    if not video_id:
        return None
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        full_text = " ".join(snippet.text for snippet in fetched_transcript)
        return full_text
    except Exception as e:
        print(f"Could not get transcript for {url}: {e}")
        return None