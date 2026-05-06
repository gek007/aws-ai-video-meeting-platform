from __future__ import annotations

import json
import logging


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_json(logger: logging.Logger, **payload) -> None:
    logger.info(json.dumps(payload, sort_keys=True))

