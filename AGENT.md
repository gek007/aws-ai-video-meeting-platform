# AI Meeting Intelligence Platform Summary

## Project Goal

Build an AWS-native AI Meeting Intelligence Platform that processes meeting recordings, converts them into structured knowledge, creates actionable items in external systems, notifies participants, tracks task status, and supports chat-based Q&A over meeting content using RAG.

## Current Implementation Snapshot

The repository contains a working Python Lambda-first implementation with 160 passing tests and real adapters throughout.

Implemented in code:

- real Aurora persistence for all 7 backend services plus `AuroraBaseStore` shared base class
- real SQS publishers for: `ingestion → media-processing`, `media → transcription`, `transcription → ai-enrichment`
- real SNS publisher for: `ai-enrichment → meeting-intelligence-topic`
- real AWS adapters:
  - `transcription-service → Amazon Transcribe` (submit + completion callback)
  - `notification-service → Amazon SES` email sender
  - `notification-service → Slack webhook` (`SlackWebhookSender`)
  - `ai-enrichment-service → Amazon Bedrock` LLM calls
  - `ai-enrichment-service → Amazon Bedrock` embedding generation (`BedrockEmbeddingGenerator`)
  - `ai-enrichment-service → OpenSearch Serverless` vector indexing (`OpenSearchVectorIndexer`)
  - `media-service → AWS MediaConvert` with `UserMetadata` propagation (`MediaConvertAdapter`)
  - `media-service → FFmpeg` subprocess conversion (`FFmpegSubprocessConverter`)
  - `apps/api → S3` pre-signed PUT URL uploads (`S3PresignedUploader`)
  - `status-observer-service → Jira` status polling (`JiraStatusPoller`)
  - `status-observer-service → GitHub` status polling (`GitHubStatusPoller`)
- `search-query-service` with keyword search and topic-overlap related-meetings scoring
- `chat-rag-service` with Retriever+Answerer protocol pattern, citations, and confidence levels
- duplicate-prevention idempotency in `integration-service` (unique on action_item_id + provider + project_key)
- `task.status.changed` vs `task.status.synced` event distinction in `status-observer-service`

Still planned:

- scheduled `EventBridge Scheduler` wiring for status polling
- `SNS → SQS` subscription wiring for task-creation and notification consumers in AWS infrastructure
- real frontend

## Core Product Capabilities

- ingest meeting video from upload or external connector
- extract audio and transcribe speech
- generate summaries, topics, decisions, and action items
- classify action items as `bug`, `feature`, or `todo`
- discover related meetings using topic overlap (in-memory) or vector search (OpenSearch)
- create external tasks in systems such as `Jira` and `GitHub Issues` with duplicate prevention
- notify participants via email (SES) or Slack webhook
- observe external task status changes and distinguish first-sync from actual changes
- support meeting chat with grounded answers, citations, and confidence
- pre-signed S3 upload with tenant/meeting/video metadata in object metadata

## AWS-Native Architecture

The platform uses a hybrid `SNS + SQS + Lambda` event-driven model.

- `S3` — raw videos, audio, transcripts, and derived artifacts; pre-signed PUT upload flow
- `EventBridge` — captures S3 upload events and MediaConvert job completion events
- `SQS` — sequential stage-by-stage processing with retry and DLQ support
- `SNS` — broadcasts `meeting.intelligence.generated` to multiple independent consumers
- `Lambda` — all service logic
- `Bedrock` — LLM enrichment + embedding generation
- `Aurora PostgreSQL` — all transactional metadata via `AuroraBaseStore`
- `OpenSearch Serverless` — vector indexing and retrieval (optional; falls back to in-memory)
- `Transcribe` — speech-to-text
- `SES` / Slack webhooks — notifications
- `MediaConvert` / `FFmpeg` — video-to-audio conversion

## End-to-End Flow

