# AI Meeting Intelligence Platform

AWS-native event-driven platform for processing meeting recordings, extracting intelligence, creating external tasks, and supporting meeting chat with RAG.

## Repository Structure

- `apps/api`
  Public API layer for meeting queries, uploads, integrations, and chat endpoints.
- `apps/web`
  Frontend application for meetings, summaries, action items, and chat.
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
  Cross-service utilities and common domain helpers.
- `libs/observability`
  Logging, tracing, metrics, correlation ID middleware.
- `libs/connectors`
  External provider adapters such as Jira, GitHub, Slack, and Teams.
- `infra/terraform`
  Infrastructure as code for AWS environments and reusable modules.
- `database`
  Aurora schema assets, migrations, and seeds.
- `docs`
  Supporting architecture, API, and operations documentation.
- `scripts`
  Local automation scripts for setup, validation, and tooling.
- `tests`
  Integration and end-to-end test suites.

## Root Docs

- `AI_MEETING_INTELLIGENCE_PLATFORM_TDD.md`
- `TODO.md`

## Notes

- This scaffold is intentionally runtime-neutral.
- Service implementation details can be added once the language and framework are finalized.

