from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image
import torch
import threading
import os
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

pipe = None
_pipe_lock = threading.Lock()


def load_model():
    global pipe

    if pipe is None:
        with _pipe_lock:
            if pipe is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                # float16 is not supported on CPU -- must fall back to float32
                dtype = torch.float16 if device == "cuda" else torch.float32

                logger.info(f"Loading Stable Diffusion pipeline on {device} ({dtype})")

                _pipe = StableDiffusionPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=dtype
                )

                # DPMSolver avoids PNDM's cross-step buffer, which caused shape
                # mismatches when different image sizes were generated back to back
                _pipe.scheduler = DPMSolverMultistepScheduler.from_config(_pipe.scheduler.config)

                _pipe.to(device)
                _pipe.enable_attention_slicing()
                if device == "cuda":
                    _pipe.vae.enable_slicing()

                pipe = _pipe

    return pipe


def _get_generator(seed: int | None):
    """Returns a generator for reproducible output, or None for fully
    random generation if seed is None. Uses whatever device the pipe
    is currently on."""
    if seed is None:
        return None
    device = pipe.device.type if pipe is not None else "cpu"
    return torch.Generator(device=device).manual_seed(seed)


# -------------------------------------------------------
# Used by Discover Page (legacy: one illustration per topic)
# -------------------------------------------------------
def generate_image(topic: str, seed: int | None = None):

    model = load_model()

    # Concrete, scene-based description instead of just style keywords.
    # SD1.5 has weak grasp of abstract nouns like "system design" on their
    # own -- give it something to actually depict (a scene/metaphor with
    # real objects), not just a mood/palette, or it defaults to generic
    # abstract-icon collages regardless of the topic.
    prompt = f"""
A clear educational diagram-style illustration depicting the concept of {topic},
shown as a single coherent scene with recognizable objects and connected elements
relevant to {topic}, flat vector art style, isometric perspective,
blue and white color palette, clean composition, single focal subject,
professional tech illustration, no text, no logos
"""

    # Steers away from the common SD1.5 failure mode for vague minimal
    # prompts: scattered disconnected shapes with no coherent subject.
    negative_prompt = """
random shapes, disconnected objects, abstract clutter, collage, noise,
watermark, text, letters, blurry, deformed, extra objects, low quality
"""

    generator = _get_generator(seed)

    with _pipe_lock:
        image = model(
            prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=30,
            guidance_scale=9.0,
            width=512,
            height=512,
            generator=generator,
        ).images[0]

    Path("generated_images").mkdir(exist_ok=True)

    filename = f"generated_images/{topic.replace(' ', '_')}.png"

    image.save(filename)

    return filename


# -------------------------------------------------------
# Used by result cards: one distinct, cached image per resource
# -------------------------------------------------------
def get_or_generate_resource_thumbnail(title: str, url: str) -> str:
    """
    Returns a path to a cached AI-generated thumbnail for a specific resource.
    Generated once per resource (keyed by URL hash) and reused after that.
    """
    Path("generated_images").mkdir(exist_ok=True)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    filename = f"generated_images/resource_{url_hash}.png"

    if os.path.exists(filename):
        return filename

    model = load_model()

    # Concrete, scene-based description instead of just style keywords --
    # see generate_image() above for why this matters for SD1.5.
    prompt = f"""
A clear educational diagram-style illustration depicting the concept of {title},
shown as a single coherent scene with recognizable objects and connected elements
relevant to {title}, flat vector art style, isometric perspective,
blue and white color palette, clean composition, single focal subject,
professional tech illustration, no text, no logos
"""

    negative_prompt = """
random shapes, disconnected objects, abstract clutter, collage, noise,
watermark, text, letters, blurry, deformed, extra objects, low quality
"""

    seed = int(url_hash, 16) % (2**32)
    generator = _get_generator(seed)

    with _pipe_lock:
        image = model(
            prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=25,
            guidance_scale=9.0,
            width=512,
            height=512,
            generator=generator,
        ).images[0]

    image.save(filename)

    return filename


# -------------------------------------------------------
# Used by Create Course Page
# -------------------------------------------------------
def create_course_cover(title: str, description: str, seed: int | None = None):

    model = load_model()

    prompt = f"""
Professional online course cover.

Topic: {title}

Description:
{description}

Modern digital illustration.
Blue and purple color palette.
Minimal.
Futuristic.
High quality.
No text.
16:9 composition.
Beautiful lighting.
Educational platform banner.
"""

    generator = _get_generator(seed)

    # SD 1.5 was trained at 512x512. Requesting 1024x576 directly pushes
    # the model far outside its native resolution and produces fractured
    # / duplicated-subject output. Generate near-native, then upscale.
    gen_width, gen_height = 768, 448
    target_width, target_height = 1024, 576

    with _pipe_lock:
        image = model(
            prompt,
            num_inference_steps=35,
            guidance_scale=8,
            width=gen_width,
            height=gen_height,
            generator=generator,
        ).images[0]

    if (gen_width, gen_height) != (target_width, target_height):
        image = image.resize((target_width, target_height), Image.LANCZOS)

    Path("generated_covers").mkdir(exist_ok=True)

    filename = f"generated_covers/{title.replace(' ', '_')}.png"

    image.save(filename)

    return filename