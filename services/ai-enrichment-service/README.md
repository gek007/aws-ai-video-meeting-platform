# AI Enrichment Service

Generates summaries, action items, topics, and the downstream SNS fan-out event.

## Current Implementation

- persists:
  - `summaries`
  - `topics`
  - `decisions`
  - `action_items`
  - `transcript_chunks`
- updates `video_items.ai_enrichment_status`
- publishes `meeting.intelligence.generated` to `SNS`
- validates structured output shape
- uses `BedrockEnrichmentGenerator` when `BEDROCK_MODEL_ID` is configured
- uses `DeterministicEnrichmentGenerator` for local development and tests

## Current Limitation

Real embedding generation and OpenSearch indexing are still pending.
