from transcription_service.handler import lambda_handler


def test_transcription_handler_returns_transcript_ready():
    response = lambda_handler(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
        },
        None,
    )
    assert response["body"]["nextEvent"]["eventType"] == "meeting.transcript.ready"
    assert response["body"]["nextEvent"]["transcript"]["key"] == "tenant_123/mtg_123/vid_123/transcript.json"
