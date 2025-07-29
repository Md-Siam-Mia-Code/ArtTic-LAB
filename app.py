# app.py
# --- STAGE 1 & 2 ---
import argparse, logging, sys, os, contextlib, signal, random
from helpers.cli_manager import setup_logging, log_system_info, APP_LOGGER_NAME
@contextlib.contextmanager
def suppress_stderr(disable=False):
    if disable: yield; return
    with open(os.devnull, 'w') as f, contextlib.redirect_stderr(f): yield
parser = argparse.ArgumentParser(description="ArtTic-LAB: A clean UI for Intel ARC GPUs.")
parser.add_argument("--disable-filters", action="store_true", help="Disable custom log filters.")
args = parser.parse_args()
setup_logging(disable_filters=args.disable_filters)
logger = logging.getLogger(APP_LOGGER_NAME)
with suppress_stderr(args.disable_filters):
    import torch, intel_extension_for_pytorch as ipex

# --- STAGE 3: APPLICATION IMPORTS & LOGIC ---
import diffusers, gradio as gr, time
from glob import glob
from ui import create_ui
from diffusers import (EulerAncestralDiscreteScheduler, EulerDiscreteScheduler,
                       LMSDiscreteScheduler, DPMSolverMultistepScheduler,
                       DDIMScheduler, UniPCMultistepScheduler)

SCHEDULER_MAP = {
    "Euler A": EulerAncestralDiscreteScheduler, "DPM++ 2M": DPMSolverMultistepScheduler,
    "DDIM": DDIMScheduler, "UniPC": UniPCMultistepScheduler,
    "Euler": EulerDiscreteScheduler, "LMS": LMSDiscreteScheduler,
}

current_pipe = None
current_model_name = ""

def get_available_models():
    return [os.path.basename(p).replace(".safetensors", "") for p in glob(os.path.join("./models", "*.safetensors"))]

def refresh_models_handler():
    logger.info("Refreshing model list...")
    return gr.Dropdown(choices=get_available_models())

def get_output_images():
    return sorted([f for f in glob(os.path.join("./outputs", "*.png"))], key=os.path.getmtime, reverse=True)

def randomize_seed_handler():
    new_seed = random.randint(0, 2**32 - 1)
    logger.info(f"Generated new random seed: {new_seed}")
    return new_seed

def swap_dimensions_handler(width, height):
    logger.info(f"Swapping dimensions from {width}x{height} to {height}x{width}.")
    return height, width

def load_model_handler(model_name, scheduler_name, progress=gr.Progress()):
    from pipelines import get_pipeline_for_model
    global current_pipe, current_model_name
    if not model_name: raise gr.Error("Please select a model from the dropdown.")
    
    try:
        logger.info(f"Loading model: {model_name}...")
        progress(0, desc=f"Getting pipeline for {model_name}...")
        current_pipe = get_pipeline_for_model(model_name)
        current_pipe.load_pipeline(progress)
        
        logger.info(f"Setting scheduler to: {scheduler_name}")
        SchedulerClass = SCHEDULER_MAP[scheduler_name]
        current_pipe.pipe.scheduler = SchedulerClass.from_config(current_pipe.pipe.scheduler.config)

        # Apply IPEX optimization. Diffusers will handle SDPA automatically.
        current_pipe.optimize_with_ipex(progress)
        
        # REMOVED: The erroneous call to enable_xformers_memory_efficient_attention() is gone.
        
        current_model_name = model_name
        is_xl = "SDXL" in current_pipe.__class__.__name__
        default_res = 1024 if is_xl else 512
        logger.info(f"Model loaded. Default resolution set to {default_res}x{default_res}.")
        progress(1, desc=f"Model '{model_name}' is ready!")
        status_message = f"Model Ready: {model_name}"
        return status_message, gr.Slider(value=default_res), gr.Slider(value=default_res)
    except Exception as e:
        logger.error(f"Failed to load model '{model_name}'. Full error: {e}")
        raise gr.Error(f"Failed to load model '{model_name}'. It may be corrupted or an unsupported type.")

def generate_image_handler(prompt, negative_prompt, steps, guidance, seed, width, height, progress=gr.Progress()):
    if not current_pipe: raise gr.Error("No model is loaded.")
    
    logger.info("Starting generation...")
    start_time = time.time()
    generator = torch.Generator("xpu").manual_seed(int(seed))
    def universal_progress_callback(pipe, step, timestep, callback_kwargs):
        progress(step / int(steps), desc=f"Sampling... {step + 1}/{int(steps)}")
        return callback_kwargs

    # The generation call is now clean. SDPA is used implicitly by default.
    image = current_pipe.generate(prompt=prompt, negative_prompt=negative_prompt, num_inference_steps=int(steps),
        guidance_scale=guidance, width=int(width), height=int(height), generator=generator,
        callback_on_step_end=universal_progress_callback).images[0]

    generation_time = time.time() - start_time
    logger.info(f"Generation completed in {generation_time:.2f} seconds.")
    os.makedirs("./outputs", exist_ok=True)
    filename = f"./outputs/{time.strftime('%Y%m%d-%H%M%S')}_{current_model_name}_{seed}.png"
    image.save(filename)
    info = f"Generated in {generation_time:.2f}s on '{current_model_name}'."
    return image, info

def signal_handler(sig, frame):
    print("\n"); logger.info("Ctrl+C detected. Shutting down ArtTic-LAB gracefully..."); sys.exit(0)

# --- STAGE 4: MAIN EXECUTION ---
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    if not args.disable_filters: os.system('cls' if os.name == 'nt' else 'clear')

    log_system_info()
    handlers = {
        "load_model": load_model_handler, "generate_image": generate_image_handler,
        "get_gallery": get_output_images, "refresh_models": refresh_models_handler,
        "randomize_seed": randomize_seed_handler, "swap_dims": swap_dimensions_handler,
    }
    app = create_ui(get_available_models(), list(SCHEDULER_MAP.keys()), handlers)
    logger.info("UI is ready. Launching Gradio server...")
    logger.info("Access ArtTic-LAB via the URLs below. Press Ctrl+C in this terminal to shutdown.")
    app.launch(share=True)