from notification_service.store import AuroraNotificationStore, InMemoryMetadataStore


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


def test_inmemory_notification_store_records_notification():
    store = InMemoryMetadataStore()
    store.record_notification(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        recipient="user@example.com",
        channel="email",
        template_name="summary_ready",
        status="sent",
    )

    assert store.records[0]["recipient"] == "user@example.com"


def test_aurora_notification_store_inserts_notification():
    connection = StubConnection()
    store = AuroraNotificationStore(connection_factory=lambda: connection)

    store.record_notification(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        recipient="user@example.com",
        channel="email",
        template_name="summary_ready",
        status="sent",
    )

    assert len(connection.cursor_obj.statements) == 1
    assert "INSERT INTO notifications" in connection.cursor_obj.statements[0][0]
    assert connection.committed is True
