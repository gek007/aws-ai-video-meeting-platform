from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True, slots=True)
class Embedding:
    chunk_index: int
    vector: list[float]
    embedding_ref: str


class InMemoryEmbeddingGenerator:
    """Deterministic embedding generator for tests. Returns sequential mock vectors."""

    def generate_batch(self, chunks: list[dict]) -> list[Embedding]:
        embeddings = []
        for chunk in chunks:
            idx = chunk["chunkIndex"]
            vector = [float(idx) / 100.0] * 10
            embeddings.append(
                Embedding(
                    chunk_index=idx,
                    vector=vector,
                    embedding_ref=f"emb_inmemory_{idx:03d}",
                )
            )
        return embeddings


class BedrockEmbeddingGenerator:
    """Generates embeddings using Amazon Bedrock Titan or Cohere embedding models."""

    DEFAULT_MODEL = "amazon.titan-embed-text-v1"

    def __init__(
        self,
        model_id: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._model_id = model_id or os.getenv("BEDROCK_EMBEDDING_MODEL_ID", self.DEFAULT_MODEL)
        self._client_factory = client_factory

    def generate_batch(self, chunks: list[dict]) -> list[Embedding]:
        embeddings = []
        for chunk in chunks:
            vector = self._embed_text(chunk["chunkText"])
            embeddings.append(
                Embedding(
                    chunk_index=chunk["chunkIndex"],
                    vector=vector,
                    embedding_ref=f"emb_bedrock_{chunk['chunkIndex']:03d}",
                )
            )
        return embeddings

    def _embed_text(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text})
        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        payload = json.loads(response["body"].read())
        return payload["embedding"]

    @property
    def _client(self):
        if self._client_factory is not None:
            return self._client_factory()
        import boto3
        return boto3.client("bedrock-runtime")
