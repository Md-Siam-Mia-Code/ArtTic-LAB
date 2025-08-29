# helpers/cli_manager.py
import logging
import sys

APP_LOGGER_NAME = "arttic_lab"
APP_VERSION = "1.5.0"  # Version bump for new UI


class ArtTicFilter(logging.Filter):
    def filter(self, record):
        return record.name.startswith(APP_LOGGER_NAME) or record.name == "py.warnings"


class CustomFormatter(logging.Formatter):
    # New color theme based on Teal/Cyan
    TEAL_DARK = "\x1b[38;2;13;148;136m"  # #0D9488
    TEAL_MID = "\x1b[38;2;20;184;166m"  # #14B8A6
    CYAN_BRIGHT = "\x1b[38;2;103;232;249m"  # #67E8F9
    RESET = "\x1b[0m"

    # All formats now use the new TEAL_MID color
    FORMATS = {
        logging.INFO: f"{TEAL_MID}[ArtTic-LAB] >{RESET} %(message)s",
        logging.WARNING: f"{TEAL_MID}[ArtTic-LAB] [WARN] >{RESET} %(message)s (%(pathname)s:%(lineno)d)",
        logging.ERROR: f"{TEAL_MID}[ArtTic-LAB] [ERROR] >{RESET} %(message)s",
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

    # ASCII art banner with a simulated gradient effect
    art = f"""
    {CustomFormatter.CYAN_BRIGHT}     █████╗ ██████╗ ████████╗ ████████╗██╗ ██████╗          ██╗      █████╗ ██████╗ 
    {CustomFormatter.TEAL_MID}    ██╔══██╗██╔══██╗╚══██╔══╝ ╚══██╔══╝██║██╔════╝          ██║     ██╔══██╗██╔══██╗
    {CustomFormatter.TEAL_MID}    ███████║██████╔╝   ██║       ██║   ██║██║       ██████  ██║     ███████║██████╔╝
    {CustomFormatter.TEAL_DARK}    ██╔══██║██╔══██╗   ██║       ██║   ██║██║               ██║     ██╔══██║██╔══██╗
    {CustomFormatter.TEAL_DARK}    ██║  ██║██║  ██║   ██║       ██║   ██║╚██████╗          ███████╗██║  ██║██████╔╝
    {CustomFormatter.TEAL_DARK}    ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝       ╚═╝   ╚═╝ ╚═════╝          ╚══════╝╚═╝  ╚═╝╚═════╝ 
    {CustomFormatter.RESET}
    """
    print(art)

    logger.info(f"Welcome to ArtTic-LAB v{APP_VERSION}!")
    logger.info("A modern, clean, and powerful UI for Intel ARC GPUs.")
    logger.info("-" * 60)
    logger.info("System Information:")

    py_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    logger.info(
        f"  Python: {py_version}, Torch: {torch.__version__}, IPEX: {ipex.__version__}, Diffusers: {diffusers.__version__}"
    )

    if torch.xpu.is_available():
        gpu_name = torch.xpu.get_device_name(0)
        # GPU name now uses the bright cyan color
        logger.info(
            f"  Intel GPU: {CustomFormatter.CYAN_BRIGHT}{gpu_name}{CustomFormatter.RESET} (Detected)"
        )
    else:
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
        py_warnings_logger = logging.getLogger("py.warnings")
        handler.addFilter(ArtTicFilter())
        py_warnings_logger.addHandler(handler)
        logging.getLogger().addHandler(logging.NullHandler())
        logging.getLogger().setLevel(logging.ERROR)

    app_logger.addHandler(handler)
