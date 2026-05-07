import json

from ai_enrichment_service.generator import BedrockEnrichmentGenerator, DeterministicEnrichmentGenerator


class StubBody:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self):
        return json.dumps(self._payload)


class StubBedrockClient:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def invoke_model(self, **kwargs):
        self.requests.append(kwargs)
        return {
            "body": StubBody(
                {
                    "content": [
                        {
                            "text": json.dumps(
                                {
                                    "summary": "Summary from Bedrock.",
                                    "topics": ["authentication"],
                                    "decisions": [{"description": "Fix timeout first", "owner": "owner@example.com"}],
                                    "actionItems": [
                                        {
                                            "title": "Fix timeout",
                                            "description": "Investigate timeout.",
                                            "type": "bug",
                                            "owner": "owner@example.com",
                                            "priority": "high",
                                        }
                                    ],
                                }
                            )
                        }
                    ]
                }
            )
        }


def test_deterministic_generator_returns_placeholder_output():
    output = DeterministicEnrichmentGenerator().generate(transcript_text="hello")

    assert output.summary == "Meeting summary placeholder."
    assert output.action_items[0]["item_type"] == "bug"


def test_bedrock_generator_invokes_model_and_parses_structured_json():
    client = StubBedrockClient()
    output = BedrockEnrichmentGenerator(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        client_factory=lambda: client,
    ).generate(transcript_text="Discuss login timeout.")

    request = client.requests[0]
    assert request["modelId"] == "anthropic.claude-3-haiku-20240307-v1:0"
    assert request["contentType"] == "application/json"
    assert output.summary == "Summary from Bedrock."
    assert output.action_items[0]["title"] == "Fix timeout"
