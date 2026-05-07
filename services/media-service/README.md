# Media Service

Converts raw meeting video into normalized audio and emits the next transcription event.

## Current Implementation

The current code persists the media-processing result and prepares the conversion output contract for the next stage:

- requires `rawVideo.bucket` and `rawVideo.key`
- derives a deterministic `S3` output path for normalized audio
- persists `audio_s3_key` and processing state in Aurora
- emits transcription-ready audio metadata:
  - `wav`
  - `16000 Hz`
  - mono channel
- publishes the next message to `transcription` SQS
- includes conversion metadata so the implementation can later be backed by `MediaConvert` or `FFmpeg`

## Current Limitation

Real video-to-audio conversion is still pending. The service currently models the conversion result and persists the expected audio artifact reference.
