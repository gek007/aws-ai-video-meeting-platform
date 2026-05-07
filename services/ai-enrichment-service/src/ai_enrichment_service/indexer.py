from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Callable

from ai_enrichment_service.embedder import Embedding


@dataclass(slots=True)
class InMemoryVectorIndexer:
    """Stores embedding vectors in memory for tests and local development."""

    documents: list[dict] = field(default_factory=list)

    def index_chunks(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        chunks: list[dict],
        embeddings: list[Embedding],
    ) -> list[str]:
        embedding_by_index = {emb.chunk_index: emb for emb in embeddings}
        doc_ids = []
        for chunk in chunks:
            emb = embedding_by_index.get(chunk["chunkIndex"])
            doc_id = emb.embedding_ref if emb else chunk.get("embeddingRef", "")
            self.documents.append(
                {
                    "docId": doc_id,
                    "tenantId": tenant_id,
                    "meetingId": meeting_id,
                    "videoItemId": video_item_id,
                    "chunkIndex": chunk["chunkIndex"],
                    "chunkText": chunk["chunkText"],
                    "vector": emb.vector if emb else [],
                }
            )
            doc_ids.append(doc_id)
        return doc_ids


class OpenSearchVectorIndexer:
    """Indexes embedding vectors into Amazon OpenSearch Serverless."""

    def __init__(
        self,
        endpoint: str | None = None,
        index_name: str | None = None,
        region: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._endpoint = endpoint or os.getenv("OPENSEARCH_ENDPOINT")
        self._index_name = index_name or os.getenv("OPENSEARCH_INDEX_NAME", "transcript-chunks")
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        if not self._endpoint and client_factory is None:
            raise ValueError("OPENSEARCH_ENDPOINT is required for OpenSearchVectorIndexer.")
        self._client_factory = client_factory

    def index_chunks(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        chunks: list[dict],
        embeddings: list[Embedding],
    ) -> list[str]:
        embedding_by_index = {emb.chunk_index: emb for emb in embeddings}
        doc_ids = []
        client = self._build_client()
        for chunk in chunks:
            emb = embedding_by_index.get(chunk["chunkIndex"])
            doc_id = emb.embedding_ref if emb else chunk.get("embeddingRef", "")
            document = {
                "tenantId": tenant_id,
                "meetingId": meeting_id,
                "videoItemId": video_item_id,
                "chunkIndex": chunk["chunkIndex"],
                "chunkText": chunk["chunkText"],
                "startOffsetSeconds": chunk.get("startOffsetSeconds"),
                "endOffsetSeconds": chunk.get("endOffsetSeconds"),
                "chunkVector": emb.vector if emb else [],
            }
            client.index(
                index=self._index_name,
                id=doc_id,
                body=document,
            )
            doc_ids.append(doc_id)
        return doc_ids

    def _build_client(self):
        if self._client_factory is not None:
            return self._client_factory()

        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
        import boto3

        credentials = boto3.Session().get_credentials()
        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self._region,
            "aoss",
            session_token=credentials.token,
        )
        return OpenSearch(
            hosts=[{"host": self._endpoint, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )
