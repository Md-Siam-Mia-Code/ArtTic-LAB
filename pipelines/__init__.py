# pipelines/__init__.py
import os
from safetensors import safe_open
from .sd15_pipeline import SD15Pipeline
from .sdxl_pipeline import SDXLPipeline
import logging # Import logging

# Get our application's logger
logger = logging.getLogger("arttic_lab")

MODELS_DIR = "./models"

def _is_xl(model_name):
    model_path = os.path.join(MODELS_DIR, f"{model_name}.safetensors")
    try:
        with safe_open(model_path, framework="pt", device="cpu") as f:
            for key in f.keys():
                if key.startswith("conditioner.embedders.1"):
                    return True
    except Exception as e:
        logger.error(f"Could not inspect model '{model_name}': {e}. Assuming SD 1.5.")
        return False
    return False

def get_pipeline_for_model(model_name):
    model_path = os.path.join(MODELS_DIR, f"{model_name}.safetensors")
    if _is_xl(model_name):
        logger.info(f"Model '{model_name}' correctly detected as SDXL.")
        return SDXLPipeline(model_path)
    else:
        logger.info(f"Model '{model_name}' correctly detected as SD 1.5.")
        return SD15Pipeline(model_path)