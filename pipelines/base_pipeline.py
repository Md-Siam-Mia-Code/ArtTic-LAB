# pipelines/base_pipeline.py
import torch
import intel_extension_for_pytorch as ipex
import logging

logger = logging.getLogger("arttic_lab")

class ArtTicPipeline:
    def __init__(self, model_path, dtype=torch.bfloat16):
        if not torch.xpu.is_available():
            raise RuntimeError("Intel ARC GPU (XPU) not detected.")
        self.pipe = None
        self.model_path = model_path
        self.dtype = dtype
        self.is_optimized = False

    def load_pipeline(self, progress):
        raise NotImplementedError("Subclasses must implement load_pipeline")

    def optimize_with_ipex(self, progress):
        if self.is_optimized:
            logger.info("Model is already optimized.")
            return
        if not self.pipe:
            raise RuntimeError("Pipeline must be loaded before optimization.")
            
        progress(0.8, desc="Optimizing model with IPEX...")
        
        # Optimize main model (U-Net for SD1/2/XL, Transformer for SD3)
        if hasattr(self.pipe, 'unet'):
            self.pipe.unet = ipex.optimize(self.pipe.unet.eval(), dtype=self.dtype, inplace=True)
            logger.info("U-Net optimized with IPEX.")
        elif hasattr(self.pipe, 'transformer'):
            self.pipe.transformer = ipex.optimize(self.pipe.transformer.eval(), dtype=self.dtype, inplace=True)
            logger.info("Transformer optimized with IPEX.")

        # Optimize VAE
        if hasattr(self.pipe, 'vae'):
            self.pipe.vae = ipex.optimize(self.pipe.vae.eval(), dtype=self.dtype, inplace=True)
            logger.info("VAE optimized with IPEX.")
            
        self.is_optimized = True

    def generate(self, *args, **kwargs):
        if not self.pipe:
            raise RuntimeError("Pipeline not loaded.")
        with torch.xpu.amp.autocast(enabled=True, dtype=self.dtype):
            return self.pipe(*args, **kwargs)