# AI Meeting Intelligence Platform TODO

## Architecture and Planning

- [ ] Confirm MVP scope: upload source, task integrations, notification channels, and tenancy model
- [ ] Confirm compliance requirements: GDPR, HIPAA, SOC2, retention, and deletion rules
- [ ] Finalize AWS region strategy and environment separation
- [x] Choose `Terraform` or `AWS CDK` for infrastructure as code
- [ ] Finalize `MediaConvert` vs `ECS Fargate + FFmpeg`
- [ ] Finalize vector store: `OpenSearch Serverless` vs `Aurora pgvector`
- [ ] Define event naming conventions and versioning strategy
- [x] Define `SNS` topic taxonomy and `SQS` subscription strategy

## Infrastructure Foundation

- [ ] Create AWS accounts or environments for `dev`, `staging`, and `prod`
- [ ] Provision `S3` buckets for raw video, audio, transcripts, and derived artifacts
- [ ] Provision `SQS` queues and DLQs for each processing stage
- [x] Provision `SNS` topics for broadcast-style domain events
- [ ] Provision `EventBridge` rules and scheduler jobs
- [ ] Provision `Aurora PostgreSQL Serverless v2`
- [ ] Provision `OpenSearch Serverless` if selected
- [ ] Provision `Secrets Manager` entries for integrations
- [ ] Provision `CloudWatch` dashboards, alarms, and log groups
- [ ] Provision `KMS` keys for encryption
- [ ] Configure IAM roles and least-privilege policies

## Database Design

- [x] Create schema for `meetings`
- [x] Create schema for `video_items`
- [x] Create schema for `participants`
- [x] Create schema for `transcripts`
- [x] Create schema for `summaries`
- [x] Create schema for `topics`
- [x] Create schema for `decisions`
- [x] Create schema for `action_items`
- [x] Create schema for `external_tasks`
- [x] Create schema for `processing_jobs`
- [x] Create schema for `notifications`
- [x] Create schema for `tenant_integrations`
- [x] Create schema for `audit_events`
- [x] Add indexes for tenant, meeting, status, and sync queries
- [x] Add idempotency constraints and unique keys

## Ingestion Service

- [x] Implement upload initialization API
- [ ] Implement authenticated pre-signed upload flow
- [x] Implement `S3` upload event handling
- [ ] Persist initial `meeting` record
- [ ] Persist initial `video_items` record in Aurora
- [ ] Publish `meeting.uploaded` event to queue
- [x] Add deduplication and idempotency handling

## Media Processing Service

- [ ] Implement video metadata extraction
- [ ] Implement video-to-audio conversion
- [ ] Persist audio artifact reference in `video_items`
- [ ] Update `video_items.processing_status`
- [ ] Publish transcription job event
- [ ] Add retry and failure handling

## Transcription Service

- [ ] Integrate with `Amazon Transcribe`
- [ ] Support diarization
- [ ] Support optional PII redaction
- [ ] Persist transcript artifact reference
- [ ] Create `transcripts` records in Aurora
- [ ] Update `video_items.transcription_status`
- [ ] Publish transcript-ready event

## AI Enrichment Service

- [x] Implement transcript chunking strategy
- [x] Persist transcript chunks for retrieval and citation support
- [x] Define prompt templates and versioning
- [ ] Integrate with `Amazon Bedrock` for summary generation
- [ ] Integrate with `Amazon Bedrock` for action item extraction
- [ ] Integrate with `Amazon Bedrock` for decision and topic extraction
- [x] Implement structured JSON output validation
- [ ] Persist summaries, topics, decisions, and action items
- [ ] Update `video_items.ai_enrichment_status`
- [ ] Generate embeddings for transcript chunks and summaries
- [ ] Publish task-creation events
- [ ] Publish notification events
- [ ] Publish `SNS` domain events for fan-out consumers

## Related Meeting Discovery

- [ ] Design transcript chunk metadata model for vector search
- [ ] Store embeddings in selected vector store
- [x] Implement similarity search API
- [ ] Add re-ranking by tenant, recency, and participants
- [ ] Return supporting transcript excerpts with results

## Meeting Chat with RAG

