# AI Meeting Intelligence Platform

AWS-native event-driven platform for processing meeting recordings, extracting intelligence, creating external tasks, and supporting meeting chat with RAG.

## Current Codebase Status

The repository contains a working Python Lambda-first implementation with real persistence, real AWS adapters, and 160 passing tests.

### Fully implemented

- **`ingestion-service`**
  Persists initial `meetings`, `video_items`, and `processing_jobs` records and publishes to `media-processing` SQS.
- **`media-service`**
  `InMemoryConverter`, `FFmpegSubprocessConverter`, and `MediaConvertAdapter` for video-to-audio conversion. `MediaConvertAdapter` stores business IDs in `UserMetadata` so the EventBridge completion callback can recover them. `MediaConversionCompletionService` handles both sync (FFmpeg) and async (MediaConvert) paths.
- **`transcription-service`**
  Submits audio to `Amazon Transcribe`, persists transcript metadata, and handles Transcribe completion events to emit `meeting.transcript.ready`.
- **`ai-enrichment-service`**
  Chunks transcripts, calls `Amazon Bedrock` when `BEDROCK_MODEL_ID` is configured, persists summaries/topics/decisions/action items/transcript chunks, generates and indexes embeddings via `BedrockEmbeddingGenerator` + `OpenSearchVectorIndexer` when configured.
- **`integration-service`**
  Creates external tasks in Jira or GitHub. Idempotency guard prevents duplicate task creation for the same `(action_item_id, provider, provider_project_key)` triple. `AuroraIntegrationStore` with `ON CONFLICT DO NOTHING`.
- **`notification-service`**
  `InMemoryNotificationSender`, `SESNotificationSender` (email), `SlackWebhookSender` (Slack), and `CompositeSender` routing by channel type.
- **`status-observer-service`**
  `InMemoryStatusPoller`, `JiraStatusPoller`, `GitHubStatusPoller` for external status sync. Distinguishes `task.status.changed` (prior state existed and changed) from `task.status.synced` (first observation).
- **`search-query-service`**
  `InMemorySearchStore` (keyword title search + topic-overlap scoring) and `AuroraSearchStore` (ILIKE + JOIN SQL). `SearchQueryService` with `search_meetings` and `related_meetings` operations.
- **`chat-rag-service`**
  `InMemoryRetriever` and `OpenSearchRetriever` for chunk retrieval. `InMemoryAnswerer` and `BedrockAnswerer` for answer generation. Returns citations and confidence.
- **`apps/api`**
  Pre-signed S3 upload flow via `S3PresignedUploader`. All meeting, summary, action-item, search, and chat endpoints. Chat uses `_build_retriever()` seeded from `repository.transcript_chunks` when OpenSearch is not configured.

### In-memory fallbacks (no AWS credentials needed for tests)

All real adapters have `InMemory*` counterparts — `InMemoryConverter`, `InMemoryEmbeddingGenerator`, `InMemoryVectorIndexer`, `InMemoryRetriever`, `InMemoryAnswerer`, `InMemoryNotificationSender`, `InMemoryUploader`, etc.

### Still pending

- scheduled `EventBridge Scheduler` polling for `status-observer-service`
- `SNS -> SQS` subscription wiring for task-creation and notification consumers in AWS infrastructure
- real frontend

## Repository Structure

```
apps/
  api/          Public API for meetings, uploads, integrations, and chat
  web/          Reserved frontend area
services/
  ingestion-service/
  media-service/
  transcription-service/
  ai-enrichment-service/
  task-orchestrator-service/
  integration-service/
  notification-service/
  status-observer-service/
  search-query-service/
  chat-rag-service/
libs/
  contracts/    Shared API, event, and message schemas
  shared/       IDs, responses, Aurora base store, repository abstractions
  observability/ Logging and correlation helpers
  connectors/   Jira and GitHub adapters
infra/terraform/
database/       Aurora schema, migrations, seeds
tests/          Integration and end-to-end test suites
```

## Verification

```
160 passed
```
