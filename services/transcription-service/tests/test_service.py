from transcription_service.service import TranscriptionService


def test_transcription_service_builds_transcript_reference():
    result = TranscriptionService().transcribe(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
        }
    )

    assert result["eventType"] == "meeting.transcript.ready"
    assert result["transcript"]["bucket"] == "transcript-bucket"
    assert result["transcript"]["key"] == "vid_123/transcript.json"

