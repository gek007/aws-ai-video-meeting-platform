# AI Meeting Intelligence Platform Flow

## Current Flow

This file describes the current implemented flow in the repository, not only the target architecture.

## Step-by-Step Flow

### 1. Video arrives

A meeting recording is uploaded manually or comes from an external source such as Zoom or Teams. The file is stored in `S3 raw-video`.

### 2. Upload event is raised

`EventBridge` detects the new object and triggers the `ingestion-service` Lambda.

### 3. Ingestion registers the meeting

The `ingestion-service` creates initial metadata records in `Aurora PostgreSQL`:

- `meetings`
- `video_items`
- `processing_jobs`

It then sends a `media.processing.requested` message to `SQS: media-processing`.

### 4. Media processing starts

The `media-service` consumes that queue message and prepares the normalized audio artifact contract.

Current code behavior:

- derives a deterministic `S3 audio` key
- persists `audio_s3_key` and media processing state in `Aurora`
- sends `transcription.requested` to the transcription queue

Current limitation:

- real video-to-audio conversion is not implemented yet

### 5. Transcription starts

The `transcription-service` receives the audio event and can submit the file to `Amazon Transcribe`.

Current code behavior:

- starts an `Amazon Transcribe` job when `TRANSCRIBE_OUTPUT_BUCKET` is configured
- returns `transcription.job.started` for real Transcribe submissions
- persists transcript reference data in `Aurora` only when the transcript artifact is ready
- handles completed Transcribe events and publishes `meeting.transcript.ready` to `SQS: ai-enrichment`

Current limitation:

- failed Transcribe jobs currently return `transcription.job.failed`, but richer retry and alerting behavior is still pending

### 6. AI enrichment runs

The `ai-enrichment-service` consumes the transcript-ready event.

Current code behavior:

- chunks transcript content
- calls `Amazon Bedrock` when `BEDROCK_MODEL_ID` is configured
- uses deterministic local generation when Bedrock is not configured
- builds structured meeting intelligence
- persists:
  - `summaries`
  - `topics`
  - `decisions`
  - `action_items`
  - `transcript_chunks`
- updates `video_items.ai_enrichment_status`
- publishes `meeting.intelligence.generated` to `SNS`

Current limitation:

- embeddings and `OpenSearch` indexing are still planned

### 7. SNS fans out to consumers

`SNS` distributes the intelligence event to multiple downstream queues independently, including:

- `SQS: task-creation`
- `SQS: notifications`

### 8. Task creation flow

The `task-orchestrator-service` reads extracted action items and prepares them for external systems.

Then the `integration-service` creates issues in tools such as:

- `Jira`
- `GitHub Issues`

Created external IDs and URLs are stored in `Aurora` in `external_tasks`.

### 9. Notification flow

The `notification-service` sends updates to users, such as:

- summary ready
- action item created
- task status changed

Current code behavior:

- persists notification records in `Aurora`
- can send email through `Amazon SES`
- uses an in-memory sender when SES is not configured

Still planned:

- Slack delivery
- Teams delivery
- retry and DLQ behavior

### 10. Status observation flow

The `status-observer-service` is intended to run on schedule using `EventBridge Scheduler`.

Current code behavior:

- accepts a status event payload
- updates `external_tasks.external_status`
- updates `last_synced_at`
- returns a `task.status.changed` event shape

Current limitation:

- real scheduled polling against external providers is not implemented yet

### 11. Search and related meetings

When the user wants related meetings, the `search-query-service` is intended to use metadata from `Aurora` plus vectors from `OpenSearch Serverless`.

Current code behavior:

- query behavior is scaffolded
- real OpenSearch-backed similarity retrieval is still pending

### 12. Meeting chat with RAG

When the user asks a question about a meeting:

- the `chat-rag-service` receives the question
- it retrieves transcript-like and artifact-like context
- it returns a grounded answer with citations

Current limitation:

- real embeddings and `Bedrock` generation are still pending

### 13. Aurora's role across the whole flow

`Aurora PostgreSQL` is the system of record for:

- meetings
- video items
- transcript references
- summaries
- topics
- decisions
- action items
- external tasks
- notifications
- chat sessions and messages
- processing jobs

### 14. S3's role

`S3` stores the heavy artifacts:

- raw video
- extracted audio
- transcript files
- optional derived exports

### 15. Why SNS and SQS together

We use:

- `SQS` for strict stage-by-stage pipeline processing
- `SNS` when one completed event must fan out to multiple consumers

So the typical patterns are:

- `SQS -> Lambda`
- `SNS -> SQS -> Lambda`
