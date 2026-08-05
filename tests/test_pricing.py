from reviewlift.core.pricing import haiku_cost_usd


def test_zero_tokens_costs_nothing():
    assert haiku_cost_usd(0, 0) == 0.0


def test_one_million_input_tokens():
    assert haiku_cost_usd(1_000_000, 0) == 1.00


def test_one_million_output_tokens():
    assert haiku_cost_usd(0, 1_000_000) == 5.00


def test_mixed_tokens():
    expected = (500 / 1_000_000) * 1.00 + (200 / 1_000_000) * 5.00
    assert haiku_cost_usd(500, 200) == expected