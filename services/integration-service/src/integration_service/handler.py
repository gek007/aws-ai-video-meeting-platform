from __future__ import annotations

import os

from integration_service.service import IntegrationService
from integration_service.store import AuroraIntegrationStore, InMemoryMetadataStore
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    metadata_store = _build_metadata_store()
    result = IntegrationService(metadata_store=metadata_store).create_external_task(event)
    return json_response(201, {"message": "External task created.", "result": result})


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraIntegrationStore()
    return InMemoryMetadataStore()
