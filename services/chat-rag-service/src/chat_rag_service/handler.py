from __future__ import annotations

import os

from chat_rag_service.answerer import BedrockAnswerer, InMemoryAnswerer
from chat_rag_service.retriever import InMemoryRetriever, OpenSearchRetriever
from chat_rag_service.service import ChatRAGService
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    retriever = _build_retriever()
    answerer = _build_answerer()
    result = ChatRAGService(retriever=retriever, answerer=answerer).answer(
        question=event.get("question", "What was decided?"),
        meeting_id=event.get("meetingId", "mtg_unknown"),
        tenant_id=event.get("tenantId", "tenant_demo"),
    )
    return json_response(200, {"message": "Chat answer generated.", "result": result})


def _build_retriever():
    if os.getenv("OPENSEARCH_ENDPOINT"):
        return OpenSearchRetriever()
    return InMemoryRetriever()


def _build_answerer():
    if os.getenv("BEDROCK_MODEL_ID"):
        return BedrockAnswerer()
    return InMemoryAnswerer()
