from diffusers import StableDiffusionPipeline
import torch

model_id = "runwayml/stable-diffusion-v1-5"

pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
)

pipe.enable_model_cpu_offload()
print("Torch CUDA:", torch.cuda.is_available())
print("Pipeline device:", pipe.device)

# Allocate a tensor directly on the GPU
x = torch.rand(1000, 1000, device="cuda")
print("Tensor device:", x.device)

# Memory optimizations for 6 GB VRAM
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

prompt = "A futuristic tesla city at sunset, ultra realistic, cinematic lighting, 8k"

image = pipe(
    prompt,
    num_inference_steps=30,
    guidance_scale=7.5,
).images[0]


print("GPU memory after:",
      torch.cuda.memory_allocated() / 1024**2, "MB")
image.save("cyberpunk_city.png")

print("Image generated successfully!")