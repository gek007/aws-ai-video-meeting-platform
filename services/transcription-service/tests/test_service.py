from transcription_service.publisher import InMemoryQueuePublisher
from transcription_service.store import InMemoryMetadataStore
from transcription_service.service import TranscriptionService


def test_transcription_service_builds_transcript_reference():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = TranscriptionService(publisher=publisher, metadata_store=metadata_store).transcribe(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
        }
    ).next_event

    assert result["eventType"] == "meeting.transcript.ready"
    assert result["transcript"]["bucket"] == "transcript-bucket"
    assert result["transcript"]["key"] == "tenant_123/mtg_123/vid_123/transcript.json"
    assert result["transcript"]["speakerDiarization"] is True
    assert result["transcript"]["piiRedaction"] is False
    assert publisher.messages[0]["eventType"] == "meeting.transcript.ready"
    assert metadata_store.records[0]["transcriptKey"] == "tenant_123/mtg_123/vid_123/transcript.json"


def test_transcription_service_allows_custom_transcript_settings():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = TranscriptionService(publisher=publisher, metadata_store=metadata_store).transcribe(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
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
