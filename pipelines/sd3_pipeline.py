# pipelines/sd3_pipeline.py
import torch
from diffusers import StableDiffusion3Pipeline
from .base_pipeline import ArtTicPipeline
import logging

logger = logging.getLogger("arttic_lab")

# The official Hugging Face repository for the base SD3 model components
SD3_BASE_MODEL_REPO = "stabilityai/stable-diffusion-3-medium-diffusers"

class SD3Pipeline(ArtTicPipeline):
    def load_pipeline(self, progress):
        """
        Loads the SD3 pipeline. This is a special case. It loads the base
        model with all its components (text encoders, VAE) from the official
        Hugging Face repo, and then replaces the main model (transformer)
        with the weights from the local single-file checkpoint.
        """
        progress(0.2, desc="Loading base SD3 components from Hugging Face...")
        try:
            # Load the entire pipeline from the official repo. This will download
            # and cache the text encoders, VAE, etc. automatically.
            self.pipe = StableDiffusion3Pipeline.from_pretrained(
                SD3_BASE_MODEL_REPO,
                torch_dtype=self.dtype,
                use_safetensors=True,
            )
        except Exception as e:
            logger.error(f"Failed to download SD3 base model. Check internet connection. Error: {e}")
            raise RuntimeError("Could not download base SD3 components from Hugging Face.")

        progress(0.5, desc="Injecting local model weights...")
        # Now, load the UNet/Transformer weights from the user's local file
        # and replace the one in the pipeline.
        self.pipe.load_lora_weights(self.model_path)
        logger.info(f"Successfully injected weights from '{self.model_path}'")
        
        progress(0.6, desc="Moving model to XPU (ARC GPU)...")
        self.pipe.to("xpu")