"""Database access layer for catalog entities and specs."""
from __future__ import annotations

import sqlite3
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Literal, overload

DB_FILE = "catalog.db"


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS categories(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS brands(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category_id, name),
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS models(
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            name     TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(brand_id, name),
            FOREIGN KEY(brand_id) REFERENCES brands(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS model_specs(
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            key      TEXT NOT NULL,
            value    TEXT,
            FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()

    def ensure_created_at(table: str):
        cur.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in cur.fetchall()}
        if "created_at" not in columns:
            cur.execute(
                f"ALTER TABLE {table} ADD COLUMN created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
            )
            conn.commit()

    ensure_created_at("categories")
    ensure_created_at("brands")
    ensure_created_at("models")

    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO categories(name) VALUES(?)",
            [("Смартфони",), ("Планшети",)],
        )
        conn.commit()
    conn.close()


# ---- CRUD helpers -----------------------------------------------------------------

def _trimmed_rows(rows: Sequence[Sequence[object]]) -> List[Tuple[object, ...]]:
    trimmed: List[Tuple[object, ...]] = []
    for row in rows:
        if not row:
            continue
        idx = row[0]
        name = row[1] if len(row) > 1 else None
        if isinstance(name, str):
            name = name.strip()
        if len(row) == 2:
            trimmed.append((idx, name))
        elif len(row) >= 3:
            trimmed.append((idx, name, *row[2:]))
        else:
            trimmed.append(tuple(row))
    return trimmed


@overload
def get_categories(include_created: Literal[False] = False) -> List[Tuple[int, str]]:
    ...


@overload
def get_categories(include_created: Literal[True]) -> List[Tuple[int, str, Optional[str]]]:
    ...


def get_categories(include_created: bool = False):
    conn = db_connect()
    cur = conn.cursor()
    if include_created:
        cur.execute("SELECT id, name, created_at FROM categories ORDER BY name")
    else:
        cur.execute("SELECT id, name FROM categories ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return _trimmed_rows(rows)


def add_category(name: str) -> None:
    name = name.strip()
    if not name:
        return
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (name,))
    conn.commit()
    conn.close()


def rename_category(cat_id: int, new_name: str):
    new_name = new_name.strip()
    if not new_name:
        return False
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE categories SET name=? WHERE id=?", (new_name, cat_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        return exc
    finally:
        conn.close()


def delete_category(cat_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


@overload
def get_brands(category_id: int, include_created: Literal[False] = False) -> List[Tuple[int, str]]:
    ...


@overload
def get_brands(category_id: int, include_created: Literal[True]) -> List[Tuple[int, str, Optional[str]]]:
    ...


def get_brands(category_id: int, include_created: bool = False):
    conn = db_connect()
    cur = conn.cursor()
    if include_created:
        cur.execute(
            "SELECT id, name, created_at FROM brands WHERE category_id=? ORDER BY name",
            (category_id,),
        )
    else:
        cur.execute(
            "SELECT id, name FROM brands WHERE category_id=? ORDER BY name",
            (category_id,),
        )
    rows = cur.fetchall()
    conn.close()
    return _trimmed_rows(rows)


def add_brand(category_id: int, name: str) -> None:
    name = name.strip()
    if not name:
        return
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO brands(category_id, name) VALUES(?,?)",
        (category_id, name),
    )
    conn.commit()
    conn.close()


def rename_brand(brand_id: int, new_name: str):
    new_name = new_name.strip()
    if not new_name:
        return False
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE brands SET name=? WHERE id=?", (new_name, brand_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        return exc
    finally:
        conn.close()


def delete_brand(brand_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM brands WHERE id=?", (brand_id,))
    conn.commit()
    conn.close()


@overload
def get_models(brand_id: int, include_created: Literal[False] = False) -> List[Tuple[int, str]]:
    ...


@overload
def get_models(brand_id: int, include_created: Literal[True]) -> List[Tuple[int, str, Optional[str]]]:
    ...


def get_models(brand_id: int, include_created: bool = False):
    conn = db_connect()
    cur = conn.cursor()
    if include_created:
        cur.execute(
            "SELECT id, name, created_at FROM models WHERE brand_id=? ORDER BY name",
            (brand_id,),
        )
    else:
        cur.execute(
            "SELECT id, name FROM models WHERE brand_id=? ORDER BY name",
            (brand_id,),
        )
    rows = cur.fetchall()
    conn.close()
    return _trimmed_rows(rows)


def add_model(brand_id: int, name: str) -> None:
    name = name.strip()
    if not name:
        return
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO models(brand_id, name) VALUES(?,?)",
        (brand_id, name),
    )
    conn.commit()
    conn.close()


def rename_model(model_id: int, new_name: str):
    new_name = new_name.strip()
    if not new_name:
        return False
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE models SET name=? WHERE id=?", (new_name, model_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        return exc
    finally:
        conn.close()


def delete_model(model_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM models WHERE id=?", (model_id,))
    conn.commit()
    conn.close()


# ---- Specs (key-value) -------------------------------------------------------------

def get_specs(model_id: int) -> List[Tuple[int, str, Optional[str]]]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, key, value FROM model_specs WHERE model_id=? ORDER BY id",
        (model_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_spec(model_id: int, key: str, value: str) -> Optional[int]:
    key = key.strip()
    if not key:
        return None
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO model_specs(model_id, key, value) VALUES(?,?,?)",
        (model_id, key, value),
    )
    conn.commit()
    inserted_id = cur.lastrowid
    conn.close()
    return inserted_id


def update_spec(spec_id: int, key: str, value: str) -> None:
    key = key.strip()
    if not key:
        return
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE model_specs SET key=?, value=? WHERE id=?",
        (key, value, spec_id),
    )
    conn.commit()
    conn.close()


def delete_spec(spec_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM model_specs WHERE id=?", (spec_id,))
    conn.commit()
    conn.close()


def replace_specs(model_id: int, specs: Sequence[Tuple[str, str]]) -> None:
    """Replace all specifications for a model while preserving order."""

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM model_specs WHERE model_id=?", (model_id,))
    if specs:
        payload: List[Tuple[int, str, str]] = []
        for key, value in specs:
            normalized_key = key.strip()
            if not normalized_key:
                continue
            payload.append((model_id, normalized_key, value))
        if payload:
            cur.executemany(
                "INSERT INTO model_specs(model_id, key, value) VALUES(?,?,?)",
                payload,
            )
    conn.commit()
    conn.close()


def load_specs_map(model_ids: Iterable[int]) -> Dict[int, Dict[str, Optional[str]]]:
    unique_ids: List[int] = []
    seen = set()
    for mid in model_ids:
        try:
            ivalue = int(mid)
        except (TypeError, ValueError):
            continue
        if ivalue in seen:
            continue
        seen.add(ivalue)
        unique_ids.append(ivalue)
    if not unique_ids:
        return {}

    placeholders = ",".join(["?"] * len(unique_ids))
    query = f"""
        SELECT model_id, key, value
        FROM model_specs
        WHERE model_id IN ({placeholders})
        ORDER BY model_id, id
    """

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(query, tuple(unique_ids))
    rows = cur.fetchall()
    conn.close()

    specs_map: Dict[int, Dict[str, Optional[str]]] = {}
    for model_id, key, value in rows:
        if isinstance(key, str):
            key = key.strip()
        if isinstance(value, str):
            value = value.strip()
        if not key:
            continue
        specs_map.setdefault(model_id, {})[key] = value
    return specs_map


def _normalize_id_list(ids) -> List[int]:
    if not ids:
        return []
    if isinstance(ids, (list, tuple, set)):
        result: List[int] = []
        for value in ids:
            try:
                ivalue = int(value)
            except (TypeError, ValueError):
                continue
            if ivalue:
                result.append(ivalue)
        return result
    try:
        ivalue = int(ids)
    except (TypeError, ValueError):
        return []
    return [ivalue] if ivalue else []


def collect_models(
    category_ids=None,
    brand_ids=None,
    model_ids=None,
) -> List[Tuple[str, str, str, int, int, int]]:
    category_ids = _normalize_id_list(category_ids)
    brand_ids = _normalize_id_list(brand_ids)
    model_ids = _normalize_id_list(model_ids)

    conn = db_connect()
    cur = conn.cursor()
    query = """
        SELECT b.name, m.name, c.name, m.id, b.id, c.id
        FROM models m
        JOIN brands b ON m.brand_id = b.id
        JOIN categories c ON b.category_id = c.id
    """
    conditions: List[str] = []
    params: List[int] = []
    if category_ids:
        placeholders = ",".join(["?"] * len(category_ids))
        conditions.append(f"c.id IN ({placeholders})")
        params.extend(category_ids)
    if brand_ids:
        placeholders = ",".join(["?"] * len(brand_ids))
        conditions.append(f"b.id IN ({placeholders})")
        params.extend(brand_ids)
    if model_ids:
        placeholders = ",".join(["?"] * len(model_ids))
        conditions.append(f"m.id IN ({placeholders})")
        params.extend(model_ids)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY c.name, b.name, m.name"
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    cleaned: List[Tuple[str, str, str, int, int, int]] = []
    for brand, model, cat, mid, brand_id, cat_id in rows:
        if isinstance(brand, str):
            brand = brand.strip()
        if isinstance(model, str):
            model = model.strip()
        if isinstance(cat, str):
            cat = cat.strip()
        cleaned.append((brand, model, cat, mid, brand_id, cat_id))
    return cleaned
