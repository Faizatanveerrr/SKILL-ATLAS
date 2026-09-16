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

# ---- Palette ----
NAVY_TOP = (14, 22, 38)       # gradient top
NAVY_BOTTOM = (8, 13, 24)     # gradient bottom
CARD_ACTIVE = (26, 35, 54)    # active bullet card fill
CARD_INACTIVE = (16, 21, 33)  # inactive bullet card fill
ACCENT_BLUE = (59, 130, 246)
ACCENT_MINT = (52, 211, 153)
TEXT_BRIGHT = (241, 245, 249)
TEXT_DIM = (120, 132, 150)
TRACK_COLOR = (30, 38, 56)    # progress bar track

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


# How many points can stack in the frame before they'd start overflowing.
# Only the last MAX_VISIBLE_POINTS are ever drawn as cards — older ones
# scroll off instead of piling up forever.
MAX_VISIBLE_POINTS = 4


def _vertical_gradient(width, height, top_color, bottom_color):
    """Pure-Pillow gradient background — no extra dependencies."""
    base = Image.new("RGB", (width, height), top_color)
    draw = ImageDraw.Draw(base)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base


def create_progressive_slide(points: list[str], active_index: int, output_path: str,
                              lesson_title: str, width=1280, height=720) -> str:
    img = _vertical_gradient(width, height, NAVY_TOP, NAVY_BOTTOM)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([(0, 0), (width, 6)], fill=ACCENT_BLUE)

    title_font = _load_font(BOLD_FONT_CANDIDATES, 30)
    point_font = _load_font(REGULAR_FONT_CANDIDATES, 30)
    point_font_bold = _load_font(BOLD_FONT_CANDIDATES, 32)
    number_font = _load_font(BOLD_FONT_CANDIDATES, 22)
    progress_font = _load_font(REGULAR_FONT_CANDIDATES, 20)

    # Title
    draw.text((60, 44), lesson_title.upper(), font=title_font, fill=ACCENT_MINT)
    draw.line([(60, 92), (width - 60, 92)], fill=(40, 50, 70), width=1)

    # Sliding window: only render the last MAX_VISIBLE_POINTS as cards
    window_start = max(0, active_index - (MAX_VISIBLE_POINTS - 1))
    visible_points = points[window_start:active_index + 1]
    active_in_window = active_index - window_start

    card_x, card_w = 60, width - 120
    y = 130
    card_gap = 18

    for i, point in enumerate(visible_points):
        is_active = (i == active_in_window)
        global_index = window_start + i

        wrapped = textwrap.fill(point, width=52)
        line_count = wrapped.count("\n") + 1
        font = point_font_bold if is_active else point_font
        text_h = (font.size + 12) * line_count
        card_h = text_h + 36

        fill = CARD_ACTIVE if is_active else CARD_INACTIVE
        draw.rounded_rectangle(
            [(card_x, y), (card_x + card_w, y + card_h)],
            radius=14, fill=fill,
        )
        if is_active:
            # Accent left border to draw the eye to the current point
            draw.rounded_rectangle(
                [(card_x, y), (card_x + 6, y + card_h)],
                radius=3, fill=ACCENT_MINT,
            )

        # Numbered badge instead of a plain dot
        badge_cx, badge_cy, badge_r = card_x + 34, y + card_h // 2, 16
        badge_color = ACCENT_MINT if is_active else TRACK_COLOR
        draw.ellipse(
            [(badge_cx - badge_r, badge_cy - badge_r), (badge_cx + badge_r, badge_cy + badge_r)],
            fill=badge_color,
        )
        num_text = str(global_index + 1)
        draw.text((badge_cx, badge_cy), num_text, font=number_font,
                   fill=NAVY_TOP if is_active else TEXT_DIM, anchor="mm")

        text_color = TEXT_BRIGHT if is_active else TEXT_DIM
        draw.multiline_text((card_x + 68, y + 18), wrapped, font=font, fill=text_color, spacing=10)

        y += card_h + card_gap

    # Progress bar (replaces the old plain "N / M" text-only counter)
    bar_x, bar_y, bar_w, bar_h = 60, height - 46, width - 120, 10
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], radius=5, fill=TRACK_COLOR)
    progress_ratio = (active_index + 1) / max(len(points), 1)
    filled_w = max(int(bar_w * progress_ratio), bar_h)
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h)], radius=5, fill=ACCENT_BLUE)
    draw.text((bar_x + bar_w, bar_y - 8), f"{active_index + 1} / {len(points)}",
               font=progress_font, fill=TEXT_DIM, anchor="ra")

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