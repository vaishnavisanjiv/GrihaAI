import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Setup log formatting
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Setup file handler
    file_handler = RotatingFileHandler(
        "buildguard_backend.log", maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(log_formatter)

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # App logger
    logger = logging.getLogger("buildguard")
    logger.setLevel(logging.DEBUG)

    return logger

logger = setup_logging()
