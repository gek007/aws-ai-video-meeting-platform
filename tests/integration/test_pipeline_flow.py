from ai_enrichment_service.service import AIEnrichmentService
from chat_rag_service.service import ChatRAGService
from ingestion_service.service import IngestionService
from integration_service.service import IntegrationService
from media_service.service import MediaService
from notification_service.service import NotificationService
from shared.repository import InMemoryRepository
from task_orchestrator_service.service import TaskOrchestratorService
from transcription_service.service import TranscriptionService


class StubMetadataStore:
    def __init__(self) -> None:
        self.created = []

    def create_initial_records(self, event) -> None:
        self.created.append(event.to_dict())


class StubQueuePublisher:
    def __init__(self) -> None:
        self.messages = []

    def publish_media_processing(self, payload: dict) -> None:
        self.messages.append(payload)


def test_pipeline_flow_from_ingestion_to_notification():
    metadata_store = StubMetadataStore()
    publisher = StubQueuePublisher()
    ingestion = IngestionService(metadata_store=metadata_store, publisher=publisher)
    ingestion_result = ingestion.ingest_uploaded_video(
        bucket="raw-video-bucket",
        key="tenant_demo/demo.mp4",
        tenant_id="tenant_demo",
        source="manual_upload",
    )

    media_event = MediaService().process(ingestion_result.next_event | {"audioOutputBucket": "audio-bucket"})
    transcript_event = TranscriptionService().transcribe(media_event)
    intelligence_event = AIEnrichmentService().enrich(transcript_event | {"transcriptText": "authentication timeout action item"})
    task_request = TaskOrchestratorService().orchestrate(intelligence_event)
    external_task = IntegrationService().create_external_task(task_request)
    notification = NotificationService().notify({"templateName": "action_item_created"})

    assert media_event["eventType"] == "transcription.requested"
    assert transcript_event["eventType"] == "meeting.transcript.ready"
    assert intelligence_event["eventType"] == "meeting.intelligence.generated"
    assert task_request["eventType"] == "task.creation.requested"
    assert external_task["eventType"] == "external.task.created"
    assert notification["eventType"] == "notification.sent"


def test_rag_flow_returns_citations_for_known_meeting():
    result = ChatRAGService(InMemoryRepository()).answer("What was decided?", "mtg_123", tenant_id="tenant_demo")
    assert result["meetingId"] == "mtg_123"
    assert len(result["citations"]) >= 1
