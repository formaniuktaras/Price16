from identifiers import FieldItem, ensure_unique_key, sanitize_key


def test_sanitize_key_removes_symbols():
    assert sanitize_key("282ME(n(") == "282MEN"


def test_sanitize_key_trims_and_uppercases():
    assert sanitize_key(" privacy clear (ARM) ") == "PRIVACYCLEARARM"


def test_sanitize_key_cyrillic_text_removed():
    assert sanitize_key(" NAZVAPOZYTSIYI (Російська) ") == "NAZVAPOZYTSIYI"


def test_sanitize_key_empty_fallback():
    assert sanitize_key("###") == "ID"


def test_ensure_unique_key_increments_suffix():
    assert ensure_unique_key("ABC", {"ABC", "ABC2"}) == "ABC3"


def test_field_item_preserves_label():
    label = "OPYSUKR (Українська)"
    item = FieldItem(key="OPYSUKR", label=label, enabled=True)
    assert item.label == label
