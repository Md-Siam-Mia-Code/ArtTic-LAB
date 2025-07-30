# pipelines/sd2_pipeline.py
from diffusers import StableDiffusionPipeline
from .base_pipeline import ArtTicPipeline

class SD2Pipeline(ArtTicPipeline):
    def load_pipeline(self, progress):
        progress(0.2, desc="Loading StableDiffusionPipeline (v2)...")
        self.pipe = StableDiffusionPipeline.from_single_file(
            self.model_path,
            torch_dtype=self.dtype,
            use_safetensors=True,
            safety_checker=None
        )