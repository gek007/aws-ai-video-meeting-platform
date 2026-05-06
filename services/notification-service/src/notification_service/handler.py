from __future__ import annotations

from notification_service.service import NotificationService
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    result = NotificationService().notify(event)
    return json_response(200, {"message": "Notification processed.", "result": result})

