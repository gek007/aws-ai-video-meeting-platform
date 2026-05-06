# AI Meeting Intelligence Platform Flow

## Step-by-Step Flow

### 1. Video arrives

A meeting recording is uploaded manually or comes from an external source such as Zoom or Teams. The file is stored in `S3 raw-video`.

### 2. Upload event is raised

`EventBridge` detects the new object and triggers the `ingestion-service` Lambda.

### 3. Ingestion registers the meeting

The `ingestion-service` creates the first metadata records in `Aurora PostgreSQL`:

- `meetings`
- `video_items`
- `processing_jobs`

It then sends a `media.processing.requested` message to `SQS: media-processing`.

### 4. Media processing starts

The `media-service` consumes that queue message and converts the video into normalized audio. The output audio is stored in `S3 audio`.

Then it emits `transcription.requested` to the transcription stage.

### 5. Transcription starts

The `transcription-service` receives the audio event and sends the file to `Amazon Transcribe`.

When transcription is ready:

- transcript JSON is stored in `S3 transcript`
- transcript reference is saved in `Aurora`
- a `meeting.transcript.ready` event is produced

### 6. AI enrichment runs

The `ai-enrichment-service` loads the transcript and sends content to `Amazon Bedrock`.

This stage generates:

- summary
- topics
- decisions
- action items
- bug / feature / todo classification
- embeddings for retrieval

It also stores these outputs in `Aurora` and vector references in `OpenSearch Serverless`.

### 7. Intelligence event is published

After enrichment, the service publishes `meeting.intelligence.generated` to `SNS`.

This is the fan-out point.

### 8. SNS fans out to consumers

`SNS` distributes that intelligence event to multiple `SQS` queues independently, for example:

- `task-creation`
- `notifications`
- analytics or audit consumers later

### 9. Task creation flow

The `task-orchestrator-service` reads extracted action items and prepares them for external systems.

Then the `integration-service` creates issues in tools such as:

- `Jira`
- `GitHub Issues`

Created external IDs and URLs are stored in `Aurora` in `external_tasks`.

### 10. Notification flow

The `notification-service` sends updates to users, such as:

- summary ready
- action item created
- task status changed

Delivery can be through:

- email via `SES`
- Slack
- Teams

### 11. Status observation flow

The `status-observer-service` runs on schedule using `EventBridge Scheduler`.

It checks open tasks in external systems and updates local status in `Aurora`. If something changed, it emits another event that can again go through `SNS` and trigger notifications.

### 12. Search and related meetings

When the user wants related meetings, the `search-query-service` uses metadata from `Aurora` plus vectors from `OpenSearch Serverless` to find semantically similar meetings.

### 13. Meeting chat with RAG

When the user asks a question about a meeting:

- the `chat-rag-service` receives the question
- it retrieves relevant transcript chunks, summaries, topics, decisions, and action items
- it may also use related meetings if allowed
- it sends the retrieved context to `Bedrock`
- it returns a grounded answer with citations

### 14. Aurora's role across the whole flow

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

### 15. S3's role

`S3` stores the heavy artifacts:

- raw video
- extracted audio
- transcript files
- optional derived exports

### 16. Why SNS and SQS together

We use:

- `SQS` for strict stage-by-stage pipeline processing
- `SNS` when one completed event must fan out to multiple consumers

So the typical patterns are:

- `SQS -> Lambda`
- `SNS -> SQS -> Lambda`

