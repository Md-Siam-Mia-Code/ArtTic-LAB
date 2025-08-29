# core/logic.py
import torch
import os
import time
import random
import logging
from glob import glob
from diffusers import (
    EulerAncestralDiscreteScheduler,
    EulerDiscreteScheduler,
    LMSDiscreteScheduler,
    DPMSolverMultistepScheduler,  # Corrected typo: Multistep
    DDIMScheduler,
    UniPCMultistepScheduler,  # Corrected typo: Multistep
)
from pipelines import get_pipeline_for_model
from pipelines.sdxl_pipeline import SDXLPipeline
from pipelines.sd2_pipeline import SD2Pipeline
from pipelines.sd3_pipeline import SD3Pipeline

# --- Application State ---
# This dictionary will hold the application's state, accessible by all functions.
# It's a cleaner approach than using multiple global variables.
app_state = {
    "current_pipe": None,
    "current_model_name": "",
    "is_model_loaded": False,
    "status_message": "No model loaded.",
}

# --- Constants ---
APP_LOGGER_NAME = "arttic_lab"
logger = logging.getLogger(APP_LOGGER_NAME)
SCHEDULER_MAP = {
    "Euler A": EulerAncestralDiscreteScheduler,
    "DPM++ 2M": DPMSolverMultistepScheduler,  # Corrected typo
    "DDIM": DDIMScheduler,
    "UniPC": UniPCMultistepScheduler,  # Corrected typo
    "Euler": EulerDiscreteScheduler,
    "LMS": LMSDiscreteScheduler,
}

# --- Core Functions ---


def get_config():
    """Returns the initial configuration for the UI."""
    return {
        "models": get_available_models(),
        "schedulers": list(SCHEDULER_MAP.keys()),
        "gallery_images": get_output_images(),
    }


def get_available_models():
    """Scans the models directory and returns a list of available model names."""
    models_path = os.path.join("./models", "*.safetensors")
    return [os.path.basename(p).replace(".safetensors", "") for p in glob(models_path)]


def get_output_images():
    """Returns a sorted list of generated images from the outputs directory."""
    outputs_path = os.path.join("./outputs", "*.png")
    # Sort by modification time, newest first, and return just the filenames
    return [
        os.path.basename(f)
        for f in sorted(glob(outputs_path), key=os.path.getmtime, reverse=True)
    ]


def unload_model():
    """Unloads the current model from VRAM and clears the cache."""
    if not app_state["is_model_loaded"]:
        logger.info("Unload command received, but no model is currently loaded.")
        return {"status_message": "No model loaded."}

    logger.info(f"Unloading model '{app_state['current_model_name']}' from VRAM...")
    pipe_to_delete = app_state["current_pipe"]

    # Explicitly delete the pipeline object
    if hasattr(pipe_to_delete, "pipe"):
        del pipe_to_delete.pipe
    del pipe_to_delete

    # Reset application state
    app_state["current_pipe"] = None
    app_state["current_model_name"] = ""
    app_state["is_model_loaded"] = False
    app_state["status_message"] = "No model loaded."

    # Clear PyTorch cache for XPU
    torch.xpu.empty_cache()

    logger.info("Model unloaded and VRAM cache cleared.")
    return {"status_message": app_state["status_message"]}


