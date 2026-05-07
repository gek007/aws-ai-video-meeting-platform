from transcription_service.handler import lambda_handler


def test_transcription_handler_returns_transcript_ready():
    response = lambda_handler(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "audio": {
                "bucket": "audio-bucket",
                "key": "tenant_123/mtg_123/vid_123/audio.wav",
            },
        },
        None,
    )
    assert response["body"]["nextEvent"]["eventType"] == "meeting.transcript.ready"
    assert response["body"]["nextEvent"]["transcript"]["key"] == "tenant_123/mtg_123/vid_123/transcript.json"


def test_transcription_handler_routes_completion_event():
    response = lambda_handler(
        {
            "detail": {
                "TranscriptionJobName": "transcribe__tenant_123__mtg_123__vid_123",
                "TranscriptionJobStatus": "COMPLETED",
            },
            "transcriptOutputBucket": "transcript-bucket",
        },
        None,
    )

    assert response["body"]["nextEvent"]["eventType"] == "meeting.transcript.ready"
    assert response["body"]["nextEvent"]["tenantId"] == "tenant_123"
