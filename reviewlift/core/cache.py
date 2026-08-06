"""Diff-hash-based result cache. Performance optimization: if the exact
same diff content has been reviewed before, skip re-calling any models
entirely and return the cached result.

Persisted to a JSON file so the cache survives across separate CLI runs,
unlike MemoryStore which is in-process only.
"""

import hashlib
import json
import os

CACHE_FILE = os.path.join(os.getcwd(), ".reviewlift_cache.json")


def diff_hash(diff: str) -> str:
    return hashlib.sha256(diff.encode("utf-8")).hexdigest()


def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache: dict) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except OSError:
        pass


def get_cached(diff: str) -> dict | None:
    cache = load_cache()
    return cache.get(diff_hash(diff))


def set_cached(diff: str, output: dict) -> None:
    cache = load_cache()
    cache[diff_hash(diff)] = output
    save_cache(cache)
