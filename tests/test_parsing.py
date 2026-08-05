from reviewlift.core.parsing import extract_confidence, extract_findings, parse_findings
from reviewlift.core.models import ReviewFinding


def test_extract_findings_clean_json():
    text = '{"findings": [{"file": "a.py", "line": 3, "message": "bad name", "severity": "info"}], "confidence": 0.8}'
    findings = extract_findings(text)
    assert findings == [{"file": "a.py", "line": 3, "message": "bad name", "severity": "info"}]


def test_extract_findings_with_surrounding_prose():
    text = 'Sure, here is my review:\n{"findings": [{"file": "b.py", "line": 1, "message": "x", "severity": "warning"}], "confidence": 0.7}\nHope that helps!'
    findings = extract_findings(text)
    assert len(findings) == 1
    assert findings[0]["file"] == "b.py"


def test_extract_findings_empty_array():
    text = '{"findings": [], "confidence": 0.95}'
    assert extract_findings(text) == []


def test_extract_findings_missing_key_returns_empty_list():
    assert extract_findings("not even json") == []


def test_extract_findings_malformed_json_returns_empty_list():
    text = '{"findings": [{"file": "a.py", "line": 1,}], "confidence": 0.5}'
    assert extract_findings(text) == []


def test_extract_confidence_normal_value():
    assert extract_confidence('{"confidence": 0.75}') == 0.75


def test_extract_confidence_clamps_above_one():
    assert extract_confidence('{"confidence": 1.5}') == 1.0


def test_extract_confidence_negative_value_falls_back_to_default():
    assert extract_confidence('{"confidence": -0.2}', default=0.5) == 0.5


def test_extract_confidence_corrupted_value_falls_back_to_default():
    assert extract_confidence('{"confidence": 0enerdly}', default=0.5) == 0.5


def test_extract_confidence_missing_key_uses_custom_default():
    assert extract_confidence("no confidence here", default=0.9) == 0.9


def test_parse_findings_valid_dicts():
    raw = [{"file": "a.py", "line": 1, "message": "x", "severity": "info"}]
    parsed = parse_findings(raw)
    assert parsed == [ReviewFinding(file="a.py", line=1, message="x", severity="info")]


def test_parse_findings_skips_malformed_entries():
    raw = [
        {"file": "a.py", "line": 1, "message": "ok", "severity": "info"},
        {"file": "b.py"},
        "not a dict",
        {"file": "c.py", "line": 2, "message": "also ok", "severity": "warning"},
    ]
    parsed = parse_findings(raw)
    assert len(parsed) == 2
    assert parsed[0].file == "a.py"
    assert parsed[1].file == "c.py"
    