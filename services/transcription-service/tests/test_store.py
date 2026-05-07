from transcription_service.store import AuroraTranscriptionStore, InMemoryMetadataStore


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


def test_inmemory_transcription_store_records_transcript_metadata():
    store = InMemoryMetadataStore()
    store.record_transcript(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        transcript_bucket="transcript-bucket",
        transcript_key="tenant_demo/mtg_123/vid_123/transcript.json",
        language_code="en-US",
        speaker_diarization=True,
        pii_redaction=False,
    )

    assert store.records[0]["transcriptionStatus"] == "completed"
    assert store.records[0]["languageCode"] == "en-US"


def test_aurora_transcription_store_inserts_transcript_and_updates_video_item():
    connection = StubConnection()
    store = AuroraTranscriptionStore(connection_factory=lambda: connection)

    store.record_transcript(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        transcript_bucket="transcript-bucket",
        transcript_key="tenant_demo/mtg_123/vid_123/transcript.json",
        language_code="en-US",
        speaker_diarization=True,
        pii_redaction=False,
    )

    assert len(connection.cursor_obj.statements) == 2
    assert "INSERT INTO transcripts" in connection.cursor_obj.statements[0][0]
    assert "UPDATE video_items" in connection.cursor_obj.statements[1][0]
    assert connection.committed is True
