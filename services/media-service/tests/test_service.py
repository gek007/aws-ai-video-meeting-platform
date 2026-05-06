from media_service.publisher import InMemoryQueuePublisher
from media_service.service import MediaService


def test_media_service_builds_audio_reference():
    publisher = InMemoryQueuePublisher()
    result = MediaService(publisher=publisher).process(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "rawVideo": {
                "bucket": "raw-video-bucket",
                "key": "tenant_123/meeting.mp4",
            },
        }
    ).next_event

    assert result["eventType"] == "transcription.requested"
    assert result["audio"]["bucket"] == "audio-bucket"
    assert result["audio"]["key"] == "tenant_123/mtg_123/vid_123/audio.wav"
    assert result["audio"]["format"] == "wav"
    assert result["audio"]["sampleRateHz"] == 16000
    assert result["audio"]["channels"] == 1
    assert result["sourceVideo"]["bucket"] == "raw-video-bucket"
    assert result["conversion"]["engine"] == "mediaconvert"
    assert publisher.messages[0]["eventType"] == "transcription.requested"


def test_media_service_allows_custom_output_bucket_and_engine():
    publisher = InMemoryQueuePublisher()
    result = MediaService(publisher=publisher).process(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "rawVideo": {
                "bucket": "raw-video-bucket",
                "key": "tenant_123/meeting.mp4",
            },
            "audioOutputBucket": "custom-audio-bucket",
            "conversionEngine": "ffmpeg",
        }
    ).next_event

    assert result["audio"]["bucket"] == "custom-audio-bucket"
    assert result["conversion"]["engine"] == "ffmpeg"


def test_media_service_publishes_to_queue_publisher():
    publisher = InMemoryQueuePublisher()
    MediaService(publisher=publisher).process(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "rawVideo": {
                "bucket": "raw-video-bucket",
                "key": "tenant_123/meeting.mp4",
            },
        }
    )

    assert len(publisher.messages) == 1
    assert publisher.messages[0]["audio"]["key"] == "tenant_123/mtg_123/vid_123/audio.wav"
