from __future__ import annotations

from shared.responses import json_response
from transcription_service.service import TranscriptionService


def lambda_handler(event: dict, _context) -> dict:
    result = TranscriptionService().transcribe(event)
    return json_response(202, {"message": "Transcript ready.", "nextEvent": result})

