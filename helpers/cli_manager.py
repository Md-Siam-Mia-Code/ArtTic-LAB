# helpers/cli_manager.py
import logging
import sys

APP_LOGGER_NAME = "arttic_lab"
APP_VERSION = "1.0.0" # Official Release

class ArtTicFilter(logging.Filter):
    def filter(self, record):
        return record.name.startswith(APP_LOGGER_NAME) or record.name == 'py.warnings'

class CustomFormatter(logging.Formatter):
    # The only color we'll use now, besides reset.
    BLUEVIOLET = "\x1b[38;2;138;43;226m" # Truecolor for blueviolet
    RESET = "\x1b[0m"

    # All formats now use BLUEVIOLET
    FORMATS = {
        logging.INFO: f"{BLUEVIOLET}[ArtTic-LAB] >{RESET} %(message)s",
        logging.WARNING: f"{BLUEVIOLET}[ArtTic-LAB] [WARN] >{RESET} %(message)s (%(pathname)s:%(lineno)d)",
        logging.ERROR: f"{BLUEVIOLET}[ArtTic-LAB] [ERROR] >{RESET} %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self._fmt)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def log_system_info():
    import torch
    import intel_extension_for_pytorch as ipex
    import diffusers

    logger = logging.getLogger(APP_LOGGER_NAME)
    
    # The ASCII art banner
    art = f"""
    {CustomFormatter.BLUEVIOLET}
     █████╗ ██████╗ ████████╗ ████████╗██╗ ██████╗          ██╗      █████╗ ██████╗ 
    ██╔══██╗██╔══██╗╚══██╔══╝ ╚══██╔══╝██║██╔════╝          ██║     ██╔══██╗██╔══██╗
    ███████║██████╔╝   ██║       ██║   ██║██║       ██████  ██║     ███████║██████╔╝
    ██╔══██║██╔══██╗   ██║       ██║   ██║██║               ██║     ██╔══██║██╔══██╗
    ██║  ██║██║  ██║   ██║       ██║   ██║╚██████╗          ███████╗██║  ██║██████╔╝
    ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝       ╚═╝   ╚═╝ ╚═════╝          ╚══════╝╚═╝  ╚═╝╚═════╝ 
    {CustomFormatter.RESET}
    """
    print(art)
    
    logger.info(f"Welcome to ArtTic-LAB v{APP_VERSION}!")
    logger.info("A modern, clean, and powerful UI for Intel ARC GPUs.")
    logger.info("-" * 60)
    logger.info("System Information:")
    
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    logger.info(f"  Python: {py_version}, Torch: {torch.__version__}, IPEX: {ipex.__version__}, Diffusers: {diffusers.__version__}")
    
    if torch.xpu.is_available():
        gpu_name = torch.xpu.get_device_name(0)
        # GPU name is now also in BLUEVIOLET
        logger.info(f"  Intel GPU: {CustomFormatter.BLUEVIOLET}{gpu_name}{CustomFormatter.RESET} (Detected)")
    else:
        # Errors will also be in BLUEVIOLET as per the formatter
        logger.error("  Intel GPU: Not Detected! The application may not work.")
    
    logger.info("-" * 60)

def setup_logging(disable_filters=False):
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    if app_logger.hasHandlers():
        app_logger.handlers.clear()

    if not disable_filters:
        logging.captureWarnings(True)
        py_warnings_logger = logging.getLogger('py.warnings')
        handler.addFilter(ArtTicFilter())
        py_warnings_logger.addHandler(handler)
        logging.getLogger().addHandler(logging.NullHandler())
        logging.getLogger().setLevel(logging.ERROR)
        
    app_logger.addHandler(handler)