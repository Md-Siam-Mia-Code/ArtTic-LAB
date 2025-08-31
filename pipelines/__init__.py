# pipelines/__init__.py
import os
from safetensors import safe_open
from .sd15_pipeline import SD15Pipeline
from .sd2_pipeline import SD2Pipeline
from .sdxl_pipeline import SDXLPipeline
from .sd3_pipeline import SD3Pipeline
from .flux_pipeline import (
    FLUXDevPipeline,
    FLUXSchnellPipeline,
)  # NEW: Import FLUX pipelines
import logging

logger = logging.getLogger("arttic_lab")

MODELS_DIR = "./models"


def _is_xl(keys):
    return any(k.startswith("conditioner.embedders.1") for k in keys)


def _is_v2(keys):
    return (
        "model.diffusion_model.input_blocks.8.1.transformer_blocks.0.attn2.to_k.weight"
        in keys
    )


def _is_sd3(keys):
    # SD3 also uses a transformer, but we can differentiate it from FLUX.
    # We check for SD3-specific text encoder keys.
    return any(k.startswith("text_encoders.2.transformer.") for k in keys)


# NEW: Detection function for FLUX models
def _is_flux(keys):
    # FLUX models have a very distinct key structure for their main transformer.
    # 'transformer.pos_embed.proj.weight' is a reliable identifier.
    return "transformer.pos_embed.proj.weight" in keys


# NEW: Detection function for the larger FLUX DEV model
def _is_flux_dev(keys):
    # The DEV model has more transformer levels than Schnell. Level 23 is a safe check.
    return any(k.startswith("transformer.levels.23.") for k in keys)


def get_pipeline_for_model(model_name):
    model_path = os.path.join(MODELS_DIR, f"{model_name}.safetensors")
    try:
        with safe_open(model_path, framework="pt", device="cpu") as f:
            keys = list(f.keys())
    except Exception as e:
        logger.error(
            f"Could not inspect model '{model_name}': {e}. Assuming SD 1.5 as fallback."
        )
        return SD15Pipeline(model_path)

    # NEW: Prioritize FLUX detection as it's the most distinct architecture
    if _is_flux(keys):
        if _is_flux_dev(keys):
            logger.info(f"Model '{model_name}' detected as FLUX.1 DEV.")
            return FLUXDevPipeline(model_path)
        else:
            logger.info(f"Model '{model_name}' detected as FLUX.1 Schnell.")
            return FLUXSchnellPipeline(model_path)

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
