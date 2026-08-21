from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
import moviepy
import os
import re
import textwrap
from concurrent.futures import ThreadPoolExecutor

OUTPUT_DIR = os.path.abspath("generated_videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NAVY = (11, 18, 32)
ACCENT_BLUE = (59, 130, 246)
ACCENT_MINT = (52, 211, 153)
TEXT_BRIGHT = (241, 245, 249)
TEXT_DIM = (100, 112, 130)

# Cross-platform font fallback — "arialbd.ttf"/"arial.ttf" only exist on Windows,
# so on Linux (servers, most deployments) this was silently falling back to
# PIL's tiny built-in default font every time.
BOLD_FONT_CANDIDATES = [
    "arialbd.ttf",
    "DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
REGULAR_FONT_CANDIDATES = [
    "arial.ttf",
    "DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def text_to_speech(text: str, output_path: str) -> str:
    tts = gTTS(text=text, lang="en")
    tts.save(output_path)
    return output_path


def split_into_points(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    return [s.strip() for s in sentences if s.strip()]


# How many points can stack in the 720px-tall frame below the title before
# they'd start overflowing. Only the last MAX_VISIBLE_POINTS are ever drawn —
# older ones scroll off instead of piling up forever. Without this, longer
# lesson content (many sentences) pushed the "active" highlighted point below
# the visible canvas, so the video appeared frozen on the last slide that
# actually fit on screen even though internally it kept changing.
MAX_VISIBLE_POINTS = 4


def create_progressive_slide(points: list[str], active_index: int, output_path: str,
                              lesson_title: str, width=1280, height=720) -> str:
    img = Image.new("RGB", (width, height), color=NAVY)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (width, 8)], fill=ACCENT_BLUE)

    title_font = _load_font(BOLD_FONT_CANDIDATES, 30)
    point_font = _load_font(REGULAR_FONT_CANDIDATES, 34)
    point_font_bold = _load_font(BOLD_FONT_CANDIDATES, 36)

    draw.text((60, 40), lesson_title.upper(), font=title_font, fill=ACCENT_MINT)

    # Only show a sliding window ending at the active point, so text never
    # overflows the frame no matter how many sentences the lesson has.
    window_start = max(0, active_index - (MAX_VISIBLE_POINTS - 1))
    visible_points = points[window_start:active_index + 1]
    active_index_in_window = active_index - window_start

    y = 150
    line_gap = 26
    for i, point in enumerate(visible_points):
        is_active = (i == active_index_in_window)
        color = TEXT_BRIGHT if is_active else TEXT_DIM
        font = point_font_bold if is_active else point_font

        bullet_color = ACCENT_MINT if is_active else TEXT_DIM
        draw.ellipse([(60, y + 12), (76, y + 28)], fill=bullet_color)

        wrapped = textwrap.fill(point, width=55)
        draw.multiline_text((100, y), wrapped, font=font, fill=color, spacing=10)

        line_count = wrapped.count("\n") + 1
        y += (font.size + 10) * line_count + line_gap

    # Small progress indicator so it's visually obvious the lesson is moving
    # forward even during a long slide window.
    progress_font = _load_font(REGULAR_FONT_CANDIDATES, 22)
    progress_text = f"{active_index + 1} / {len(points)}"
    draw.text((width - 140, height - 50), progress_text, font=progress_font, fill=TEXT_DIM)

    img.save(output_path)
    return output_path


def zoom_effect(clip, zoom_ratio=0.06):
    def resize_fn(t):
        return 1 + zoom_ratio * (t / clip.duration)
    return clip.resized(resize_fn)


def create_lesson_video(lesson_title: str, lesson_text: str, lesson_id: str) -> str:
    """
    Generates narration per-sentence (instead of one block) so each slide's
    on-screen duration is taken from the *actual* audio length for that
    sentence rather than estimated from character count. This keeps the
    highlighted point in sync with what's being said, instead of drifting
    later and later as the lesson goes on.
    """
    video_path = os.path.join(OUTPUT_DIR, f"{lesson_id}_video.mp4")

    points = split_into_points(lesson_text)
    if not points:
        points = [lesson_text]

    # 1. Generate one narration clip per sentence. gTTS is a network call per
    # sentence — doing these one at a time was the main source of slowness
    # for longer lessons. They're independent I/O-bound calls, so we fire
    # them off concurrently and only wait once at the end.
    segment_audio_paths = [os.path.join(OUTPUT_DIR, f"{lesson_id}_seg_{i}.mp3") for i in range(len(points))]

    with ThreadPoolExecutor(max_workers=min(6, len(points))) as executor:
        futures = [
            executor.submit(text_to_speech, point, seg_path)
            for point, seg_path in zip(points, segment_audio_paths)
        ]
        for future in futures:
            future.result()  # surfaces any TTS errors here instead of silently continuing

    audio_clips = []
    durations = []
    for seg_path in segment_audio_paths:
        clip = AudioFileClip(seg_path)
        durations.append(clip.duration)
        audio_clips.append(clip)

    # 2. Stitch the per-sentence narration into one continuous audio track.
    full_audio = concatenate_audioclips(audio_clips)
    audio_path = os.path.join(OUTPUT_DIR, f"{lesson_id}_audio.mp3")
    full_audio.write_audiofile(audio_path, logger=None)

    # 3. Build slides using the REAL per-sentence durations (no guessing).
    slide_paths = []
    video_clips = []
    for i, dur in enumerate(durations):
        slide_path = os.path.join(OUTPUT_DIR, f"{lesson_id}_slide_{i}.png")
        create_progressive_slide(points, i, slide_path, lesson_title)
        slide_paths.append(slide_path)

        clip = ImageClip(slide_path).with_duration(dur + 0.35)
        clip = zoom_effect(clip, zoom_ratio=0.05)
        clip = clip.with_effects([moviepy.vfx.CrossFadeIn(0.35)])
        video_clips.append(clip)

    video = concatenate_videoclips(video_clips, method="compose", padding=-0.35)
    video = video.with_audio(full_audio)
    video.write_videofile(
        video_path,
        fps=15,
        logger=None,
        preset="ultrafast",
        threads=4,
        audio_codec="aac",
    )

    # 4. Cleanup — close all open clips and remove intermediate files.
    for clip in audio_clips:
        clip.close()
    full_audio.close()
    video.close()

    for path in segment_audio_paths + slide_paths:
        try:
            os.remove(path)
        except OSError:
            pass
    try:
        os.remove(audio_path)
    except OSError:
        pass

    return video_path