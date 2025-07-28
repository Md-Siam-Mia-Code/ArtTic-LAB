# pipelines/sdxl_pipeline.py
from diffusers import StableDiffusionXLPipeline
from .base_pipeline import ArtTicPipeline

class SDXLPipeline(ArtTicPipeline):
    def load_pipeline(self, progress):
        progress(0.2, desc="Loading StableDiffusionXLPipeline...")
        self.pipe = StableDiffusionXLPipeline.from_single_file(
            self.model_path,
            torch_dtype=self.dtype,
            use_safetensors=True,
            variant="fp16"
        )
        progress(0.6, desc="Moving model to XPU (ARC GPU)...")
        self.pipe.to("xpu")