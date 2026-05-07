from __future__ import annotations

import os

from shared.responses import json_response
from status_observer_service.store import AuroraStatusObserverStore, InMemoryMetadataStore
from status_observer_service.service import StatusObserverService


def lambda_handler(event: dict, _context) -> dict:
    metadata_store = _build_metadata_store()
    result = StatusObserverService(metadata_store=metadata_store).sync(event)
    return json_response(200, {"message": "Status sync processed.", "result": result})


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraStatusObserverStore()
    return InMemoryMetadataStore()
