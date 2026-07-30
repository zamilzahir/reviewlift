"""MCP tool server exposing PR-reading tools. Stub: returns mock data for now."""

MOCK_DIFF = """diff --git a/app.py b/app.py
+def add(a, b):
+    return a+b
"""


def get_diff(pr_id: str) -> str:
    return MOCK_DIFF


def list_hunks(diff: str) -> list[str]:
    return [diff]