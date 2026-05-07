from search_query_service.store import AuroraSearchStore, InMemorySearchStore


# ── InMemorySearchStore ──────────────────────────────────────────────────────

def _meetings():
    return [
        {"meetingId": "mtg_001", "tenantId": "t1", "title": "Q1 Budget Planning"},
        {"meetingId": "mtg_002", "tenantId": "t1", "title": "Login Timeout Fix"},
        {"meetingId": "mtg_003", "tenantId": "t2", "title": "Budget Review"},
    ]


def _topics():
    return [
        {"meetingId": "mtg_001", "tenantId": "t1", "label": "budget"},
        {"meetingId": "mtg_001", "tenantId": "t1", "label": "planning"},
        {"meetingId": "mtg_002", "tenantId": "t1", "label": "auth"},
        {"meetingId": "mtg_003", "tenantId": "t1", "label": "budget"},
        {"meetingId": "mtg_003", "tenantId": "t1", "label": "planning"},
    ]


def test_inmemory_search_finds_by_title():
    store = InMemorySearchStore(meetings=_meetings(), topics=_topics())
    results = store.search_meetings(tenant_id="t1", query="budget", limit=20)
    assert len(results) == 1
    assert results[0]["meetingId"] == "mtg_001"
    assert results[0]["score"] == 1.0
    assert results[0]["matchType"] == "title"


def test_inmemory_search_is_case_insensitive():
    store = InMemorySearchStore(meetings=_meetings(), topics=_topics())
    results = store.search_meetings(tenant_id="t1", query="LOGIN", limit=20)
    assert len(results) == 1
    assert results[0]["meetingId"] == "mtg_002"


def test_inmemory_search_scoped_to_tenant():
    store = InMemorySearchStore(meetings=_meetings(), topics=_topics())
    results = store.search_meetings(tenant_id="t2", query="budget", limit=20)
    assert len(results) == 1
    assert results[0]["meetingId"] == "mtg_003"


def test_inmemory_search_returns_empty_when_no_match():
    store = InMemorySearchStore(meetings=_meetings(), topics=_topics())
    results = store.search_meetings(tenant_id="t1", query="zzznomatch", limit=20)
    assert results == []


def test_inmemory_related_meetings_scores_by_shared_topics():
    store = InMemorySearchStore(meetings=_meetings(), topics=_topics())
    results = store.related_meetings(tenant_id="t1", meeting_id="mtg_001", limit=10)
    assert len(results) == 1
    assert results[0]["meetingId"] == "mtg_003"
    assert results[0]["score"] == 1.0  # both budget+planning shared out of 2 source topics


def test_inmemory_related_meetings_returns_empty_when_no_topics():
    store = InMemorySearchStore(meetings=_meetings(), topics=[])
    results = store.related_meetings(tenant_id="t1", meeting_id="mtg_001", limit=10)
    assert results == []


def test_inmemory_related_meetings_scoped_to_tenant():
    store = InMemorySearchStore(meetings=_meetings(), topics=_topics())
    # mtg_003 topics are labelled t1 — from t2 perspective there are no topics for mtg_001
    results = store.related_meetings(tenant_id="t2", meeting_id="mtg_001", limit=10)
    assert results == []


# ── AuroraSearchStore ────────────────────────────────────────────────────────

class StubCursor:
    def __init__(self, rows=None) -> None:
        self.statements: list[tuple] = []
        self._rows = rows or []

    def execute(self, sql, params):
        self.statements.append((sql, params))

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class StubConnection:
    def __init__(self, rows=None) -> None:
        self.cursor_obj = StubCursor(rows)

    def cursor(self):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_aurora_search_meetings_executes_query():
    rows = [("mtg_001", "Q1 Budget", "DONE", "2025-01-01T10:00:00")]
    conn = StubConnection(rows=rows)
    store = AuroraSearchStore(connection_factory=lambda: conn)
    results = store.search_meetings(tenant_id="t1", query="budget", limit=5)
    assert len(results) == 1
    assert results[0]["meetingId"] == "mtg_001"
    assert results[0]["title"] == "Q1 Budget"
    assert results[0]["matchType"] == "metadata"
    sql, params = conn.cursor_obj.statements[0]
    assert "SELECT" in sql
    assert params[0] == "t1"
    assert params[3] == 5


def test_aurora_search_returns_empty_list_on_no_rows():
    conn = StubConnection(rows=[])
    store = AuroraSearchStore(connection_factory=lambda: conn)
    results = store.search_meetings(tenant_id="t1", query="zzz", limit=20)
    assert results == []


def test_aurora_related_meetings_executes_query():
    rows = [("mtg_002", 2, 0.8)]
    conn = StubConnection(rows=rows)
    store = AuroraSearchStore(connection_factory=lambda: conn)
    results = store.related_meetings(tenant_id="t1", meeting_id="mtg_001", limit=5)
    assert len(results) == 1
    assert results[0]["meetingId"] == "mtg_002"
    assert results[0]["score"] == 0.8


def test_aurora_related_returns_empty_list_on_no_rows():
    conn = StubConnection(rows=[])
    store = AuroraSearchStore(connection_factory=lambda: conn)
    results = store.related_meetings(tenant_id="t1", meeting_id="mtg_001", limit=10)
    assert results == []
