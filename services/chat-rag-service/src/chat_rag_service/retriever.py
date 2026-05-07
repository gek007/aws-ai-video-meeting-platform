from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    meeting_id: str
    video_item_id: str
    chunk_text: str
    score: float
    start_offset_seconds: float | None = None
    end_offset_seconds: float | None = None


@dataclass(slots=True)
class InMemoryRetriever:
    """Returns deterministic chunks from an in-memory store for tests."""

    chunks: list[dict] = field(default_factory=list)

    def retrieve(
        self,
        *,
        question: str,
        meeting_id: str,
        tenant_id: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        matches = [c for c in self.chunks if c.get("meetingId") == meeting_id and c.get("tenantId") == tenant_id]
        return [
            RetrievedChunk(
                chunk_id=c.get("chunkId", f"chunk_{i}"),
                meeting_id=c["meetingId"],
                video_item_id=c.get("videoItemId", "vid_unknown"),
                chunk_text=c.get("chunkText", ""),
                score=c.get("score", 0.9),
                start_offset_seconds=c.get("startOffsetSeconds"),
                end_offset_seconds=c.get("endOffsetSeconds"),
            )
            for i, c in enumerate(matches[:top_k])
        ]


class OpenSearchRetriever:
    """Retrieves transcript chunks using vector similarity from OpenSearch Serverless."""

    def __init__(
        self,
        endpoint: str | None = None,
        index_name: str | None = None,
        region: str | None = None,
        embedding_client_factory: Callable[[], object] | None = None,
        search_client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._endpoint = endpoint or os.getenv("OPENSEARCH_ENDPOINT")
        self._index_name = index_name or os.getenv("OPENSEARCH_INDEX_NAME", "transcript-chunks")
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        self._embedding_model = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v1")
        if not self._endpoint and search_client_factory is None:
            raise ValueError("OPENSEARCH_ENDPOINT is required for OpenSearchRetriever.")
        self._embedding_client_factory = embedding_client_factory
        self._search_client_factory = search_client_factory

    def retrieve(
        self,
        *,
        question: str,
        meeting_id: str,
        tenant_id: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        vector = self._embed(question)
        hits = self._search(vector=vector, meeting_id=meeting_id, tenant_id=tenant_id, top_k=top_k)
        return [
            RetrievedChunk(
                chunk_id=hit["_id"],
                meeting_id=hit["_source"].get("meetingId", meeting_id),
                video_item_id=hit["_source"].get("videoItemId", ""),
                chunk_text=hit["_source"].get("chunkText", ""),
                score=hit.get("_score", 0.0),
                start_offset_seconds=hit["_source"].get("startOffsetSeconds"),
                end_offset_seconds=hit["_source"].get("endOffsetSeconds"),
            )
            for hit in hits
        ]

    def _embed(self, text: str) -> list[float]:
        import json
        client = self._embedding_client_factory() if self._embedding_client_factory else self._bedrock_client()
        response = client.invoke_model(
            modelId=self._embedding_model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"inputText": text}),
        )
        return json.loads(response["body"].read())["embedding"]

    def _search(self, *, vector: list[float], meeting_id: str, tenant_id: str, top_k: int) -> list[dict]:
        client = self._search_client_factory() if self._search_client_factory else self._opensearch_client()
        query = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {"knn": {"chunkVector": {"vector": vector, "k": top_k}}},
                    ],
                    "filter": [
                        {"term": {"meetingId": meeting_id}},
                        {"term": {"tenantId": tenant_id}},
                    ],
                }
            },
        }
        result = client.search(index=self._index_name, body=query)
        return result["hits"]["hits"]

    def _bedrock_client(self):
        import boto3
        return boto3.client("bedrock-runtime")

    def _opensearch_client(self):
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
        import boto3
        credentials = boto3.Session().get_credentials()
        auth = AWS4Auth(
            credentials.access_key, credentials.secret_key,
            self._region, "aoss", session_token=credentials.token,
        )
        return OpenSearch(
            hosts=[{"host": self._endpoint, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )
