# pipelines/flux_pipeline.py
import torch
import logging
from diffusers import FluxPipeline, FluxSchnellPipeline
from .base_pipeline import ArtTicPipeline

logger = logging.getLogger("arttic_lab")

# Base Hugging Face repository IDs for FLUX models.
# The pipeline will download the base architecture from here and then
# inject the weights from the user's local single-file model.
FLUX_DEV_BASE_REPO = "black-forest-labs/FLUX.1-dev-diffusers"
FLUX_SCHNELL_BASE_REPO = "black-forest-labs/FLUX.1-schnell-diffusers"


class FLUXDevPipeline(ArtTicPipeline):
    """Pipeline for the full FLUX.1 DEV model."""

    def load_pipeline(self, progress):
        progress(0.2, desc="Loading base FLUX.1 DEV components...")
        try:
            # Load the base pipeline structure, text encoders, etc.
            self.pipe = FluxPipeline.from_pretrained(
                FLUX_DEV_BASE_REPO,
                torch_dtype=self.dtype,
                use_safetensors=True,
            )
        except Exception as e:
            logger.error(
                f"Failed to download FLUX.1 DEV base model. Check internet connection. Error: {e}"
            )
            raise RuntimeError(
                "Could not download base FLUX.1 DEV components from Hugging Face."
            )

        progress(0.5, desc="Injecting local model weights...")
        # Load the user's single-file model weights into the pipeline
        self.pipe.load_lora_weights(self.model_path)
        logger.info(f"Successfully injected FLUX DEV weights from '{self.model_path}'")


class FLUXSchnellPipeline(ArtTicPipeline):
    """Pipeline for the distilled FLUX.1 Schnell model."""

    def load_pipeline(self, progress):
        progress(0.2, desc="Loading base FLUX.1 Schnell components...")
        try:
            # Load the base pipeline structure for the Schnell variant
            self.pipe = FluxSchnellPipeline.from_pretrained(
                FLUX_SCHNELL_BASE_REPO,
                torch_dtype=self.dtype,
                use_safetensors=True,
            )
        except Exception as e:
            logger.error(
                f"Failed to download FLUX.1 Schnell base model. Check internet connection. Error: {e}"
            )
            raise RuntimeError(
                "Could not download base FLUX.1 Schnell components from Hugging Face."
            )

        progress(0.5, desc="Injecting local model weights...")
        self.pipe.load_lora_weights(self.model_path)
        logger.info(
            f"Successfully injected FLUX Schnell weights from '{self.model_path}'"
        )

    def generate(self, *args, **kwargs):
        """
        Overrides the base generate method to handle FLUX Schnell's specific needs.
        FLUX Schnell is trained without a negative prompt, so we ensure it is not passed.
        """
        if "negative_prompt" in kwargs:
            logger.info(
                "FLUX Schnell does not use a negative prompt. It will be ignored."
            )
            kwargs.pop("negative_prompt")

        # Call the original generation method from the base class
        return super().generate(*args, **kwargs)
