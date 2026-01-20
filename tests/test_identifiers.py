from identifiers import clean_id, make_unique_id, sanitize_key, ensure_unique_key


def test_clean_id_removes_symbols():
    assert clean_id("282ME(n(") == "282MEN"


def test_clean_id_trims_and_uppercases():
    assert clean_id(" privacy clear (ARM) ") == "PRIVACYCLEARARM"


def test_clean_id_empty_fallback():
    assert clean_id("###") == "ID"


def test_make_unique_id_increments_suffix():
    assert make_unique_id("ABC", {"ABC", "ABC2"}) == "ABC3"


def test_sanitize_key_removes_symbols():
    assert sanitize_key("282ME(n(") == "282MEN"


def test_sanitize_key_trims_and_uppercases():
    assert sanitize_key(" NAZVAPOZYTSIYI (Російська) ") == "NAZVAPOZYTSIYI"


def test_ensure_unique_key_increments_suffix():
    assert ensure_unique_key("ABC", {"ABC", "ABC2"}) == "ABC3"
