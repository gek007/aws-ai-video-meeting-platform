from ingestion_service.publisher import InMemoryQueuePublisher
from ingestion_service.service import IngestionService


class StubMetadataStore:
    def __init__(self) -> None:
        self.created = []

    def create_initial_records(self, event) -> None:
        self.created.append(event.to_dict())


def test_ingestion_service_creates_record_and_media_request():
    metadata_store = StubMetadataStore()
    publisher = InMemoryQueuePublisher()

    result = IngestionService(metadata_store=metadata_store, publisher=publisher).ingest_uploaded_video(
        bucket="raw-video-bucket",
        key="tenant_123/meeting.mp4",
        tenant_id="tenant_123",
        source="manual_upload",
    )

    assert metadata_store.created[0]["tenantId"] == "tenant_123"
    assert publisher.messages[0]["eventType"] == "media.processing.requested"
    assert publisher.messages[0]["rawVideo"]["key"] == "tenant_123/meeting.mp4"
    assert result.next_event["processingJobId"].startswith("job_")
