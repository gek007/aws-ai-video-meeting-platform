# AI Meeting Intelligence Platform Summary

## Project Goal

Build an AWS-native AI Meeting Intelligence Platform that processes meeting recordings, converts them into structured knowledge, creates actionable items in external systems, notifies participants, tracks task status, and supports chat-based Q&A over meeting content using RAG.

## Current Implementation Snapshot

The repository currently contains a working Python Lambda-first scaffold with passing tests and real adapters in selected places.

Implemented in code:

- real Aurora persistence for:
  - `ingestion-service`
  - `media-service`
  - `transcription-service`
  - `ai-enrichment-service`
  - `integration-service`
  - `notification-service`
  - `status-observer-service`
- real SQS publishers for:
  - `ingestion-service -> media-processing`
  - `media-service -> transcription`
  - `transcription-service -> ai-enrichment`
- real SNS publisher for:
  - `ai-enrichment-service -> meeting-intelligence-topic`
- real AWS adapters for:
  - `transcription-service -> Amazon Transcribe`
  - `notification-service -> Amazon SES`

Still planned:

- real media conversion engine
- real `Amazon Bedrock` for AI enrichment is wired
- real `OpenSearch` indexing
- real scheduled AWS infrastructure
- real Transcribe completion event handling

## Core Product Capabilities

- ingest meeting video from upload or external connector
- extract audio and transcribe speech
- generate summaries, topics, decisions, and action items
- classify action items as `bug`, `feature`, or `todo`
- discover related meetings using embeddings and semantic retrieval
- create external tasks in systems such as `Jira` and `GitHub Issues`
- notify participants and assignees
- observe external task status changes
- support meeting chat with grounded answers and citations

## AWS-Native Architecture

The platform uses a hybrid `SNS + SQS + Lambda` event-driven model.

- `S3`
  Stores raw videos, extracted audio, transcripts, and derived artifacts.
- `EventBridge`
  Captures storage events and drives scheduled jobs.
- `SQS`
  Handles sequential stage-by-stage processing with retry and DLQ support.
- `SNS`
  Broadcasts domain events to multiple independent consumers.
- `Lambda`
  Runs ingestion, orchestration, enrichment, notification, and sync logic.
- `Bedrock`
  Provides AI enrichment when configured; embeddings and chat answer generation are still planned.
- `Aurora PostgreSQL`
  Stores transactional metadata and media lifecycle state.
- `OpenSearch Serverless`
  Planned vector store for related meeting discovery and RAG retrieval.
- `Transcribe`
  Performs speech-to-text on meeting audio.
- `SES` / chat webhooks
  Deliver notifications.

## End-to-End Flow

1. A meeting recording is uploaded to `S3` or received from a connector.
2. `EventBridge` triggers `ingestion-service`.
3. Ingestion persists `meeting`, `video_item`, and `processing_job` records in `Aurora`.
4. Ingestion sends the job to `SQS: media-processing`.
5. Media processing prepares normalized audio metadata, persists the audio artifact reference, and sends the next message to `SQS: transcription`.
6. The transcription stage submits audio to `Amazon Transcribe` or local in-memory transcription. Real Transcribe submissions return `transcription.job.started`; completed Transcribe events persist the ready transcript and send `meeting.transcript.ready` to `SQS: ai-enrichment`.
7. AI enrichment persists summaries, topics, decisions, action items, and transcript chunks.
8. Enrichment publishes `meeting.intelligence.generated` to `SNS`.
9. `SNS` fans out to `SQS` consumers such as task creation and notifications.
10. External task integrations create issues in tools like `Jira` or `GitHub`.
11. Notification services send updates to participants and owners.
12. Status observers poll external task status and update local state.
13. Chat queries use RAG over transcript chunks, summaries, and related artifacts.

## Important Implementation Note

The current code intentionally preserves a simplified downstream contract:

- `transcription-service` starts `Amazon Transcribe`, returns `transcription.job.started`, and handles completed Transcribe events by emitting `meeting.transcript.ready`.

The remaining work around Transcribe is retry, alerting, and production EventBridge wiring for failed or delayed jobs.

## Canonical Eventing Pattern

