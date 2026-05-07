# Ingestion Service

Lambda-first service responsible for:

- validating upload events
- creating initial meeting and video item records
- writing processing job state
- publishing the next-stage media processing message

## Current Implementation

- `handler.py`
  Lambda entrypoint for `S3` / `EventBridge`-style upload events
- `service.py`
  Core orchestration logic separated from the Lambda adapter
- `store.py`
  In-memory and Aurora metadata stores
- `publisher.py`
  In-memory and SQS publisher implementations

Implemented now:

- Aurora persistence for `meetings`, `video_items`, and `processing_jobs`
- SQS publishing to `media-processing`
- upload-style event parsing
- idempotency and deduplication helpers

Still planned:

- authenticated pre-signed upload flow
- deeper source metadata validation
