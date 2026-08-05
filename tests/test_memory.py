from reviewlift.memory.store import MemoryStore


def test_save_and_get_round_trip():
    store = MemoryStore()
    store.save("pr1", {"confidence": 0.9})
    assert store.get("pr1") == {"confidence": 0.9}


def test_get_unknown_pr_returns_none():
    store = MemoryStore()
    assert store.get("nonexistent") is None


def test_save_overwrites_previous_entry():
    store = MemoryStore()
    store.save("pr1", {"confidence": 0.5})
    store.save("pr1", {"confidence": 0.9})
    assert store.get("pr1") == {"confidence": 0.9}