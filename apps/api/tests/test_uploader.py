import pytest
from api_app.uploader import InMemoryUploader, S3PresignedUploader


def test_in_memory_uploader_returns_session():
    uploader = InMemoryUploader()
    session = uploader.create_upload_session(filename="meeting.mp4", tenant_id="tenant_123")

    assert session.meeting_id.startswith("mtg_")
    assert session.video_item_id.startswith("vid_")
    assert "tenant_123" in session.s3_key
    assert "meeting.mp4" in session.s3_key
    assert session.method == "PUT"
    assert session.expires_in == 3600
    assert session.s3_bucket == "raw-video-bucket-local"


def test_in_memory_uploader_generates_unique_ids():
    uploader = InMemoryUploader()
    s1 = uploader.create_upload_session(filename="a.mp4", tenant_id="t1")
    s2 = uploader.create_upload_session(filename="a.mp4", tenant_id="t1")
    assert s1.meeting_id != s2.meeting_id
    assert s1.video_item_id != s2.video_item_id


def test_in_memory_uploader_respects_custom_expiry():
    uploader = InMemoryUploader()
    session = uploader.create_upload_session(filename="f.mp4", tenant_id="t", expires_in=600)
    assert session.expires_in == 600


def test_s3_presigned_uploader_raises_without_bucket():
    with pytest.raises(ValueError, match="RAW_VIDEO_BUCKET"):
        S3PresignedUploader()


def test_s3_presigned_uploader_calls_generate_presigned_url():
    calls = []

    def fake_client():
        class _Client:
            def generate_presigned_url(self, operation, Params, ExpiresIn):
                calls.append({"operation": operation, "params": Params, "expiresIn": ExpiresIn})
                return f"https://s3.amazonaws.com/{Params['Bucket']}/{Params['Key']}?sig=fake"
        return _Client()

    uploader = S3PresignedUploader(bucket="my-raw-video-bucket", client_factory=fake_client)
    session = uploader.create_upload_session(
        filename="meeting.mp4",
        tenant_id="tenant_xyz",
        content_type="video/mp4",
        expires_in=1800,
    )

    assert len(calls) == 1
    assert calls[0]["operation"] == "put_object"
    assert calls[0]["params"]["Bucket"] == "my-raw-video-bucket"
    assert "tenant_xyz" in calls[0]["params"]["Key"]
    assert "meeting.mp4" in calls[0]["params"]["Key"]
    assert calls[0]["params"]["ContentType"] == "video/mp4"
    assert calls[0]["params"]["Metadata"]["tenant-id"] == "tenant_xyz"
    assert calls[0]["expiresIn"] == 1800
    assert session.upload_url.startswith("https://s3.amazonaws.com/")
    assert session.meeting_id.startswith("mtg_")
    assert session.video_item_id.startswith("vid_")