- Use `SQS -> Lambda` for strict processing stages:
  - media processing
  - transcription
  - AI enrichment
- Use `SNS -> SQS -> Lambda` for fan-out events:
  - meeting intelligence generated
  - task status changed
  - processing failed

This preserves:

- decoupling
- independent retries
- backpressure control
- per-consumer DLQs
- multi-subscriber extensibility

## Major Services

- `ingestion-service`
  Validates uploads, creates core records, and starts processing.
- `media-service`
  Builds normalized audio artifact metadata and updates `video_items`.
- `transcription-service`
  Submits audio to `Amazon Transcribe`, persists ready transcript state, and forwards the pipeline event when the transcript exists.
- `ai-enrichment-service`
  Persists structured meeting intelligence and publishes the SNS fan-out event.
- `task-orchestrator-service`
  Converts extracted action items into integration-ready work.
- `integration-service`
  Connects to `Jira`, `GitHub`, and similar targets and persists `external_tasks`.
- `notification-service`
  Delivers emails through `SES` or in-memory fallback and persists notification history.
- `status-observer-service`
  Polls external systems and persists task status changes.
- `search-query-service`
  Serves read APIs and retrieval-oriented queries.
- `chat-rag-service`
  Answers meeting questions using retrieved context and citations.

## Repository Structure

```text
.
|-- AGENT.md
|-- AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md
|-- ARCHITECTURE_DIAGRAMS.md
|-- FLOW.md
|-- TODO.md
|-- README.md
|-- apps/
|   |-- api/
|   `-- web/
|-- services/
|   |-- ingestion-service/
|   |-- media-service/
|   |-- transcription-service/
|   |-- ai-enrichment-service/
|   |-- task-orchestrator-service/
|   |-- integration-service/
|   |-- notification-service/
|   |-- status-observer-service/
|   |-- search-query-service/
|   `-- chat-rag-service/
|-- libs/
|   |-- contracts/
|   |-- shared/
|   |-- observability/
|   `-- connectors/
|-- infra/
|   `-- terraform/
|-- database/
|   |-- migrations/
|   `-- seeds/
`-- tests/
```

## Database Summary

`Aurora PostgreSQL` is the system of record for metadata, workflow state, integrations, and audit history.

Core implemented persistence areas:

- `meetings`
- `video_items`
- `transcripts`
- `summaries`
- `topics`
- `decisions`
- `action_items`
- `external_tasks`
- `processing_jobs`
- `notifications`
- `transcript_chunks`

Additional schema already present:

- `participants`
- `tenant_integrations`
- `audit_events`
- `chat_sessions`
- `chat_messages`

## RAG / Meeting Chat

The platform supports chat over meeting content using retrieval-augmented generation.

Current code behavior:

- retrieval is scaffolded over transcript and artifact-style data
- tenant-aware filtering exists
- citation-shaped answers are returned
- real embeddings and Bedrock-backed answer generation are still pending

## Recommended AWS Stack

- frontend hosting: `S3 + CloudFront` or `Amplify`
- auth: `Amazon Cognito`
- API layer: `API Gateway + Lambda`
- asynchronous processing: `SQS`, `SNS`, `EventBridge`
- media conversion: `AWS Elemental MediaConvert` or `ECS Fargate + FFmpeg`
- transcription: `Amazon Transcribe`
- LLM and embeddings: `Amazon Bedrock`
- relational data: `Aurora PostgreSQL Serverless v2`
- vector search: `OpenSearch Serverless`
- notifications: `SES`, Slack webhooks, Teams webhooks
- secrets: `Secrets Manager`
- observability: `CloudWatch`, `X-Ray`, `CloudTrail`
- infrastructure as code: `Terraform`

## Current Documentation

- [README.md](/G:/__VSCode/youtube-analytic/README.md)
- [FLOW.md](/G:/__VSCode/youtube-analytic/FLOW.md)
- [TODO.md](/G:/__VSCode/youtube-analytic/TODO.md)
- [AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md](/G:/__VSCode/youtube-analytic/AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md)
- [ARCHITECTURE_DIAGRAMS.md](/G:/__VSCode/youtube-analytic/ARCHITECTURE_DIAGRAMS.md)
