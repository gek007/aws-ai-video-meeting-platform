# AI Meeting Intelligence Platform Summary

## Project Goal

Build an AWS-native AI Meeting Intelligence Platform that processes meeting recordings, converts them into structured knowledge, creates actionable items in external systems, notifies participants, tracks task status, and supports chat-based Q&A over meeting content using RAG.

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
  Provides summarization, extraction, embeddings, and chat answer generation.
- `Aurora PostgreSQL`
  Stores transactional metadata and media lifecycle state.
- `OpenSearch Serverless`
  Stores vectors for related meeting discovery and RAG retrieval.
- `Transcribe`
  Performs speech-to-text on meeting audio.
- `SES` / chat webhooks
  Deliver notifications.

## End-to-End Flow

1. A meeting recording is uploaded to `S3` or received from a connector.
2. `EventBridge` triggers `Ingestion Lambda`.
3. Ingestion persists `meeting`, `video_item`, and `processing_job` records in `Aurora`.
4. Ingestion sends the job to `SQS: media-processing`.
5. Media processing converts video to audio and stores the result in `S3`.
6. The transcription stage sends audio to `Amazon Transcribe`.
7. Transcript artifacts are stored in `S3` and referenced in `Aurora`.
8. AI enrichment loads transcript content and calls `Bedrock`.
9. Enrichment persists summaries, topics, decisions, action items, and embeddings metadata.
10. Enrichment publishes a domain event to `SNS`.
11. `SNS` fans out to `SQS` consumers such as task creation and notifications.
12. External task integrations create issues in tools like `Jira` or `GitHub`.
13. Notification services send updates to participants and owners.
14. Scheduled observers poll external task status and update local state.
15. Chat queries use RAG over transcript chunks, summaries, and related artifacts.

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
  Extracts audio and updates `video_items` processing state.
- `transcription-service`
  Orchestrates `Amazon Transcribe`.
- `ai-enrichment-service`
  Calls `Bedrock` for summary, action item extraction, topic extraction, and embeddings.
- `task-orchestrator-service`
  Converts extracted action items into integration-ready work.
- `integration-service`
  Connects to `Jira`, `GitHub`, `Linear`, `Asana`, Slack, Teams, and similar targets.
- `notification-service`
  Delivers emails and chat notifications.
- `status-observer-service`
  Polls external systems for task changes.
- `search-query-service`
  Serves read APIs and retrieval-oriented queries.
- `chat-rag-service`
  Answers meeting questions using retrieved context and `Bedrock`.

## Repository Structure

```text
.
|-- AGENT.md
|-- AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md
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
|       |-- bootstrap/
|       |-- environments/
|       `-- modules/
|-- database/
|   |-- migrations/
|   `-- seeds/
|-- docs/
|   |-- architecture/
|   |-- api/
|   `-- operations/
|-- scripts/
`-- tests/
    |-- integration/
    `-- e2e/
```

## Database Summary

`Aurora PostgreSQL` is the system of record for metadata, workflow state, integrations, and audit history.

### Core Tables

- `meetings`
  Business-level meeting record.
- `video_items`
  Media-specific record for uploaded video assets, lifecycle status, and artifact pointers.
- `participants`
  Meeting participants and ownership data.
- `transcripts`
  Transcript metadata and storage references.
- `summaries`
  Generated meeting summaries.
- `topics`
  Extracted discussion topics.
- `decisions`
  Captured meeting decisions.
- `action_items`
  Extracted tasks, bugs, and features.
- `external_tasks`
  Mapping from internal action items to external systems.
- `processing_jobs`
  State of pipeline jobs and retryable stages.
- `notifications`
  Outbound notification history.
- `tenant_integrations`
  External system configuration by tenant.
- `audit_events`
  Immutable operational and business audit history.
- `chat_sessions`
  Persisted meeting chat sessions when enabled.
- `chat_messages`
  User and assistant messages for meeting chat.
- `transcript_chunks`
  Chunk metadata used for retrieval and citations.

## Storage and Search

- `S3 raw-video`
  Original uploaded recordings.
- `S3 audio`
  Extracted normalized audio.
- `S3 transcript`
  Transcription outputs.
- `S3 derived-artifacts`
  Optional exports and generated reports.
- `OpenSearch Serverless`
  Vector storage for transcript chunks, summaries, topics, and related meeting retrieval.

## RAG / Meeting Chat

The platform supports chat over meeting content using retrieval-augmented generation.

### Retrieval Sources

- transcript chunks
- summaries
- topics
- decisions
- action items
- optionally related meetings in the same tenant

### Chat Behavior

- question is embedded and matched against indexed meeting artifacts
- top chunks and structured records are assembled into context
- `Bedrock` generates an answer constrained to retrieved evidence
- answer returns with citations and confidence metadata
- if evidence is weak, the system should return insufficient-information responses

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

## Operational Principles

- serverless-first where practical
- event-driven and loosely coupled
- idempotent consumers
- at-least-once delivery
- DLQ per queue
- correlation IDs propagated across events
- prompt versioning for `Bedrock` tasks
- strict tenant isolation
- KMS encryption for data at rest

## Current Documentation

- [AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md](G:\__VSCode\youtube-analytic\AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md)
- [TODO.md](G:\__VSCode\youtube-analytic\TODO.md)
- [README.md](G:\__VSCode\youtube-analytic\README.md)

## Current Assumptions

- architecture is AWS-native and serverless-first
- eventing is hybrid `SNS + SQS + Lambda`
- `Aurora PostgreSQL` is the metadata and workflow system of record
- `OpenSearch Serverless` is the preferred vector store
- MVP starts with manual upload plus `Jira` and `GitHub Issues`
- meeting chat uses RAG with citations
