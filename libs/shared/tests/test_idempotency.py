from shared.idempotency import IdempotencyStore


def test_idempotency_store_tracks_seen_keys():
    store = IdempotencyStore()
    assert store.seen("k1") is False
    store.remember("k1")
    assert store.seen("k1") is True

