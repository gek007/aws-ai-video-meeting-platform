from media_service.converter import InMemoryConverter
from media_service.publisher import InMemoryQueuePublisher
from media_service.store import InMemoryMetadataStore
from media_service.service import MediaService


def test_media_service_builds_audio_reference():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = MediaService(publisher=publisher, metadata_store=metadata_store, converter=InMemoryConverter()).process(
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
    assert result["conversion"]["engine"] == "in-memory"
    assert publisher.messages[0]["eventType"] == "transcription.requested"
    assert metadata_store.updates[0]["audioKey"] == "tenant_123/mtg_123/vid_123/audio.wav"


def test_media_service_allows_custom_output_bucket_and_engine():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = MediaService(publisher=publisher, metadata_store=metadata_store, converter=InMemoryConverter()).process(
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
    assert result["conversion"]["engine"] == "in-memory"
    assert metadata_store.updates[0]["conversionEngine"] == "in-memory"


def test_media_service_publishes_to_queue_publisher():
    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    MediaService(publisher=publisher, metadata_store=metadata_store, converter=InMemoryConverter()).process(
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
    assert metadata_store.updates[0]["processingStatus"] == "completed"


def test_media_service_returns_job_started_when_converter_is_async():
    from media_service.converter import ConversionArtifact

    class AsyncConverter:
        def convert(self, *, source_bucket, source_key, output_bucket, output_key,
                    tenant_id="", meeting_id="", video_item_id="", correlation_id=None):
            return ConversionArtifact(
                audio_bucket=output_bucket,
                audio_key=output_key,
                is_ready=False,
                job_id="async-job-001",
                engine="mediaconvert",
            )

    publisher = InMemoryQueuePublisher()
    metadata_store = InMemoryMetadataStore()
    result = MediaService(
        publisher=publisher,
        metadata_store=metadata_store,
        converter=AsyncConverter(),
    ).process(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "rawVideo": {"bucket": "raw-video-bucket", "key": "tenant_123/meeting.mp4"},
        }
    ).next_event

    assert result["eventType"] == "media.conversion.job.started"
    assert result["conversionJobId"] == "async-job-001"
    assert result["conversionEngine"] == "mediaconvert"
    assert len(publisher.messages) == 0
    assert len(metadata_store.updates) == 0
