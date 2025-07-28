# ArtTic-LAB - Core Engine v0.2
# A script to test a single image generation on Intel ARC GPUs.

import torch
import intel_extension_for_pytorch as ipex
from diffusers import StableDiffusionPipeline
import time
import os

# --- Configuration ---
MODEL_PATH = "./models/ultraRealisticByStable_v30.safetensors"
OUTPUT_PATH = "./outputs"
PROMPT = "photo of a beautiful Scandinavian woman, 8k, ultra realistic, cinematic lighting, masterpiece"

# --- Main Generation Function ---
def main():
    print("--- ArtTic-LAB Core Engine ---")
    
    # 1. Check for Intel ARC GPU (XPU)
    if not torch.xpu.is_available():
        print("Error: Intel ARC GPU (XPU) not detected. Please check your drivers and installation.")
        return
    
    print("Intel ARC GPU detected!")
    # Use bfloat16 for better performance, your A770 16GB supports this well.
    dtype = torch.bfloat16 
    
    # 2. Load the Stable Diffusion Pipeline
    print(f"Loading model: {MODEL_PATH}")
    # We use `from_single_file` which is the modern way to load .safetensors or .ckpt files
    pipe = StableDiffusionPipeline.from_single_file(
        MODEL_PATH,
        torch_dtype=dtype,
        use_safetensors=True
    )
    print("Model loaded successfully.")

    # 3. Move the model to the ARC GPU
    print("Moving model to XPU (ARC GPU)...")
    pipe = pipe.to("xpu")

    # 4. (Optional but Recommended) Optimize the model with IPEX
    # This step can significantly speed up inference time.
    print("Optimizing model with IPEX. This may take a moment...")
    pipe.unet = ipex.optimize(pipe.unet.eval(), dtype=dtype, inplace=True)
    print("Model optimized.")

    # 5. Generate the image
    print(f"\nGenerating image with prompt: '{PROMPT}'")
    start_time = time.time()
    
    # The generator allows us to set a seed for reproducible results
    generator = torch.Generator("xpu").manual_seed(12345) 
    
    with torch.xpu.amp.autocast(enabled=True, dtype=dtype):
        image = pipe(
            prompt=PROMPT,
            num_inference_steps=25,
            guidance_scale=7.5,
            generator=generator
        ).images[0]

    end_time = time.time()
    print(f"Image generated in {end_time - start_time:.2f} seconds.")

    # 6. Save the image
    # We use a timestamp to ensure unique filenames
    os.makedirs(OUTPUT_PATH, exist_ok=True) # Ensure output directory exists
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_filename = f"{OUTPUT_PATH}/{timestamp}.png"
    image.save(output_filename)
    print(f"Image saved to: {output_filename}")
    print("\n--- Generation Complete ---")

# --- Run the script ---
if __name__ == "__main__":
    main()