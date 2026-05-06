from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class ServiceConfig:
    service_name: str
    environment: str
    log_level: str


def load_service_config(default_service_name: str) -> ServiceConfig:
    return ServiceConfig(
        service_name=os.getenv("SERVICE_NAME", default_service_name),
        environment=os.getenv("APP_ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

