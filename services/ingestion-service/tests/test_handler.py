from ingestion_service.handler import lambda_handler
from ingestion_service.service import IngestionService


class StubMetadataStore:
    def __init__(self) -> None:
        self.created = []

    def create_initial_records(self, event, processing_job_id: str) -> None:
        payload = event.to_dict()
        payload["processingJobId"] = processing_job_id
        self.created.append(payload)


class StubQueuePublisher:
    def __init__(self) -> None:
        self.messages = []

    def publish_media_processing(self, payload: dict) -> None:
        self.messages.append(payload)


def test_ingestion_service_creates_event_and_next_stage_message():
    metadata_store = StubMetadataStore()
    publisher = StubQueuePublisher()
    service = IngestionService(metadata_store=metadata_store, publisher=publisher)

    result = service.ingest_uploaded_video(
        bucket="raw-video-bucket",
        key="tenant_123/meeting.mp4",
        tenant_id="tenant_123",
        source="manual_upload",
    )

    assert result.meeting_id.startswith("mtg_")
    assert result.video_item_id.startswith("vid_")
    assert result.processing_job_id.startswith("job_")
    assert metadata_store.created[0]["eventType"] == "meeting.uploaded"
    assert publisher.messages[0]["eventType"] == "media.processing.requested"


def test_lambda_handler_returns_accepted_response():
    event = {
        "detail": {
            "bucket": {"name": "raw-video-bucket"},
            "object": {"key": "tenant_123/meeting.mp4"},
            "tenantId": "tenant_123",
            "source": "manual_upload",
        }
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 202
    assert response["body"]["message"] == "Video accepted for processing."
    assert response["body"]["meetingId"].startswith("mtg_")
    assert response["body"]["videoItemId"].startswith("vid_")
