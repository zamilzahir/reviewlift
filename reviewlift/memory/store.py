"""Stub in-memory store for past review results. Will be made persistent later."""


class MemoryStore:
    def __init__(self):
        self._data = {}

    def save(self, pr_id: str, result) -> None:
        self._data[pr_id] = result

    def get(self, pr_id: str):
        return self._data.get(pr_id)