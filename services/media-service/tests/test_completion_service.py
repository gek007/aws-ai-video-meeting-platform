import pytest
from media_service.publisher import InMemoryQueuePublisher
from media_service.store import InMemoryMetadataStore
from media_service.service import MediaConversionCompletionService


def _base_event():
    return {
        "tenantId": "tenant_123",
        "meetingId": "mtg_123",
        "videoItemId": "vid_123",
        "correlationId": "corr_123",
        "conversionEngine": "mediaconvert",
    }


def test_completion_service_emits_transcription_requested_on_success():
    publisher = InMemoryQueuePublisher()
    store = InMemoryMetadataStore()
    event = {
        "status": "COMPLETE",
        "jobId": "mc-job-123",
        "conversionEngine": "mediaconvert",
        "userMetadata": {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "outputBucket": "audio-bucket",
            "outputKey": "tenant_123/mtg_123/vid_123/audio.wav",
        },
    }
    result = MediaConversionCompletionService(publisher=publisher, metadata_store=store).complete(event)

    assert result.next_event["eventType"] == "transcription.requested"
    assert result.next_event["tenantId"] == "tenant_123"
    assert result.next_event["audio"]["bucket"] == "audio-bucket"
    assert result.next_event["audio"]["key"] == "tenant_123/mtg_123/vid_123/audio.wav"
    assert result.next_event["conversion"]["jobId"] == "mc-job-123"
    assert len(publisher.messages) == 1
    assert store.updates[0]["audioKey"] == "tenant_123/mtg_123/vid_123/audio.wav"


def test_completion_service_handles_native_eventbridge_format():
    """Native aws.mediaconvert EventBridge events carry IDs only in detail.userMetadata."""
    publisher = InMemoryQueuePublisher()
    store = InMemoryMetadataStore()
    event = {
        "source": "aws.mediaconvert",
        "detail": {
            "status": "COMPLETE",
            "JobId": "mc-job-456",
            "userMetadata": {
                "tenantId": "tenant_123",
                "meetingId": "mtg_123",
                "videoItemId": "vid_123",
                "outputBucket": "audio-bucket",
                "outputKey": "tenant_123/mtg_123/vid_123/audio.wav",
            },
        },
    }
    result = MediaConversionCompletionService(publisher=publisher, metadata_store=store).complete(event)
    assert result.next_event["eventType"] == "transcription.requested"
    assert result.next_event["tenantId"] == "tenant_123"
    assert publisher.messages[0]["audio"]["bucket"] == "audio-bucket"


def test_completion_service_emits_failed_event_on_error():
    publisher = InMemoryQueuePublisher()
    store = InMemoryMetadataStore()
    event = {
        "status": "ERROR",
        "jobId": "mc-job-789",
        "userMetadata": {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
        },
    }
    result = MediaConversionCompletionService(publisher=publisher, metadata_store=store).complete(event)

    assert result.next_event["eventType"] == "media.conversion.job.failed"
    assert result.next_event["failedStatus"] == "ERROR"
    assert result.next_event["tenantId"] == "tenant_123"
    assert len(publisher.messages) == 0
    assert len(store.updates) == 0


def test_completion_service_raises_when_job_id_missing():
    publisher = InMemoryQueuePublisher()
    store = InMemoryMetadataStore()
    with pytest.raises(ValueError, match="jobId"):
        MediaConversionCompletionService(publisher=publisher, metadata_store=store).complete(
            {"userMetadata": {"tenantId": "t", "meetingId": "m", "videoItemId": "v"}, "status": "COMPLETE"}
        )


def test_completion_service_raises_when_ids_missing_from_metadata():
    publisher = InMemoryQueuePublisher()
    store = InMemoryMetadataStore()
    with pytest.raises(ValueError, match="tenantId"):
        MediaConversionCompletionService(publisher=publisher, metadata_store=store).complete(
            {"status": "COMPLETE", "jobId": "mc-job-x", "userMetadata": {"outputBucket": "b"}}
        )
