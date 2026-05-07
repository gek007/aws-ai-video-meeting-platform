from media_service.store import AuroraMediaStore, InMemoryMetadataStore


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


def test_inmemory_media_store_records_audio_artifact():
    store = InMemoryMetadataStore()
    store.record_audio_artifact(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        audio_bucket="audio-bucket",
        audio_key="tenant_demo/mtg_123/vid_123/audio.wav",
        conversion_engine="mediaconvert",
    )

    assert store.updates[0]["videoItemId"] == "vid_123"
    assert store.updates[0]["processingStatus"] == "completed"


def test_aurora_media_store_updates_video_item_audio_fields():
    connection = StubConnection()
    store = AuroraMediaStore(connection_factory=lambda: connection)

    store.record_audio_artifact(
        tenant_id="tenant_demo",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        audio_bucket="audio-bucket",
        audio_key="tenant_demo/mtg_123/vid_123/audio.wav",
        conversion_engine="mediaconvert",
    )

    assert len(connection.cursor_obj.statements) == 1
    assert "UPDATE video_items" in connection.cursor_obj.statements[0][0]
    assert connection.cursor_obj.statements[0][1][0] == "tenant_demo/mtg_123/vid_123/audio.wav"
    assert connection.committed is True
