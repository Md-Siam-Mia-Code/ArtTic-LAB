# app.py
import argparse
import logging
import sys
import os
import contextlib
import signal
import random
import torch
from helpers.cli_manager import setup_logging, log_system_info, APP_LOGGER_NAME
from core.logic import SCHEDULER_MAP, get_available_models, get_output_images

# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="ArtTic-LAB: A clean UI for Intel ARC GPUs."
)
parser.add_argument(
    "--disable-filters", action="store_true", help="Disable custom log filters."
)
parser.add_argument(
    "--ui",
    type=str,
    default="custom",
    choices=["custom", "gradio"],
    help="Specify which user interface to launch.",
)
parser.add_argument(
    "--host", type=str, default="127.0.0.1", help="Host address to bind the server to."
)
parser.add_argument("--port", type=int, default=7860, help="Port to run the server on.")
parser.add_argument(
    "--share",
    action="store_true",
    help="Enable Gradio sharing (only works with --ui gradio).",
)

args = parser.parse_args()

# --- Initial Setup ---
setup_logging(disable_filters=args.disable_filters)
logger = logging.getLogger(APP_LOGGER_NAME)


# --- Graceful Shutdown ---
def signal_handler(sig, frame):
    print("\n")
    logger.info("Ctrl+C detected. Shutting down ArtTic-LAB gracefully...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# --- Gradio UI Launcher ---
def launch_gradio():
    """Initializes and launches the Gradio user interface."""
    import gradio as gr
    from ui import create_ui
    from core import logic as core

    logger.info("Launching Gradio UI...")

    # Wrapper functions (handlers) that adapt core logic for Gradio
    def load_model_handler_gr(
        model_name, scheduler_name, vae_tiling, cpu_offload, progress=gr.Progress()
    ):
        try:
            result = core.load_model(
                model_name,
                scheduler_name,
                vae_tiling,
                cpu_offload,
                progress_callback=lambda p, d: progress(p, desc=d),
            )
            return (
                result["status_message"],
                gr.Slider(value=result["width"]),
                gr.Slider(value=result["height"]),
            )
        except Exception as e:
            raise gr.Error(str(e))

    def generate_image_handler_gr(
        prompt,
        negative_prompt,
        steps,
        guidance,
        seed,
        width,
        height,
        progress=gr.Progress(),
    ):
        if not core.app_state["is_model_loaded"]:
            raise gr.Error("No model is loaded.")
        try:
            result = core.generate_image(
                prompt,
                negative_prompt,
                steps,
                guidance,
                seed,
                width,
                height,
                progress_callback=lambda p, d: progress(p, desc=d),
            )
            # Gradio's gr.Image needs a file path or PIL image
            image_path = os.path.join("./outputs", result["image_filename"])
            return image_path, result["info"]
        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise gr.Error(str(e))

    def refresh_models_handler_gr():
        logger.info("Refreshing model list...")
        return gr.Dropdown(choices=core.get_available_models())

    def unload_model_handler_gr():
        result = core.unload_model()
        return result["status_message"]

    def swap_dimensions_handler_gr(w, h):
        return h, w

    def randomize_seed_handler_gr():
        return random.randint(0, 2**32 - 1)

    # Gradio doesn't need a VAE tiling handler, it's passed at load time.
    # We pass a dummy lambda to prevent errors.
    handlers = {
        "load_model": load_model_handler_gr,
        "generate_image": generate_image_handler_gr,
        "get_gallery": lambda: [
            os.path.join("./outputs", f) for f in core.get_output_images()
        ],
        "refresh_models": refresh_models_handler_gr,
        "randomize_seed": randomize_seed_handler_gr,
        "swap_dims": swap_dimensions_handler_gr,
        "unload_model": unload_model_handler_gr,
        "toggle_vae_tiling": lambda: None,
    }

    app = create_ui(get_available_models(), list(SCHEDULER_MAP.keys()), handlers)
    logger.info("UI is ready. Launching Gradio server...")
    logger.info(
        "Access ArtTic-LAB via the URLs below. Press Ctrl+C in this terminal to shutdown."
    )
    app.launch(server_name=args.host, server_port=args.port, share=args.share)


# --- Custom Web UI Launcher ---
def launch_web_ui():
    """Initializes and launches the custom FastAPI web interface."""
    try:
        import uvicorn
        from web.server import app as fastapi_app
    except ImportError:
        logger.error("Required packages for the custom UI are not installed.")
        logger.error("Please run the installer (install.bat or install.sh) again.")
        sys.exit(1)

    logger.info("Launching custom web UI...")
    logger.info(f"Access ArtTic-LAB at http://{args.host}:{args.port}")
    logger.info("Press Ctrl+C in this terminal to shutdown.")

    config = uvicorn.Config(
        fastapi_app, host=args.host, port=args.port, log_level="warning"
    )
    server = uvicorn.Server(config)
    server.run()


# --- Main Execution ---
if __name__ == "__main__":
    if not args.disable_filters:
        os.system("cls" if os.name == "nt" else "clear")

    # Log system info once at the start
    log_system_info()

    # Launch the selected UI
    if args.ui == "gradio":
        launch_gradio()
    else:  # Default to custom
        launch_web_ui()
