# Transcription Service

Accepts normalized audio references, can submit jobs to Amazon Transcribe, persists ready transcript metadata, and emits transcript-ready events only when a transcript artifact exists.

## Current Implementation

- `transcriber.py`
  Provides `InMemoryTranscriber` and `AmazonTranscribeClient`
- `store.py`
  Persists transcript metadata and updates `video_items.transcription_status`
- `publisher.py`
  Sends the next event to `ai-enrichment` SQS
- completion handling
  Processes completed Transcribe events, persists the transcript, and publishes `meeting.transcript.ready`

## Current Limitation

Failed Transcribe jobs currently return `transcription.job.failed`, but retry and alerting behavior is still pending.
