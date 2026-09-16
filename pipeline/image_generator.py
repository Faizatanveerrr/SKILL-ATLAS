"""
Deterministic, zero-cost cover/thumbnail generator.

This replaces a previous Stable Diffusion (diffusers + torch) implementation.
SD1.5 requires ~4GB of model weights downloaded at runtime and several GB of
RAM just to load — that's incompatible with Streamlit Community Cloud's free
tier (1GB RAM, no GPU), which is what was causing the app to crash/hang on
the Create Course page.

Instead, this generates clean geometric "poster" style artwork with Pillow:
a gradient background, a handful of soft decorative shapes placed
deterministically from a hash of the input (so the same topic/title/url
always produces the same look, mirroring the old `seed` behavior), and the
title text laid out on top. No model download, no GPU, runs in milliseconds.

Function names and signatures are unchanged from the previous version, so
nothing that imports this module (views/create_course.py, etc.) needs to
change.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import hashlib
import os
import random
import textwrap
from pathlib import Path

# A small set of curated two-tone gradients + accent color, so output always
# looks intentional rather than random-RGB garish. Picked by hash, not by
# actual randomness, so the same input is always the same palette.
PALETTES = [
    {"top": (17, 24, 39), "bottom": (30, 58, 138), "accent": (96, 165, 250)},   # navy/blue
    {"top": (30, 27, 75), "bottom": (76, 29, 149), "accent": (167, 139, 250)},  # indigo/purple
    {"top": (6, 35, 42), "bottom": (13, 74, 84), "accent": (45, 212, 191)},     # teal
    {"top": (15, 23, 42), "bottom": (40, 30, 20), "accent": (251, 146, 60)},    # slate/orange
    {"top": (6, 40, 30), "bottom": (6, 78, 59), "accent": (52, 211, 153)},      # green/mint
    {"top": (46, 16, 30), "bottom": (88, 24, 69), "accent": (244, 114, 182)},   # magenta
]

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


def _seed_from(text: str, seed: int | None) -> int:
    """Same string (or explicit seed) always produces the same artwork,
    mirroring the old Stable Diffusion `seed` parameter's determinism."""
    if seed is not None:
        return seed
    return int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)


def _palette_for(seed: int) -> dict:
    return PALETTES[seed % len(PALETTES)]


def _vertical_gradient(width: int, height: int, top_color, bottom_color) -> Image.Image:
    base = Image.new("RGB", (width, height), top_color)
    draw = ImageDraw.Draw(base)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base


def _add_decorative_shapes(img: Image.Image, seed: int, accent, count: int = 6) -> Image.Image:
    """Soft, semi-transparent blobs for visual texture — deterministic
    per seed, kept out of the way of wherever text will be placed by the
    caller (shapes lean toward the right/edges)."""
    rng = random.Random(seed)
    width, height = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    for _ in range(count):
        r = rng.randint(int(min(width, height) * 0.08), int(min(width, height) * 0.28))
        cx = rng.randint(int(width * 0.55), width + r // 2)  # bias toward right side
        cy = rng.randint(-r // 2, height + r // 2)
        alpha = rng.randint(18, 45)
        odraw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(*accent, alpha))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=min(width, height) * 0.02))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _draw_title_block(img: Image.Image, title: str, accent, subtitle: str | None = None,
                       max_width_frac: float = 0.62) -> None:
    draw = ImageDraw.Draw(img)
    width, height = img.size

    title_font = _load_font(BOLD_FONT_CANDIDATES, max(28, width // 22))
    sub_font = _load_font(REGULAR_FONT_CANDIDATES, max(16, width // 45))

    margin_x = int(width * 0.06)
    wrap_width = max(10, int(max_width_frac * width / (title_font.size * 0.55)))
    wrapped_title = textwrap.fill(title, width=wrap_width)

    # Small accent tick above the title
    tick_y = int(height * 0.30)
    draw.rectangle([(margin_x, tick_y), (margin_x + 56, tick_y + 5)], fill=accent)

    draw.multiline_text(
        (margin_x, tick_y + 24), wrapped_title, font=title_font,
        fill=(245, 247, 250), spacing=10,
    )

    if subtitle:
        title_h = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font, spacing=10)[3]
        sub_wrap = textwrap.fill(subtitle, width=int(wrap_width * 1.3))
        draw.multiline_text(
            (margin_x, tick_y + 24 + title_h + 18), sub_wrap, font=sub_font,
            fill=(200, 208, 220), spacing=8,
        )


# -------------------------------------------------------
# Used by Discover Page (legacy: one illustration per topic)
# -------------------------------------------------------
def generate_image(topic: str, seed: int | None = None) -> str:
    seed = _seed_from(topic, seed)
    palette = _palette_for(seed)

    width, height = 512, 512
    img = _vertical_gradient(width, height, palette["top"], palette["bottom"])
    img = _add_decorative_shapes(img, seed, palette["accent"], count=5)
    _draw_title_block(img, topic, palette["accent"], max_width_frac=0.75)

    Path("generated_images").mkdir(exist_ok=True)
    filename = f"generated_images/{topic.replace(' ', '_')}.png"
    img.save(filename)
    return filename


# -------------------------------------------------------
# Used by result cards: one distinct, cached image per resource
# -------------------------------------------------------
def get_or_generate_resource_thumbnail(title: str, url: str) -> str:
    """
    Returns a path to a cached generated thumbnail for a specific resource.
    Generated once per resource (keyed by URL hash) and reused after that.
    """
    Path("generated_images").mkdir(exist_ok=True)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    filename = f"generated_images/resource_{url_hash}.png"

    if os.path.exists(filename):
        return filename

    seed = int(url_hash, 16) % (2**32)
    palette = _palette_for(seed)

    width, height = 512, 512
    img = _vertical_gradient(width, height, palette["top"], palette["bottom"])
    img = _add_decorative_shapes(img, seed, palette["accent"], count=5)
    _draw_title_block(img, title, palette["accent"], max_width_frac=0.75)

    img.save(filename)
    return filename


# -------------------------------------------------------
# Used by Create Course Page
# -------------------------------------------------------
def create_course_cover(title: str, description: str, seed: int | None = None) -> str:
    seed = _seed_from(title, seed)
    palette = _palette_for(seed)

    width, height = 1024, 576
    img = _vertical_gradient(width, height, palette["top"], palette["bottom"])
    img = _add_decorative_shapes(img, seed, palette["accent"], count=8)
    _draw_title_block(img, title, palette["accent"], subtitle=description, max_width_frac=0.6)

    Path("generated_covers").mkdir(exist_ok=True)
    filename = f"generated_covers/{title.replace(' ', '_')}.png"
    img.save(filename)
    return filename
