# app.py
import gradio as gr
import torch
import time
import os
from glob import glob
from ui import create_ui
from pipelines import get_pipeline_for_model

# --- Global State ---
current_pipe = None
current_model_name = ""

# --- Helper Functions ---
def get_available_models():
    model_paths = glob(os.path.join("./models", "*.safetensors"))
    return [os.path.basename(p).replace(".safetensors", "") for p in model_paths]

def get_output_images():
    files = [f for f in glob(os.path.join("./outputs", "*.png"))]
    return sorted(files, key=os.path.getmtime, reverse=True)

# --- Handler Functions (Bridge between UI and Pipelines) ---
def load_model_handler(model_name, progress=gr.Progress()):
    global current_pipe, current_model_name
    if not model_name:
        return "Please select a model."
    if model_name == current_model_name:
        return f"Model '{model_name}' is already loaded."

    progress(0, desc=f"Getting pipeline for {model_name}...")
    current_pipe = get_pipeline_for_model(model_name)
    
    current_pipe.load_pipeline(progress)
    current_pipe.optimize_with_ipex(progress)
    
    current_model_name = model_name
    progress(1, desc=f"Model '{model_name}' is ready!")
    return f"Successfully loaded {model_name}."

def generate_image_handler(prompt, negative_prompt, steps, guidance, seed, progress=gr.Progress()):
    if not current_pipe:
        raise gr.Error("No model is loaded. Please load a model first.")
    
    start_time = time.time()
    generator = torch.Generator("xpu").manual_seed(seed) if seed != -1 else torch.Generator("xpu")
    
    def universal_progress_callback(pipe, step, timestep, callback_kwargs):
        progress(step / int(steps), desc=f"Sampling... {step + 1}/{int(steps)}")
        return callback_kwargs

    image = current_pipe.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=int(steps),
        guidance_scale=guidance,
        generator=generator,
        callback_on_step_end=universal_progress_callback 
    ).images[0]
    
    generation_time = time.time() - start_time
    
    os.makedirs("./outputs", exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"./outputs/{timestamp}_{current_model_name}_{seed}.png"
    image.save(filename)
    
    info = f"Generated in {generation_time:.2f}s on '{current_model_name}'."
    return image, info

# --- Main Entry Point ---
if __name__ == "__main__":
    handlers = {
        "load_model": load_model_handler,
        "generate_image": generate_image_handler,
        "get_gallery": get_output_images,
    }
    app = create_ui(get_available_models(), handlers)
    
    available_models = get_available_models()
    if available_models:
        print("--- Pre-loading initial model ---")
        try:
            class DummyProgress:
                def __call__(self, *args, **kwargs): pass
            load_model_handler(available_models[0], progress=DummyProgress())
            print("--- Initial model loaded ---")
        except Exception as e:
            print(f"Could not pre-load model: {e}")
    
    app.launch(share=True)