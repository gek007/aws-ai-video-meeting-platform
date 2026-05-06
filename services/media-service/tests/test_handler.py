from media_service.handler import lambda_handler


def test_media_handler_returns_transcription_request():
    response = lambda_handler(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "rawVideo": {
                "bucket": "raw-video-bucket",
                "key": "tenant_123/meeting.mp4",
            },
        },
        None,
    )
    assert response["statusCode"] == 202
    assert response["body"]["nextEvent"]["eventType"] == "transcription.requested"
    assert response["body"]["nextEvent"]["audio"]["key"] == "tenant_123/mtg_123/vid_123/audio.wav"
