# ArtTic-LAB - Web UI v0.1
# A clean, modern, and powerful UI for image generation on Intel ARC GPUs.

import torch
import intel_extension_for_pytorch as ipex
from diffusers import StableDiffusionPipeline
import gradio as gr
import time
import os

# --- Configuration ---
# We can add more models here in the future
MODEL_MAP = {
    "ultraRealisticByStable_v30": "./models/ultraRealisticByStable_v30.safetensors"
}
OUTPUT_PATH = "./outputs"
DEFAULT_MODEL = "ultraRealisticByStable_v30"

# --- Global State ---
# We will only load the model once to keep things fast.
pipe = None
current_model_name = None

# --- Core Loading and Optimization Logic ---
def load_model(model_name):
    global pipe, current_model_name
    
    # Check if the requested model is already loaded
    if model_name == current_model_name and pipe is not None:
        print(f"Model '{model_name}' is already loaded.")
        return
        
    print(f"Loading model: {model_name}...")
    model_path = MODEL_MAP[model_name]
    
    if not torch.xpu.is_available():
        raise gr.Error("Intel ARC GPU (XPU) not detected. Please check your drivers and installation.")
    
    # Use bfloat16 for better performance
    dtype = torch.bfloat16
    
    # Load the Stable Diffusion Pipeline from the single file
    new_pipe = StableDiffusionPipeline.from_single_file(
        model_path,
        torch_dtype=dtype,
        use_safetensors=True
    )
    print("Model loaded. Moving to XPU (ARC GPU)...")
    new_pipe = new_pipe.to("xpu")

    # Optimize the model with IPEX for a massive speedup
    print("Optimizing model with IPEX. This may take a moment...")
    new_pipe.unet = ipex.optimize(new_pipe.unet.eval(), dtype=dtype, inplace=True)
    
    # Update the global pipe and model name
    pipe = new_pipe
    current_model_name = model_name
    print(f"Model '{model_name}' is now ready.")

# --- The Generation Function (Called by the UI) ---
def generate_image(prompt, negative_prompt, steps, guidance, seed):
    if pipe is None:
        raise gr.Error("Model not loaded. Please wait for the model to finish loading.")
        
    print(f"Generating image with settings: "
          f"Prompt: '{prompt}', "
          f"Steps: {steps}, Guidance: {guidance}, Seed: {seed}")
          
    start_time = time.time()
    
    # Use a generator for reproducible results. If seed is -1, use a random seed.
    generator = torch.Generator("xpu").manual_seed(seed) if seed != -1 else torch.Generator("xpu")
    
    # Use autocast for performance
    with torch.xpu.amp.autocast(enabled=True, dtype=torch.bfloat16):
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=int(steps),
            guidance_scale=guidance,
            generator=generator
        ).images[0]

    end_time = time.time()
    generation_time = end_time - start_time
    print(f"Image generated in {generation_time:.2f} seconds.")

    # Save the image with a unique name
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_filename = f"{OUTPUT_PATH}/{timestamp}_{seed}.png"
    image.save(output_filename)
    print(f"Image saved to: {output_filename}")
    
    # Return the image and a performance string to the UI
    return image, f"Generated in {generation_time:.2f} seconds."

# --- Building the Gradio UI ---
def create_ui():
    with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as app:
        gr.Markdown("# 🎨 ArtTic-LAB")
        gr.Markdown("A clean, modern, and powerful UI for image generation on Intel ARC GPUs.")
        
        with gr.Row():
            with gr.Column(scale=2):
                prompt = gr.Textbox(label="Prompt", value="photo of a beautiful Scandinavian woman, 8k, ultra realistic", lines=3)
                negative_prompt = gr.Textbox(label="Negative Prompt", placeholder="e.g., ugly, deformed, blurry", lines=2)
                
                with gr.Row():
                    steps = gr.Slider(label="Steps", minimum=1, maximum=100, value=25, step=1)
                    guidance = gr.Slider(label="Guidance Scale", minimum=1, maximum=20, value=7.5, step=0.1)
                
                with gr.Row():
                    seed = gr.Number(label="Seed", value=12345, precision=0)
                    randomize_seed_btn = gr.Button("Randomize")
                
                generate_btn = gr.Button("Generate", variant="primary")

            with gr.Column(scale=3):
                output_image = gr.Image(label="Result", type="pil", interactive=False)
                info_text = gr.Textbox(label="Info", interactive=False)

        # UI Event Handlers
        generate_btn.click(
            fn=generate_image,
            inputs=[prompt, negative_prompt, steps, guidance, seed],
            outputs=[output_image, info_text]
        )
        
        # Helper to set a random seed
        def random_seed():
            return -1 # Our backend knows -1 means random
        randomize_seed_btn.click(fn=random_seed, inputs=[], outputs=seed)

    return app

# --- Main Entry Point ---
if __name__ == "__main__":
    # 1. Create the UI
    app = create_ui()
    
    # 2. Pre-load the default model before launching the UI
    # This makes the app responsive as soon as it starts
    load_model(DEFAULT_MODEL)
    
    # 3. Launch the Gradio Web UI
    # share=True creates a public link (optional, remove if you only want local access)
    app.launch(share=True)