- [ ] Define chat UX and conversation persistence requirements
- [x] Create schema for `chat_sessions`
- [x] Create schema for `chat_messages`
- [x] Create schema for `transcript_chunks`
- [ ] Implement question embedding generation
- [x] Implement retrieval pipeline over transcript chunks and structured artifacts
- [x] Add permission-aware retrieval filters by tenant and meeting
- [ ] Implement grounded answer generation with `Amazon Bedrock`
- [x] Require citations in every answer when evidence exists
- [x] Return insufficient-information responses when retrieval is weak
- [x] Implement `POST /meetings/{id}/chat`
- [x] Implement chat session history APIs if conversation continuity is required
- [ ] Add metrics for answer latency, citation coverage, and retrieval quality
- [ ] Add evaluation dataset for meeting Q&A quality checks

## External Task Integration

- [x] Define provider abstraction for external issue systems
- [x] Implement `Jira` connector
- [x] Implement `GitHub Issues` connector
- [ ] Map internal action item types to provider issue types
- [ ] Persist external task IDs and URLs
- [ ] Add duplicate prevention for repeated task creation
- [ ] Add rate limit and retry handling
- [ ] Subscribe integration queues to relevant `SNS` topics

## Notifications

- [x] Define notification templates for summary ready
- [x] Define notification templates for action item creation
- [x] Define notification templates for task status changes
- [ ] Implement email delivery with `SES`
- [ ] Implement Slack webhook delivery
- [ ] Persist notification delivery status
- [ ] Add retry and DLQ handling
- [ ] Subscribe notification queues to relevant `SNS` topics

## Status Observation

- [ ] Implement scheduled sync with `EventBridge Scheduler`
- [ ] Implement polling for open external tasks
- [ ] Persist external status changes
- [ ] Trigger notifications on meaningful status changes
- [ ] Add stale-item reminder logic

## API Layer

- [x] Implement `GET /meetings/{id}`
- [x] Implement `GET /meetings/{id}/summary`
- [x] Implement `GET /meetings/{id}/related`
- [x] Implement `GET /meetings/{id}/action-items`
- [x] Implement `GET /video-items/{id}`
- [x] Implement `GET /search/meetings`
- [x] Implement `POST /meetings/{id}/chat`
- [x] Implement `GET /meetings/{id}/chat/sessions`
- [x] Implement `GET /chat/sessions/{sessionId}/messages`
- [x] Implement `POST /integrations/{provider}/connect`
- [x] Implement `POST /tasks/{id}/sync`

## Frontend

- [ ] Decide whether MVP includes a web UI
- [ ] Set up hosting with `S3 + CloudFront` or `Amplify`
- [ ] Implement authentication with `Cognito`
- [ ] Build meeting list page
- [ ] Build meeting details page
- [ ] Build transcript and summary views
- [ ] Build meeting chat panel with citations
- [ ] Build action item dashboard
- [ ] Build integration settings page

## Security and Compliance

- [ ] Enforce encryption at rest with `KMS`
- [ ] Enforce secure transport for all APIs and webhooks
- [ ] Store external credentials in `Secrets Manager`
- [ ] Implement tenant isolation checks
- [ ] Add audit logging for key actions
- [ ] Define retention and deletion workflows
- [ ] Add webhook signature validation where applicable

## Observability

- [ ] Standardize structured logging format
- [ ] Propagate correlation IDs across events
- [ ] Create `CloudWatch` dashboards
- [ ] Add alarms for DLQ depth, queue lag, and Lambda failures
- [ ] Add alarms for `SNS` publish failures and subscription delivery issues
- [ ] Add alarms for transcription and Bedrock failure rates
- [ ] Enable tracing with `X-Ray`

## Testing

- [ ] Add unit tests for event schemas and parsers
- [ ] Add unit tests for idempotency logic
- [ ] Add unit tests for retrieval ranking and citation generation
- [x] Add integration tests for queue-driven flows
- [ ] Add integration tests for Bedrock structured outputs
- [x] Add integration tests for RAG question answering
- [ ] Add integration tests for external connectors
- [ ] Add end-to-end test for full meeting processing flow
- [ ] Add end-to-end test for meeting chat quality and permissions
- [ ] Add load tests for burst upload scenarios
- [ ] Add chaos/failure tests for external dependency outages

## Delivery and Release

- [ ] Set up CI/CD pipeline
- [ ] Add database migration pipeline
- [ ] Add environment configuration management
- [ ] Define rollout strategy for MVP
- [ ] Define rollback procedure for service and prompt changes
- [ ] Prepare production readiness checklist
