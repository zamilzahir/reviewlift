from reviewlift.core.diff_split import split_diff_by_file


def test_splits_two_file_diff():
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old\n+new\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-foo\n+bar\n"
    )
    chunks = split_diff_by_file(diff)
    assert len(chunks) == 2
    assert chunks[0]["file"] == "a.py"
    assert chunks[1]["file"] == "b.py"
    assert "old" in chunks[0]["content"]
    assert "foo" in chunks[1]["content"]


def test_single_file_diff_returns_one_chunk():
    diff = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b\n"
    chunks = split_diff_by_file(diff)
    assert len(chunks) == 1
    assert chunks[0]["file"] == "x.py"


def test_no_headers_returns_single_unknown_chunk():
    chunks = split_diff_by_file("just some raw text, not a real diff")
    assert len(chunks) == 1
    assert chunks[0]["file"] == "unknown"


def test_empty_diff_returns_no_chunks():
    assert split_diff_by_file("") == []