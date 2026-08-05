"""Splits a multi-file unified diff into one chunk per file."""

import re

FILE_HEADER_PATTERN = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.MULTILINE)


def split_diff_by_file(diff: str) -> list[dict]:
    """Split a unified diff into per-file chunks.

    Returns a list of {"file": str, "content": str}, one per file touched
    in the diff. If no file headers are found, returns the whole diff as
    a single unnamed chunk rather than failing outright.
    """
    matches = list(FILE_HEADER_PATTERN.finditer(diff))
    if not matches:
        return [{"file": "unknown", "content": diff}] if diff.strip() else []

    chunks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(diff)
        file_name = match.group(2)
        chunks.append({"file": file_name, "content": diff[start:end]})
    return chunks