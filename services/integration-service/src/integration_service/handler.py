from __future__ import annotations

from integration_service.service import IntegrationService
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    result = IntegrationService().create_external_task(event)
    return json_response(201, {"message": "External task created.", "result": result})

