from ai_enrichment_service.service import AIEnrichmentService
from chat_rag_service.service import ChatRAGService
from ingestion_service.service import IngestionService
from integration_service.service import IntegrationService
from integration_service.store import InMemoryMetadataStore as IntegrationMetadataStore
from media_service.publisher import InMemoryQueuePublisher as MediaQueuePublisher
from media_service.service import MediaService
from media_service.store import InMemoryMetadataStore as MediaMetadataStore
from notification_service.sender import InMemoryNotificationSender
from notification_service.service import NotificationService
from notification_service.store import InMemoryMetadataStore as NotificationMetadataStore
from shared.repository import InMemoryRepository
from status_observer_service.service import StatusObserverService
from status_observer_service.store import InMemoryMetadataStore as StatusObserverMetadataStore
from task_orchestrator_service.service import TaskOrchestratorService
from ai_enrichment_service.store import InMemoryMetadataStore as AIEnrichmentMetadataStore
from transcription_service.publisher import InMemoryQueuePublisher as TranscriptionQueuePublisher
from transcription_service.service import TranscriptionService
from transcription_service.store import InMemoryMetadataStore as TranscriptionMetadataStore
from transcription_service.transcriber import InMemoryTranscriber
from ai_enrichment_service.publisher import InMemoryTopicPublisher


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

    media_event = MediaService(
        publisher=MediaQueuePublisher(),
        metadata_store=MediaMetadataStore(),
    ).process(
        ingestion_result.next_event | {"audioOutputBucket": "audio-bucket"}
    ).next_event
    transcript_event = TranscriptionService(
        publisher=TranscriptionQueuePublisher(),
        metadata_store=TranscriptionMetadataStore(),
        transcriber=InMemoryTranscriber(),
    ).transcribe(media_event).next_event
    intelligence_event = AIEnrichmentService(
        publisher=InMemoryTopicPublisher(),
        metadata_store=AIEnrichmentMetadataStore(),
    ).enrich(
        transcript_event | {"transcriptText": "authentication timeout action item"}
    )
    task_request = TaskOrchestratorService().orchestrate(intelligence_event)
    external_task = IntegrationService(metadata_store=IntegrationMetadataStore()).create_external_task(task_request)
    notification = NotificationService(
        metadata_store=NotificationMetadataStore(),
        sender=InMemoryNotificationSender(),
    ).notify({"templateName": "action_item_created"})

    assert media_event["eventType"] == "transcription.requested"
    assert transcript_event["eventType"] == "meeting.transcript.ready"
    assert intelligence_event["eventType"] == "meeting.intelligence.generated"
    assert task_request["eventType"] == "task.creation.requested"
    assert external_task["eventType"] == "external.task.created"
    assert notification["eventType"] == "notification.sent"
    assert notification["provider"] == "in-memory"


def test_rag_flow_returns_citations_for_known_meeting():
    result = ChatRAGService(InMemoryRepository()).answer("What was decided?", "mtg_123", tenant_id="tenant_demo")
    assert result["meetingId"] == "mtg_123"
    assert len(result["citations"]) >= 1


def test_status_observer_flow_updates_external_task_status():
    status_event = StatusObserverService(
        metadata_store=StatusObserverMetadataStore()
    ).sync(
        {
            "tenantId": "tenant_demo",
            "provider": "jira",
            "externalId": "JIRA-101",
            "status": "DONE",
        }
    )

    assert status_event["eventType"] == "task.status.changed"
    assert status_event["tenantId"] == "tenant_demo"
    assert status_event["status"] == "DONE"
