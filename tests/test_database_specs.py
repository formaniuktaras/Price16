import database


def _prepare_model(tmp_path, monkeypatch) -> int:
    db_path = tmp_path / "specs.db"
    monkeypatch.setattr(database, "DB_FILE", str(db_path))
    database.init_db()

    database.add_category("Тестова")
    categories = database.get_categories()
    cat_id = next(cid for cid, name in categories if name == "Тестова")

    database.add_brand(cat_id, "BrandX")
    brands = database.get_brands(cat_id)
    brand_id = next(bid for bid, name in brands if name == "BrandX")

    database.add_model(brand_id, "ModelX")
    models = database.get_models(brand_id)
    model_id = next(mid for mid, name in models if name == "ModelX")
    return model_id


def test_insert_spec_returns_row_id(tmp_path, monkeypatch):
    model_id = _prepare_model(tmp_path, monkeypatch)

    spec_id = database.insert_spec(model_id, "Параметр", "Значення")
    assert isinstance(spec_id, int) and spec_id > 0

    specs = database.get_specs(model_id)
    assert len(specs) == 1
    stored_id, key, value = specs[0]
    assert stored_id == spec_id
    assert key == "Параметр"
    assert value == "Значення"


def test_replace_specs_resets_previous_values(tmp_path, monkeypatch):
    model_id = _prepare_model(tmp_path, monkeypatch)
    first_id = database.insert_spec(model_id, "Old", "123")
    assert first_id

    database.replace_specs(
        model_id,
        [
            ("  Key A  ", "  Value A  "),
            ("Key B", "Value B"),
            ("", "should be ignored"),
        ],
    )

    specs = database.get_specs(model_id)
    assert [(key, value) for _sid, key, value in specs] == [
        ("Key A", "  Value A  "),
        ("Key B", "Value B"),
    ]

    database.replace_specs(
        model_id,
        [
            ("Key B", "Updated"),
            ("Key C", "New"),
        ],
    )

    specs = database.get_specs(model_id)
    assert [(key, value) for _sid, key, value in specs] == [
        ("Key B", "Updated"),
        ("Key C", "New"),
    ]
