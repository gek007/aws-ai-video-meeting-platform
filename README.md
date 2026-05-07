# AI Meeting Intelligence Platform

AWS-native event-driven platform for processing meeting recordings, extracting intelligence, creating external tasks, and supporting meeting chat with RAG.

## Current Codebase Status

The repository is no longer documentation-only. The current implementation is a Python Lambda-first scaffold with real persistence and several real AWS adapters.

Implemented now:

- `ingestion-service`
  Persists initial `meetings`, `video_items`, and `processing_jobs` records and publishes to `media-processing` SQS.
- `media-service`
  Persists normalized audio artifact metadata and publishes to `transcription` SQS.
- `transcription-service`
  Persists transcript metadata and publishes to `ai-enrichment` SQS only when a transcript artifact is ready. The real `Amazon Transcribe` adapter currently returns a job-started event.
- `ai-enrichment-service`
  Persists summaries, topics, decisions, action items, and transcript chunks, then publishes to `SNS`.
- `integration-service`
  Persists created `external_tasks`.
- `notification-service`
  Persists notification records and can deliver email through `Amazon SES`.
- `status-observer-service`
  Persists external task status changes into `external_tasks`.

Implemented with in-memory fallbacks for local tests:

- queue publishers
- SNS publisher
- Transcribe adapter
- SES sender
- Aurora metadata stores

Still stubbed or partial:

- real video-to-audio conversion
- real `Amazon Bedrock` calls for AI enrichment are wired
- real `OpenSearch` vector indexing
- real scheduled status sync and queue subscriptions in AWS infrastructure
- real Transcribe completion event handling is implemented in `transcription-service`

## Important Runtime Notes

- The current `transcription-service` can start an `Amazon Transcribe` job and returns `transcription.job.started`. It also handles completed Transcribe events and emits `meeting.transcript.ready`.
- The current `ai-enrichment-service` can call `Amazon Bedrock` when `BEDROCK_MODEL_ID` is configured, and otherwise uses deterministic local generation.
- The current chat and search services are scaffolded and tested, but not yet backed by real embeddings or OpenSearch.

## Repository Structure

- `apps/api`
  Public API layer for meeting queries, uploads, integrations, and chat endpoints.
- `apps/web`
  Reserved frontend application area for meetings, summaries, action items, and chat.
- `services/`
  Independent backend services aligned to the architecture:
  - `ingestion-service`
  - `media-service`
  - `transcription-service`
  - `ai-enrichment-service`
  - `task-orchestrator-service`
  - `integration-service`
  - `notification-service`
  - `status-observer-service`
  - `search-query-service`
  - `chat-rag-service`
- `libs/contracts`
  Shared API, event, and message schemas.
- `libs/shared`
  Cross-service utilities, IDs, responses, idempotency helpers, and repository abstractions.
- `libs/observability`
  Logging and correlation helpers.
- `libs/connectors`
  External provider adapters such as Jira and GitHub.
- `infra/terraform`
  Infrastructure as code for AWS environments and reusable modules.
- `database`
  Aurora schema assets, migrations, and seeds.
- `docs`
  Reserved supporting architecture, API, and operations documentation area.
- `scripts`
  Local automation scripts for setup, validation, and tooling.
- `tests`
  Integration and end-to-end test suites.

## Root Docs

- [AGENT.md](/G:/__VSCode/youtube-analytic/AGENT.md)
- [FLOW.md](/G:/__VSCode/youtube-analytic/FLOW.md)
- [TODO.md](/G:/__VSCode/youtube-analytic/TODO.md)
- [AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md](/G:/__VSCode/youtube-analytic/AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md)
- [ARCHITECTURE_DIAGRAMS.md](/G:/__VSCode/youtube-analytic/ARCHITECTURE_DIAGRAMS.md)

## Verification

Current test status after the latest implementation pass:

- `67 passed`
