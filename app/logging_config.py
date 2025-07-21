import logging
import sys

def setup_logging():
    logger = logging.getLogger("crm_sync")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(handler)
