from __future__ import annotations

from shared.responses import json_response
from status_observer_service.service import StatusObserverService


def lambda_handler(event: dict, _context) -> dict:
    result = StatusObserverService().sync(event)
    return json_response(200, {"message": "Status sync processed.", "result": result})

