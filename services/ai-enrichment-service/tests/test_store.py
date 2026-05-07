from ai_enrichment_service.store import AuroraAIEnrichmentStore, InMemoryMetadataStore


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


def test_inmemory_ai_store_records_enrichment_payload():
    store = InMemoryMetadataStore()
    store.persist_enrichment(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        summary="Summary",
        topics=["authentication"],
        decisions=[{"description": "Prioritize timeout fix", "owner": "owner@example.com"}],
        action_items=[{"title": "Fix login timeout issue", "item_type": "bug"}],
        transcript_chunks=[{"chunkIndex": 0, "chunkText": "hello", "embeddingRef": "emb_001"}],
        prompt_version="v1",
    )

    assert store.records[0]["summary"] == "Summary"
    assert store.records[0]["aiEnrichmentStatus"] == "completed"


def test_aurora_ai_store_persists_summary_topics_decisions_actions_and_chunks():
    connection = StubConnection()
    store = AuroraAIEnrichmentStore(connection_factory=lambda: connection)

    store.persist_enrichment(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        summary="Summary",
        topics=["authentication", "reliability"],
        decisions=[{"description": "Prioritize timeout fix", "owner": "owner@example.com"}],
        action_items=[{"actionItemId": "act_known", "title": "Fix login timeout issue", "description": "Investigate", "item_type": "bug", "owner_email": "owner@example.com", "priority": "high"}],
        transcript_chunks=[{"chunkIndex": 0, "chunkText": "hello", "embeddingRef": "emb_001"}],
        prompt_version="v1",
    )

    stmts = connection.cursor_obj.statements
    assert len(stmts) == 8  # SELECT (idempotency) + 7 writes
    assert "SELECT" in stmts[0][0]
    assert "INSERT INTO summaries" in stmts[1][0]
    assert "INSERT INTO topics" in stmts[2][0]
    assert "INSERT INTO topics" in stmts[3][0]
    assert "INSERT INTO decisions" in stmts[4][0]
    assert "INSERT INTO action_items" in stmts[5][0]
    assert stmts[5][1][0] == "act_known"
    assert "INSERT INTO transcript_chunks" in stmts[6][0]
    assert "UPDATE video_items" in stmts[7][0]
    assert connection.committed is True