1. Client calls `POST /upload/init` → API returns a pre-signed S3 PUT URL with `tenantId/meetingId/videoItemId` in S3 object metadata.
2. Client PUTs video directly to S3.
3. `EventBridge` detects the new object and triggers `ingestion-service`.
4. Ingestion persists `meeting`, `video_item`, `processing_job` in Aurora; sends `media.processing.requested` to `SQS: media-processing`.
5. `media-service` converts video to audio (in-memory / FFmpeg / MediaConvert). For MediaConvert: stores IDs in `UserMetadata`, returns `media.conversion.job.started`. EventBridge delivers the completion event back to `media-service`, which continues the pipeline.
6. `media-service` persists audio artifact, sends `transcription.requested` to `SQS: transcription`.
7. `transcription-service` submits audio to Transcribe; handles completion callback; persists transcript; sends `meeting.transcript.ready` to `SQS: ai-enrichment`.
8. `ai-enrichment-service` chunks transcript, calls Bedrock, persists all artifacts, generates and indexes embeddings, publishes `meeting.intelligence.generated` to `SNS`.
9. `SNS` fans out to `SQS: task-creation` and `SQS: notifications`.
10. `integration-service` creates external tasks (Jira/GitHub) with idempotency guard.
11. `notification-service` delivers email (SES) or Slack webhook notification.
12. `status-observer-service` polls external providers and persists status changes.
13. Chat queries route through `chat-rag-service`: retrieves chunks from OpenSearch or in-memory fallback, answers via Bedrock or in-memory, returns citations.
14. Search queries route through `search-query-service`: keyword ILIKE or topic-overlap scoring.

## Canonical Eventing Pattern

- `SQS → Lambda` for strict processing stages: media → transcription → AI enrichment
- `SNS → SQS → Lambda` for fan-out: meeting intelligence generated, task status changed, processing failed

## Key Design Decisions

- **`AuroraBaseStore`** — shared base class in `libs/shared/src/shared/aurora.py`; lazy psycopg import; context-manager `_connect()` with optional `connection_factory` for tests
- **`UserMetadata` propagation** — `MediaConvertAdapter` stores `tenantId/meetingId/videoItemId` in job `UserMetadata`; completion handler reads from `detail.userMetadata`
- **Retriever + Answerer protocols** — `chat-rag-service` uses DI so OpenSearch and Bedrock can be swapped for in-memory fallbacks
- **Idempotency key** — `(action_item_id, provider, provider_project_key)` for external tasks
- **Status event semantics** — `task.status.changed` = prior record existed and status differs; `task.status.synced` = first observation

## Major Services

- `ingestion-service` — validates uploads, creates core records, starts processing
- `media-service` — video-to-audio conversion (sync or async), EventBridge completion callback
- `transcription-service` — Transcribe submission + completion handling
- `ai-enrichment-service` — LLM enrichment, embedding generation, vector indexing
- `task-orchestrator-service` — converts action items into integration-ready work
- `integration-service` — Jira/GitHub connector with duplicate prevention
- `notification-service` — SES email, Slack webhook, composite routing
- `status-observer-service` — external status polling and change detection
- `search-query-service` — keyword and topic-overlap search, Aurora-backed
- `chat-rag-service` — RAG with citations and confidence

## Repository Structure

```
.
├── AGENT.md
├── AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md
├── FLOW.md
├── TODO.md
├── README.md
├── apps/
│   ├── api/
│   └── web/
├── services/
│   ├── ingestion-service/
│   ├── media-service/
│   ├── transcription-service/
│   ├── ai-enrichment-service/
│   ├── task-orchestrator-service/
│   ├── integration-service/
│   ├── notification-service/
│   ├── status-observer-service/
│   ├── search-query-service/
│   └── chat-rag-service/
├── libs/
│   ├── contracts/
│   ├── shared/
│   ├── observability/
│   └── connectors/
├── infra/
│   └── terraform/
├── database/
│   ├── migrations/
│   └── seeds/
└── tests/
```

## Database Summary

`Aurora PostgreSQL` is the system of record for all transactional metadata.

Core implemented persistence:

- `meetings`, `video_items`, `processing_jobs`
- `transcripts`, `transcript_chunks`
- `summaries`, `topics`, `decisions`, `action_items`
- `external_tasks` (with unique key on action_item_id + provider + provider_project_key)
- `notifications`

Additional schema present: `participants`, `tenant_integrations`, `audit_events`, `chat_sessions`, `chat_messages`

## Test Count

160 passing (as of May 2026)
