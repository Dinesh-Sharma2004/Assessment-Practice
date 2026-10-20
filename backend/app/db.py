import sqlite3
from contextlib import contextmanager

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
  id TEXT PRIMARY KEY, assessment_id TEXT NOT NULL, profile TEXT NOT NULL,
  status TEXT NOT NULL, current_section INTEGER, created_at REAL NOT NULL, completed_at REAL);
CREATE TABLE IF NOT EXISTS sections (
  attempt_id TEXT NOT NULL, idx INTEGER NOT NULL, key TEXT NOT NULL, status TEXT NOT NULL,
  duration INTEGER NOT NULL, started_at REAL, deadline REAL, finalized_at REAL, score REAL,
  PRIMARY KEY (attempt_id, idx));
CREATE TABLE IF NOT EXISTS answers (
  attempt_id TEXT NOT NULL, qid TEXT NOT NULL, value TEXT, review INTEGER NOT NULL DEFAULT 0,
  visited INTEGER NOT NULL DEFAULT 0, updated_at REAL, PRIMARY KEY (attempt_id, qid));
CREATE TABLE IF NOT EXISTS submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id TEXT NOT NULL, qid TEXT NOT NULL, code TEXT NOT NULL,
  submitted_at REAL NOT NULL, earned REAL NOT NULL, detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS results (
  attempt_id TEXT NOT NULL, qid TEXT NOT NULL, earned REAL NOT NULL, max_marks REAL NOT NULL,
  attempted INTEGER NOT NULL, source TEXT NOT NULL, detail TEXT, PRIMARY KEY (attempt_id, qid));
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)   # explicit BEGIN/COMMIT below
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    c = connect()
    try:
        c.executescript(SCHEMA)
    finally:
        c.close()


@contextmanager
def tx():
    """Transaction: commits on success, rolls back on any exception."""
    c = connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        yield c
        c.execute("COMMIT")
    except BaseException:
        c.execute("ROLLBACK")
        raise
    finally:
        c.close()


@contextmanager
def read():
    c = connect()
    try:
        yield c
    finally:
        c.close()
