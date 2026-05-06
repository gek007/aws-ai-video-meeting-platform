from __future__ import annotations

from chat_rag_service.service import ChatRAGService
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    result = ChatRAGService().answer(
        question=event.get("question", "What was decided?"),
        meeting_id=event.get("meetingId", "mtg_unknown"),
    )
    return json_response(200, {"message": "Chat answer generated.", "result": result})

