import json

from media_service.handler import lambda_handler


def _processing_event():
    return {
        "tenantId": "tenant_123",
        "meetingId": "mtg_123",
        "videoItemId": "vid_123",
        "correlationId": "corr_123",
        "rawVideo": {
            "bucket": "raw-video-bucket",
            "key": "tenant_123/meeting.mp4",
        },
    }


def test_media_handler_returns_transcription_request():
    response = lambda_handler(_processing_event(), None)
    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    assert body["nextEvent"]["eventType"] == "transcription.requested"
    assert body["nextEvent"]["audio"]["key"] == "tenant_123/mtg_123/vid_123/audio.wav"


def test_media_handler_completion_emits_transcription_requested():
    completion_event = {
        "eventType": "media.conversion.job.completed",
        "status": "COMPLETE",
        "jobId": "mc-job-abc",
        "conversionEngine": "mediaconvert",
        "userMetadata": {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "outputBucket": "audio-bucket",
            "outputKey": "tenant_123/mtg_123/vid_123/audio.wav",
        },
    }
    response = lambda_handler(completion_event, None)
    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    assert body["nextEvent"]["eventType"] == "transcription.requested"
    assert body["nextEvent"]["audio"]["bucket"] == "audio-bucket"


def test_media_handler_completion_failed_status():
    completion_event = {
        "eventType": "media.conversion.job.completed",
        "status": "ERROR",
        "jobId": "mc-job-fail",
        "userMetadata": {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
        },
    }
    response = lambda_handler(completion_event, None)
    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    assert body["nextEvent"]["eventType"] == "media.conversion.job.failed"
