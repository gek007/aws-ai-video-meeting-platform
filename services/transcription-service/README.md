# Transcription Service

Accepts normalized audio references, can submit jobs to Amazon Transcribe, persists ready transcript metadata, and emits transcript-ready events only when a transcript artifact exists.

## Current Implementation

- `transcriber.py`
  Provides `InMemoryTranscriber` and `AmazonTranscribeClient`
- `store.py`
  Persists transcript metadata and updates `video_items.transcription_status`
- `publisher.py`
  Sends the next event to `ai-enrichment` SQS

## Current Limitation

The service can start a real `Amazon Transcribe` job and returns `transcription.job.started`. A later iteration should add the completion callback handler that emits `meeting.transcript.ready`.
