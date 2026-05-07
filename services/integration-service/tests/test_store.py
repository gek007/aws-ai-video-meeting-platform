from integration_service.store import AuroraIntegrationStore, InMemoryMetadataStore


class StubCursor:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []
        self._fetchone_result = None

    def execute(self, sql: str, params: tuple) -> None:
        self.statements.append((sql, params))

    def fetchone(self):
        return self._fetchone_result

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


def _record_kwargs(project_key="PROJ"):
    return {
        "tenant_id": "tenant_demo",
        "action_item_id": "act_123",
        "provider": "jira",
        "provider_project_key": project_key,
        "external_id": "JIRA-101",
        "external_url": "https://jira.example.com/browse/JIRA-101",
        "status": "OPEN",
    }


def test_inmemory_store_records_external_task():
    store = InMemoryMetadataStore()
    store.record_external_task(**_record_kwargs())
    assert store.records[0]["externalId"] == "JIRA-101"
    assert store.records[0]["providerProjectKey"] == "PROJ"


def test_inmemory_store_find_returns_none_when_not_found():
    store = InMemoryMetadataStore()
    result = store.find_existing_task(action_item_id="act_123", provider="jira", provider_project_key="PROJ")
    assert result is None


def test_inmemory_store_find_returns_existing_record():
    store = InMemoryMetadataStore()
    store.record_external_task(**_record_kwargs())
    result = store.find_existing_task(action_item_id="act_123", provider="jira", provider_project_key="PROJ")
    assert result is not None
    assert result["externalId"] == "JIRA-101"


def test_inmemory_store_find_distinguishes_project_keys():
    store = InMemoryMetadataStore()
    store.record_external_task(**_record_kwargs(project_key="PROJ-A"))
    result = store.find_existing_task(action_item_id="act_123", provider="jira", provider_project_key="PROJ-B")
    assert result is None


def test_aurora_store_inserts_external_task():
    connection = StubConnection()
    store = AuroraIntegrationStore(connection_factory=lambda: connection)
    store.record_external_task(**_record_kwargs())
    assert len(connection.cursor_obj.statements) == 1
    assert "INSERT INTO external_tasks" in connection.cursor_obj.statements[0][0]
    assert connection.committed is True


def test_aurora_store_find_returns_none_when_row_missing():
    connection = StubConnection()
    connection.cursor_obj._fetchone_result = None
    store = AuroraIntegrationStore(connection_factory=lambda: connection)
    result = store.find_existing_task(action_item_id="act_123", provider="jira", provider_project_key="PROJ")
    assert result is None


def test_aurora_store_find_returns_existing_row():
    connection = StubConnection()
    connection.cursor_obj._fetchone_result = ("JIRA-101", "https://jira.example.com/browse/JIRA-101", "OPEN")
    store = AuroraIntegrationStore(connection_factory=lambda: connection)
    result = store.find_existing_task(action_item_id="act_123", provider="jira", provider_project_key="PROJ")
    assert result["externalId"] == "JIRA-101"
    assert result["status"] == "OPEN"
