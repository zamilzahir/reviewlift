from reviewlift.core.router import classify_chunk, next_tier, should_escalate


def test_classify_chunk_low_risk_goes_to_low_tier():
    assert classify_chunk("def add(a, b):\n    return a + b") == "low"


def test_classify_chunk_detects_auth_keyword():
    assert classify_chunk("def check_auth(token):\n    return token == SECRET") == "advanced"


def test_classify_chunk_detects_sql_keyword():
    assert classify_chunk("cursor.execute(raw_sql_query)") == "advanced"


def test_classify_chunk_is_case_insensitive():
    assert classify_chunk("PASSWORD = 'hunter2'") == "advanced"


def test_next_tier_progression():
    assert next_tier("low") == "mid"
    assert next_tier("mid") == "advanced"


def test_next_tier_at_top_returns_none():
    assert next_tier("advanced") is None


def test_should_escalate_below_threshold():
    assert should_escalate(0.3) is True


def test_should_escalate_above_threshold():
    assert should_escalate(0.9) is False


def test_should_escalate_at_exact_threshold_does_not_escalate():
    assert should_escalate(0.6) is False