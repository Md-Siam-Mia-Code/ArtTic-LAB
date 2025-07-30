# pipelines/sd15_pipeline.py
from diffusers import StableDiffusionPipeline
from .base_pipeline import ArtTicPipeline

class SD15Pipeline(ArtTicPipeline):
    def load_pipeline(self, progress):
        progress(0.2, desc="Loading StableDiffusionPipeline...")
        self.pipe = StableDiffusionPipeline.from_single_file(
            self.model_path,
            torch_dtype=self.dtype,
            use_safetensors=True,
            safety_checker=None
        )