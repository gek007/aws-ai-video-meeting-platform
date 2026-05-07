from ingestion_service.store import AuroraMetadataStore, InMemoryMetadataStore
from contracts.events import MeetingUploadedEvent, RawVideoLocation


class StubCursor:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple) -> None:
        self.statements.append((sql, params))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class StubConnection:
    def __init__(self) -> None:
        self.cursor_obj = StubCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self) -> None:
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def build_event() -> MeetingUploadedEvent:
    return MeetingUploadedEvent(
        event_type="meeting.uploaded",
        event_version="1.0",
        event_id="evt_123",
        occurred_at="2026-05-07T10:00:00Z",
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        source="manual_upload",
        raw_video=RawVideoLocation(bucket="raw-video-bucket", key="tenant_demo/demo-meeting.mp4"),
        correlation_id="corr_123",
        idempotency_key="tenant_demo:vid_123:meeting.uploaded",
    )


def test_inmemory_metadata_store_records_processing_job_id():
    store = InMemoryMetadataStore()
    store.create_initial_records(build_event(), "job_123")
    assert store.records[0]["processingJobId"] == "job_123"


def test_aurora_metadata_store_inserts_meeting_video_and_job_records():
    connection = StubConnection()
    store = AuroraMetadataStore(connection_factory=lambda: connection)

    store.create_initial_records(build_event(), "job_123")

    assert len(connection.cursor_obj.statements) == 3
    assert "INSERT INTO meetings" in connection.cursor_obj.statements[0][0]
    assert "INSERT INTO video_items" in connection.cursor_obj.statements[1][0]
    assert "INSERT INTO processing_jobs" in connection.cursor_obj.statements[2][0]
    assert connection.committed is True
