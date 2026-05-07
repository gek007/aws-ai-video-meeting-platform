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

## Current Limitation

Real `Amazon Bedrock` inference and real embedding generation are still pending. The current codebase uses deterministic enrichment logic to keep the pipeline and persistence contract in place.
