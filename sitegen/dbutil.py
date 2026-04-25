"""Small SQLite helpers used by the page generators.

prometeu.db has the git-history schema:

  commits      (id, namespace, commit_at, hash, ...)
  namespaces   (id, name)
  <ns>             — latest row per id (current snapshot)
  <ns>_version     — every observed version of each row, with _commit FK
  <ns>_version_detail — column-level diffs (rare use)

Most "what's current" queries hit <ns> directly; "what changed" queries join
<ns>_version to commits via _commit.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect(db_path: str | Path):
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    )
    return cur.fetchone() is not None


def rows(con: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    cur = con.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def latest_commit_at(con: sqlite3.Connection) -> str | None:
    cur = con.execute("SELECT max(commit_at) FROM commits")
    row = cur.fetchone()
    return row[0] if row else None


def latest_commit_for_namespace(con: sqlite3.Connection, namespace: str) -> int | None:
    cur = con.execute(
        """SELECT max(c.id) FROM commits c
           JOIN namespaces n ON c.namespace = n.id
           WHERE n.name = ?""",
        (namespace,),
    )
    row = cur.fetchone()
    return row[0] if row and row[0] is not None else None