def load_model(
    model_name, scheduler_name, vae_tiling, cpu_offload, progress_callback=None
):
    """Loads a new model into memory, applying specified configurations."""
    if not model_name:
        raise ValueError("Please select a model from the dropdown.")

    def update_progress(progress, desc):
        if progress_callback:
            progress_callback(progress, desc)

    try:
        # If a model is already loaded, unload it first.
        if app_state["is_model_loaded"]:
            unload_model()

        logger.info(f"Loading model: {model_name}...")
        update_progress(0, f"Getting pipeline for {model_name}...")

        pipe = get_pipeline_for_model(model_name)
        pipe.load_pipeline(lambda p, d: update_progress(p, d))

        pipe.place_on_device(use_cpu_offload=cpu_offload)
        pipe.optimize_with_ipex(lambda p, d: update_progress(p, d))

        if not isinstance(pipe, SD3Pipeline):
            logger.info(f"Setting scheduler to: {scheduler_name}")
            SchedulerClass = SCHEDULER_MAP[scheduler_name]
            pipe.pipe.scheduler = SchedulerClass.from_config(pipe.pipe.scheduler.config)

        # VAE Tiling/Slicing
        if vae_tiling:
            pipe.pipe.enable_vae_slicing()
            pipe.pipe.enable_vae_tiling()
        else:
            pipe.pipe.disable_vae_slicing()
            pipe.pipe.disable_vae_tiling()

        app_state["current_pipe"] = pipe
        app_state["current_model_name"] = model_name

        if isinstance(pipe, SD3Pipeline):
            default_res, model_type = 1024, "SD3"
        elif isinstance(pipe, SDXLPipeline):
            default_res, model_type = 1024, "SDXL"
        elif isinstance(pipe, SD2Pipeline):
            default_res, model_type = 768, "SD 2.x"
        else:
            default_res, model_type = 512, "SD 1.5"

        status_suffix = "(CPU Offload)" if cpu_offload else ""
        status_message = f"Ready: {model_name} ({model_type}) {status_suffix}"

        app_state["status_message"] = status_message
        app_state["is_model_loaded"] = True

        logger.info(
            f"Model '{model_name}' is ready! Type: {model_type} {status_suffix}."
        )
        update_progress(1, "Model Ready!")

        return {
            "status_message": status_message,
            "model_type": model_type,
            "width": default_res,
            "height": default_res,
        }
    except Exception as e:
        logger.error(
            f"Failed to load model '{model_name}'. Full error: {e}", exc_info=True
        )
        # Ensure state is clean after a failed load
        app_state.update(
            {"current_pipe": None, "current_model_name": "", "is_model_loaded": False}
        )
        raise RuntimeError(
            f"Failed to load model '{model_name}'. Check logs for details."
        )


def generate_image(
    prompt,
    negative_prompt,
    steps,
    guidance,
    seed,
    width,
    height,
    progress_callback=None,
):
    """Generates an image based on the provided parameters."""
    if not app_state["is_model_loaded"]:
        raise ConnectionAbortedError("Cannot generate, no model is loaded.")

    logger.info("Starting image generation...")
    start_time = time.time()

    # Seed must be an integer
    seed = int(seed if seed is not None else random.randint(0, 2**32 - 1))
    generator = torch.Generator("xpu").manual_seed(seed)

    # Universal progress callback that the pipeline can use
    def pipeline_progress_callback(pipe, step, timestep, callback_kwargs):
        progress = step / int(steps)
        if progress_callback:
            # step is 0-indexed, so we add 1 for display
            progress_callback(progress, f"Sampling... {step + 1}/{int(steps)}")
        return callback_kwargs

    gen_kwargs = {
        "prompt": prompt,
        "num_inference_steps": int(steps),
        "guidance_scale": float(guidance),
        "width": int(width),
        "height": int(height),
        "generator": generator,
        "callback_on_step_end": pipeline_progress_callback,
    }
    # Add negative prompt only if it's not empty
    if negative_prompt and negative_prompt.strip():
        gen_kwargs["negative_prompt"] = negative_prompt

    # Generate the image
    image = app_state["current_pipe"].generate(**gen_kwargs).images[0]
    generation_time = time.time() - start_time
    logger.info(f"Generation completed in {generation_time:.2f} seconds.")

    # Save the image
    os.makedirs("./outputs", exist_ok=True)
    filename = (
        f"{time.strftime('%Y%m%d-%H%M%S')}_{app_state['current_model_name']}_{seed}.png"
    )
    filepath = os.path.join("./outputs", filename)
    image.save(filepath)

    info_text = f"Generated in {generation_time:.2f}s on '{app_state['current_model_name']}' with seed {seed}."

    return {"image_filename": filename, "info": info_text}
