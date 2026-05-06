# Media Service

Converts raw meeting video into normalized audio and emits the next transcription event.

## Current Conversion Contract

The service currently prepares the conversion output contract for the next stage:

- requires `rawVideo.bucket` and `rawVideo.key`
- derives a deterministic `S3` output path for normalized audio
- emits transcription-ready audio metadata:
  - `wav`
  - `16000 Hz`
  - mono channel
- includes conversion metadata so the implementation can later be backed by `MediaConvert` or `FFmpeg`
