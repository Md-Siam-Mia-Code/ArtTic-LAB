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
        self.is_offloaded = False

    def load_pipeline(self, progress):
        raise NotImplementedError("Subclasses must implement load_pipeline")

    def place_on_device(self, use_cpu_offload=False):
        if not self.pipe:
            raise RuntimeError("Pipeline must be loaded before placing on device.")
        
        if use_cpu_offload:
            logger.info("Enabling Model CPU Offload for low VRAM usage.")
            self.pipe.enable_model_cpu_offload()
            self.is_offloaded = True
        else:
            logger.info("Moving model to XPU (ARC GPU) for maximum performance.")
            self.pipe.to("xpu")
            self.is_offloaded = False

    def optimize_with_ipex(self, progress):
        if self.is_optimized:
            logger.info("Model is already optimized.")
            return
        if self.is_offloaded:
            logger.warning("IPEX optimization is not available in CPU Offload mode.")
            return
        if not self.pipe:
            raise RuntimeError("Pipeline must be loaded before optimization.")
            
        progress(0.8, desc="Optimizing model with IPEX...")
        
        if hasattr(self.pipe, 'unet'):
            self.pipe.unet = ipex.optimize(self.pipe.unet.eval(), dtype=self.dtype, inplace=True)
            logger.info("U-Net optimized with IPEX.")
        elif hasattr(self.pipe, 'transformer'):
            self.pipe.transformer = ipex.optimize(self.pipe.transformer.eval(), dtype=self.dtype, inplace=True)
            logger.info("Transformer optimized with IPEX.")

        if hasattr(self.pipe, 'vae'):
            self.pipe.vae = ipex.optimize(self.pipe.vae.eval(), dtype=self.dtype, inplace=True)
            logger.info("VAE optimized with IPEX.")
            
        self.is_optimized = True

    def generate(self, *args, **kwargs):
        if not self.pipe:
            raise RuntimeError("Pipeline not loaded.")
        # Autocast is still beneficial even with offloading, as the active module is on XPU
        with torch.xpu.amp.autocast(enabled=True, dtype=self.dtype):
            return self.pipe(*args, **kwargs)