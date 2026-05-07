import pytest
from media_service.converter import InMemoryConverter, MediaConvertAdapter


def test_in_memory_converter_returns_ready_artifact():
    converter = InMemoryConverter()
    artifact = converter.convert(
        source_bucket="raw-video",
        source_key="tenant/meeting.mp4",
        output_bucket="audio-bucket",
        output_key="tenant/mtg/vid/audio.wav",
    )
    assert artifact.is_ready is True
    assert artifact.audio_bucket == "audio-bucket"
    assert artifact.audio_key == "tenant/mtg/vid/audio.wav"
    assert artifact.engine == "in-memory"
    assert len(converter.conversions) == 1


def test_mediaconvert_adapter_submits_job():
    captured = {}

    def fake_client():
        class _Client:
            def create_job(self, **kwargs):
                captured.update(kwargs)
                return {"Job": {"Id": "mc-job-123"}}
        return _Client()

    adapter = MediaConvertAdapter(role_arn="arn:aws:iam::123:role/MCRole", client_factory=fake_client)
    artifact = adapter.convert(
        source_bucket="raw-video",
        source_key="tenant/meeting.mp4",
        output_bucket="audio-bucket",
        output_key="tenant/mtg/vid/audio.wav",
        tenant_id="tenant_123",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        correlation_id="corr_123",
    )

    assert artifact.is_ready is False
    assert artifact.job_id == "mc-job-123"
    assert artifact.engine == "mediaconvert"
    assert artifact.audio_bucket == "audio-bucket"
    assert captured["Role"] == "arn:aws:iam::123:role/MCRole"
    assert "Settings" in captured
    assert captured["UserMetadata"]["outputKey"] == "tenant/mtg/vid/audio.wav"
    assert captured["UserMetadata"]["tenantId"] == "tenant_123"
    assert captured["UserMetadata"]["meetingId"] == "mtg_123"
    assert captured["UserMetadata"]["videoItemId"] == "vid_123"
    assert captured["UserMetadata"]["correlationId"] == "corr_123"


def test_mediaconvert_adapter_includes_queue_when_set():
    def fake_client():
        class _Client:
            def create_job(self, **kwargs):
                return {"Job": {"Id": "mc-job-456", **kwargs}}
        return _Client()

    adapter = MediaConvertAdapter(
        role_arn="arn:aws:iam::123:role/MCRole",
        queue_arn="arn:aws:mediaconvert:us-east-1:123:queues/Default",
        client_factory=fake_client,
    )
    artifact = adapter.convert(
        source_bucket="raw-video",
        source_key="tenant/meeting.mp4",
        output_bucket="audio-bucket",
        output_key="tenant/mtg/vid/audio.wav",
    )
    assert artifact.is_ready is False


def test_mediaconvert_adapter_requires_role():
    with pytest.raises(ValueError, match="MEDIACONVERT_ROLE_ARN"):
        MediaConvertAdapter()
