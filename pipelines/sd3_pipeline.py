# pipelines/sd3_pipeline.py
import torch
from diffusers import StableDiffusion3Pipeline
from .base_pipeline import ArtTicPipeline
import logging

logger = logging.getLogger("arttic_lab")

SD3_BASE_MODEL_REPO = "stabilityai/stable-diffusion-3-medium-diffusers"

class SD3Pipeline(ArtTicPipeline):
    def load_pipeline(self, progress):
        progress(0.2, desc="Loading base SD3 components from Hugging Face...")
        try:
            self.pipe = StableDiffusion3Pipeline.from_pretrained(
                SD3_BASE_MODEL_REPO,
                torch_dtype=self.dtype,
                use_safetensors=True,
            )
        except Exception as e:
            logger.error(f"Failed to download SD3 base model. Check internet connection. Error: {e}")
            raise RuntimeError("Could not download base SD3 components from Hugging Face.")

        progress(0.5, desc="Injecting local model weights...")
        self.pipe.load_lora_weights(self.model_path)
        logger.info(f"Successfully injected weights from '{self.model_path}'")