# pipelines/__init__.py
import os
from safetensors import safe_open
from .sd15_pipeline import SD15Pipeline
from .sd2_pipeline import SD2Pipeline
from .sdxl_pipeline import SDXLPipeline
from .sd3_pipeline import SD3Pipeline
from .flux_pipeline import ArtTicFLUXPipeline
import logging

logger = logging.getLogger("arttic_lab")

MODELS_DIR = "./models"


def _is_xl(keys):
    """Checks for the second text encoder unique to SDXL."""
    return any(k.startswith("conditioner.embedders.1") for k in keys)


def _is_v2(keys):
    """Checks for a specific transformer block key present in SD 2.x."""
    return (
        "model.diffusion_model.input_blocks.8.1.transformer_blocks.0.attn2.to_k.weight"
        in keys
    )


def _is_sd3(keys):
    """Checks for the plural 'text_encoders' key, which is unique to SD3."""
    return any(k.startswith("text_encoders.") for k in keys)


def get_pipeline_for_model(model_name):
    """
    Inspects a model's tensor keys and filename to determine its architecture and
    returns the appropriate pipeline class.
    """
    model_path = os.path.join(MODELS_DIR, f"{model_name}.safetensors")
    model_name_lower = model_name.lower()

    # --- NEW ROBUST CHECK ---
    # Prioritize filename for FLUX models as it's more reliable for fine-tunes.
    if "flux" in model_name_lower:
        # Check for the more specific 'schnell' keyword first.
        if "schnell" in model_name_lower:
            logger.info(
                f"Model '{model_name}' detected as FLUX.1 Schnell based on filename."
            )
            return ArtTicFLUXPipeline(model_path, is_schnell=True)
        # Otherwise, assume it is a DEV model (the default FLUX variant).
        else:
            logger.info(
                f"Model '{model_name}' detected as FLUX.1 DEV based on filename."
            )
            return ArtTicFLUXPipeline(model_path, is_schnell=False)

    # If not a FLUX model by filename, proceed with key-based detection for others.
    try:
        with safe_open(model_path, framework="pt", device="cpu") as f:
            keys = list(f.keys())
    except Exception as e:
        logger.error(
            f"Could not inspect model '{model_name}': {e}. Assuming SD 1.5 as fallback."
        )
        return SD15Pipeline(model_path)

    if _is_sd3(keys):
        logger.info(f"Model '{model_name}' detected as SD3.")
        return SD3Pipeline(model_path)
    elif _is_xl(keys):
        logger.info(f"Model '{model_name}' detected as SDXL.")
        return SDXLPipeline(model_path)
    elif _is_v2(keys):
        logger.info(f"Model '{model_name}' detected as SD 2.x.")
        return SD2Pipeline(model_path)
    else:
        logger.info(f"Model '{model_name}' detected as SD 1.5.")
        return SD15Pipeline(model_path)
