"""Simple retry wrapper for network calls (Ollama, Claude API).
Retries the SAME tier once on transient failure before giving up —
distinct from tier escalation, which happens on low confidence, not
on the call itself failing.
"""

import time


def retry_call(fn, *args, retries: int = 2, delay: float = 0.5, **kwargs):
    """Call fn(*args, **kwargs), retrying on exception up to `retries` times
    total, with a short delay between attempts. Re-raises the last
    exception if all attempts fail."""
    last_exception = None
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < retries - 1:
                time.sleep(delay)
    raise last_exception
