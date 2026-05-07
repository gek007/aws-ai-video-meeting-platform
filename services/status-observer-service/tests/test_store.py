from status_observer_service.store import AuroraStatusObserverStore, InMemoryMetadataStore


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


def test_inmemory_status_observer_store_records_status():
    store = InMemoryMetadataStore()

    store.record_task_status(
        tenant_id="tenant_demo",
        provider="jira",
        external_id="JIRA-101",
        status="DONE",
    )

    assert store.records[0]["tenantId"] == "tenant_demo"
    assert store.records[0]["externalId"] == "JIRA-101"


def test_aurora_status_observer_store_updates_external_task():
    connection = StubConnection()
    store = AuroraStatusObserverStore(connection_factory=lambda: connection)

    store.record_task_status(
        tenant_id="tenant_demo",
        provider="jira",
        external_id="JIRA-101",
        status="DONE",
    )

    assert len(connection.cursor_obj.statements) == 1
    assert "UPDATE external_tasks" in connection.cursor_obj.statements[0][0]
    assert "tenant_id = %s" in connection.cursor_obj.statements[0][0]
    assert connection.committed is True
