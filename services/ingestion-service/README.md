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

## Next Steps

- wire Aurora persistence
- wire `SQS` publishing
- add idempotency storage
- add source metadata validation

