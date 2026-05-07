from transcription_service.publisher import InMemoryQueuePublisher
from transcription_service.service import TranscriptionService


def test_transcription_service_builds_transcript_reference():
    publisher = InMemoryQueuePublisher()
    result = TranscriptionService(publisher=publisher).transcribe(
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


def test_transcription_service_allows_custom_transcript_settings():
    publisher = InMemoryQueuePublisher()
    result = TranscriptionService(publisher=publisher).transcribe(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "transcriptOutputBucket": "custom-transcript-bucket",
            "speakerDiarization": False,
            "piiRedaction": True,
        }
    ).next_event

    assert result["transcript"]["bucket"] == "custom-transcript-bucket"
    assert result["transcript"]["speakerDiarization"] is False
    assert result["transcript"]["piiRedaction"] is True
