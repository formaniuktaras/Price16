from identifiers import make_unique_id, sanitize_key


def test_sanitize_key_removes_symbols():
    assert sanitize_key("282ME(n(") == "282MEN"


def test_make_unique_id_increments_suffix():
    assert make_unique_id("ABC", {"ABC", "ABC2"}) == "ABC3"
