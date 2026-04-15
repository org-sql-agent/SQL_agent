import logging
import sys


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a logger that outputs only to stdout (no file), suitable for local and cloud use.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove all previous handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger
