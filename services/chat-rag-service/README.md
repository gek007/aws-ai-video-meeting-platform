# Chat RAG Service

Answers meeting questions using retrieved transcript and artifact context.

## Current Implementation

- supports tenant-aware retrieval filters
- returns grounded answer-shaped responses with citations
- uses scaffolded retrieval logic suitable for tests and service integration

## Current Limitation

Real embeddings, OpenSearch retrieval, and `Amazon Bedrock` answer generation are still pending.
