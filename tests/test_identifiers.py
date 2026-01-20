from identifiers import clean_id, make_unique_id


def test_clean_id_removes_symbols():
    assert clean_id("282ME(n(") == "282MEN"


def test_clean_id_trims_and_uppercases():
    assert clean_id(" privacy clear (ARM) ") == "PRIVACYCLEARARM"


def test_clean_id_empty_fallback():
    assert clean_id("###") == "ID"


def test_make_unique_id_increments_suffix():
    assert make_unique_id("ABC", {"ABC", "ABC2"}) == "ABC3"
