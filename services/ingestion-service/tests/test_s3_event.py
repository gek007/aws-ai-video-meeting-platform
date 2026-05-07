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


def test_ingest_s3_event_maps_detail_payload():
    metadata_store = StubMetadataStore()
    publisher = StubQueuePublisher()
    service = IngestionService(metadata_store=metadata_store, publisher=publisher)

    result = service.ingest_s3_event(
        {
            "bucket": {"name": "raw-video-bucket"},
            "object": {"key": "tenant_demo/demo.mp4"},
            "tenantId": "tenant_demo",
            "source": "manual_upload",
        }
    )

    assert result.next_event["rawVideo"]["bucket"] == "raw-video-bucket"
    assert metadata_store.created[0]["source"] == "manual_upload"
