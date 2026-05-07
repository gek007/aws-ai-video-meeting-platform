# AI Meeting Intelligence Platform Flow

## Current Flow

This file describes the current implemented flow, not only the target architecture.

## Step-by-Step Flow

### 1. Video arrives / Upload initiated

A client calls `POST /upload/init`. The API builds a pre-signed S3 PUT URL via `S3PresignedUploader` (or `InMemoryUploader` when `RAW_VIDEO_BUCKET` is not set). The URL includes tenant/meeting/video IDs as S3 object metadata. The client PUTs the file directly to S3.

### 2. Upload event is raised

`EventBridge` detects the new S3 object and triggers the `ingestion-service` Lambda.

### 3. Ingestion registers the meeting

The `ingestion-service` creates initial metadata records in `Aurora PostgreSQL`:

- `meetings`
- `video_items`
- `processing_jobs`

It then sends a `media.processing.requested` message to `SQS: media-processing`.

### 4. Media processing

The `media-service` consumes the queue message and converts video to audio using one of three converters:

- **`InMemoryConverter`** — returns a ready artifact immediately (tests and local dev)
- **`FFmpegSubprocessConverter`** — runs real FFmpeg in a subprocess; returns a ready artifact
- **`MediaConvertAdapter`** — submits an async AWS Elemental MediaConvert job; stores `tenantId/meetingId/videoItemId` in `UserMetadata`; returns a not-ready artifact with a `job_id`

When the artifact is ready (sync path), `media-service` persists the audio artifact reference and sends `transcription.requested` to `SQS: transcription`.

### 5. MediaConvert completion (async path only)

When a MediaConvert job finishes, EventBridge delivers a completion event to `media-service`. `MediaConversionCompletionService` reads `detail.userMetadata` to recover `tenantId/meetingId/videoItemId`, then continues the pipeline identically to the sync path.

### 6. Transcription starts

The `transcription-service` receives the audio event and submits it to `Amazon Transcribe` when `TRANSCRIBE_OUTPUT_BUCKET` is configured. Otherwise uses a local adapter.

- Persists transcript reference metadata in Aurora
- Handles completed Transcribe events and publishes `meeting.transcript.ready` to `SQS: ai-enrichment`

### 7. AI enrichment

The `ai-enrichment-service` consumes the transcript-ready event:

- chunks transcript content
- calls `Amazon Bedrock` when `BEDROCK_MODEL_ID` is configured; otherwise uses `DeterministicEnrichmentGenerator`
- persists: `summaries`, `topics`, `decisions`, `action_items`, `transcript_chunks`
- generates embeddings via `BedrockEmbeddingGenerator` when `BEDROCK_EMBEDDING_MODEL_ID` is configured
- indexes chunks into `OpenSearch Serverless` via `OpenSearchVectorIndexer` when `OPENSEARCH_ENDPOINT` is configured
- updates `video_items.ai_enrichment_status`
- publishes `meeting.intelligence.generated` to `SNS`

### 8. SNS fans out to consumers

`SNS` distributes the intelligence event to multiple downstream queues:

- `SQS: task-creation`
- `SQS: notifications`

### 9. Task creation flow

The `task-orchestrator-service` reads extracted action items and prepares them for external systems.

The `integration-service` creates issues in Jira or GitHub Issues:

- **Idempotency**: `find_existing_task()` checks for an existing record matching `(action_item_id, provider, provider_project_key)` before calling the connector. Returns `external.task.exists` with `duplicate: true` when already present.
- Created external IDs, URLs, and status are stored in `Aurora: external_tasks`

### 10. Notification flow

The `notification-service` sends updates through `CompositeSender` which routes by channel:

- `email` → `SESNotificationSender` (Amazon SES)
- `slack` → `SlackWebhookSender` (Slack incoming webhook)
- local/test → `InMemoryNotificationSender`

Notification delivery status is persisted in Aurora.

### 11. Status observation

The `status-observer-service` is intended to run on schedule via `EventBridge Scheduler`.

Current behavior:

- `InMemoryStatusPoller` — returns status from a seeded map (tests)
- `JiraStatusPoller` — polls Jira REST API
- `GitHubStatusPoller` — polls GitHub Issues API
- Compares fetched status against the last persisted status
- Emits `task.status.changed` when a prior record exists and the status differs
- Emits `task.status.synced` when no prior record exists (first observation)

### 12. Search and related meetings

The `search-query-service` serves two operations:

- **`search_meetings`** — keyword search with ILIKE on title and summary content (Aurora) or keyword title match (in-memory)
- **`related_meetings`** — finds meetings sharing topic labels, scored by fraction of shared topics (Aurora JOIN or in-memory scoring)

The handler auto-selects `AuroraSearchStore` when `AURORA_DATABASE_URL` / `DATABASE_URL` is set; otherwise uses no store (empty results).

### 13. Meeting chat with RAG

When a user posts a question to `POST /meetings/{id}/chat`:

1. `_build_retriever()` in the API picks either `OpenSearchRetriever` (when `OPENSEARCH_ENDPOINT` is set) or `InMemoryRetriever` seeded from `repository.get_transcript_chunks()`
2. `ChatRAGService` retrieves the most relevant transcript chunks
3. `BedrockAnswerer` (when `BEDROCK_MODEL_ID` is set) or `InMemoryAnswerer` generates a grounded answer
4. Response includes the answer, citations with chunk metadata, confidence level, and meeting/question echo

### 14. Aurora's role

`Aurora PostgreSQL` is the system of record for all transactional state. All Aurora stores inherit from `AuroraBaseStore` in `libs/shared/src/shared/aurora.py`, which provides a lazy `psycopg` import and an injectable `connection_factory` for tests.

### 15. S3's role

`S3` stores:

- raw video (via pre-signed PUT upload)
- extracted audio
- transcript files
- optional derived exports

### 16. SNS + SQS pattern

- `SQS → Lambda` for strict sequential stages (media → transcription → AI enrichment)
- `SNS → SQS → Lambda` for fan-out events (meeting intelligence generated, task status changed)
