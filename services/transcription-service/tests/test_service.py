from transcription_service.publisher import InMemoryQueuePublisher
from transcription_service.transcriber import InMemoryTranscriber, TranscriptionArtifact
from transcription_service.store import InMemoryMetadataStore
from transcription_service.service import TranscriptionService


class SubmittedTranscriber:
    def transcribe(self, **_kwargs):
        return TranscriptionArtifact(
            transcript_bucket="transcript-bucket",
            transcript_key="tenant_123/mtg_123/vid_123/transcript.json",
            language_code="en-US",
            speaker_diarization=True,
            pii_redaction=False,
            job_name="transcribe-job",
            provider="amazon-transcribe",
            is_ready=False,
        )


def test_transcription_service_builds_transcript_reference():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = TranscriptionService(
        publisher=publisher,
        metadata_store=metadata_store,
        transcriber=InMemoryTranscriber(),
    ).transcribe(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "audio": {
                "bucket": "audio-bucket",
                "key": "tenant_123/mtg_123/vid_123/audio.wav",
            },
        }
    ).next_event

    assert result["eventType"] == "meeting.transcript.ready"
    assert result["transcript"]["bucket"] == "transcript-bucket"
    assert result["transcript"]["key"] == "tenant_123/mtg_123/vid_123/transcript.json"
    assert result["transcript"]["speakerDiarization"] is True
    assert result["transcript"]["piiRedaction"] is False
    assert result["transcriptionProvider"] == "in-memory"
    assert publisher.messages[0]["eventType"] == "meeting.transcript.ready"
    assert metadata_store.records[0]["transcriptKey"] == "tenant_123/mtg_123/vid_123/transcript.json"


def test_transcription_service_allows_custom_transcript_settings():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = TranscriptionService(
        publisher=publisher,
        metadata_store=metadata_store,
        transcriber=InMemoryTranscriber(),
    ).transcribe(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "audio": {
                "bucket": "audio-bucket",
                "key": "tenant_123/mtg_123/vid_123/audio.wav",
            },
            "transcriptOutputBucket": "custom-transcript-bucket",
            "languageCode": "en-GB",
            "speakerDiarization": False,
            "piiRedaction": True,
        }
    ).next_event

    assert result["transcript"]["bucket"] == "custom-transcript-bucket"
    assert result["transcript"]["language"] == "en-GB"
    assert result["transcript"]["speakerDiarization"] is False
    assert result["transcript"]["piiRedaction"] is True
    assert metadata_store.records[0]["piiRedaction"] is True


def test_transcription_service_does_not_publish_ready_event_until_transcript_exists():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = TranscriptionService(
        publisher=publisher,
        metadata_store=metadata_store,
        transcriber=SubmittedTranscriber(),
    ).transcribe(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "audio": {
                "bucket": "audio-bucket",
                "key": "tenant_123/mtg_123/vid_123/audio.wav",
            },
        }
    ).next_event

    assert result["eventType"] == "transcription.job.started"
    assert result["expectedTranscript"]["key"] == "tenant_123/mtg_123/vid_123/transcript.json"
    assert publisher.messages == []
    assert metadata_store.records == []
