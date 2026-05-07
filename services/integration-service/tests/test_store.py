from integration_service.store import AuroraIntegrationStore, InMemoryMetadataStore


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


def test_inmemory_integration_store_records_external_task():
    store = InMemoryMetadataStore()
    store.record_external_task(
        tenant_id="tenant_demo",
        action_item_id="act_123",
        provider="jira",
        external_id="JIRA-101",
        external_url="https://jira.example.com/browse/JIRA-101",
        status="OPEN",
    )

    assert store.records[0]["externalId"] == "JIRA-101"


def test_aurora_integration_store_inserts_external_task():
    connection = StubConnection()
    store = AuroraIntegrationStore(connection_factory=lambda: connection)

    store.record_external_task(
        tenant_id="tenant_demo",
        action_item_id="act_123",
        provider="jira",
        external_id="JIRA-101",
        external_url="https://jira.example.com/browse/JIRA-101",
        status="OPEN",
    )

    assert len(connection.cursor_obj.statements) == 1
    assert "INSERT INTO external_tasks" in connection.cursor_obj.statements[0][0]
    assert connection.committed is True
