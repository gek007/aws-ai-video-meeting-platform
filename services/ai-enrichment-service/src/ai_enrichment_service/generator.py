from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class EnrichmentOutput:
    summary: str
    topics: list[str]
    decisions: list[dict]
    action_items: list[dict]
    model_id: str


class DeterministicEnrichmentGenerator:
    def generate(self, *, transcript_text: str) -> EnrichmentOutput:
        del transcript_text
        return EnrichmentOutput(
            summary="Meeting summary placeholder.",
            topics=["authentication", "reliability"],
            decisions=[{"description": "Prioritize timeout fix", "owner": "owner@example.com"}],
            action_items=[
                {
                    "title": "Fix login timeout issue",
                    "description": "Investigate and resolve intermittent login timeout failures.",
                    "item_type": "bug",
                    "owner_email": "owner@example.com",
                    "priority": "high",
                }
            ],
            model_id="deterministic-placeholder",
        )


class BedrockEnrichmentGenerator:
    def __init__(
        self,
        model_id: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._model_id = model_id or os.getenv("BEDROCK_MODEL_ID")
        if not self._model_id:
            raise ValueError("BEDROCK_MODEL_ID is required for BedrockEnrichmentGenerator.")
        self._client_factory = client_factory

    def generate(self, *, transcript_text: str) -> EnrichmentOutput:
        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(self._request_body(transcript_text)),
        )
        payload = json.loads(response["body"].read())
        text = payload["content"][0]["text"]
        structured = json.loads(text)
        return EnrichmentOutput(
            summary=structured["summary"],
            topics=structured.get("topics", []),
            decisions=structured.get("decisions", []),
            action_items=structured.get("actionItems", structured.get("action_items", [])),
            model_id=self._model_id,
        )

    def _request_body(self, transcript_text: str) -> dict:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self._prompt(transcript_text),
                        }
                    ],
                }
            ],
        }

    def _prompt(self, transcript_text: str) -> str:
        return (
            "Extract meeting intelligence from the transcript. "
            "Return only valid JSON with keys summary, topics, decisions, and actionItems. "
            "Each action item must include title, description, item_type, owner_email, and priority when known.\n\n"
            f"Transcript:\n{transcript_text}"
        )

    @property
    def _client(self):
        if self._client_factory is not None:
            return self._client_factory()

        import boto3

        return boto3.client("bedrock-runtime")
