import os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.mkdtemp(prefix="oa-test-")
os.environ["OA_DB"] = os.path.join(_tmp, "t.db")      # must be set before the app is imported
os.environ["OA_TEST_MODE"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app import bank, clock, db  # noqa: E402
from backend.app.main import app  # noqa: E402


@pytest.fixture()
def client():
    clock.reset()
    for f in Path(_tmp).glob("t.db*"):
        f.unlink()
    db.init()
    with TestClient(app) as c:
        yield c
    clock.reset()


ORDER = ["mcq", "apt", "da", "sql", "pandas", "dsa"]


def new_attempt(client, aid="oa01", profile="standard"):
    r = client.post("/api/attempts", json={"assessmentId": aid, "profile": profile})
    assert r.status_code == 200
    return r.json()["attemptId"]


def goto_section(client, att, idx):
    """Fast-forward the fake clock to just after section `idx` has started (never sleeps)."""
    st = client.get(f"/api/attempts/{att}").json()
    cur = st["currentSection"]
    for i in range(cur, idx):
        remaining = client.get(f"/api/attempts/{att}").json()["sections"][i]["remainingSeconds"]
        clock.advance(remaining + 1)
    return client.get(f"/api/attempts/{att}").json()


def q_of(aid, qid):
    return bank.find_question(bank.get(aid), qid)[1]


def ref(aid, qid):
    return q_of(aid, qid)["solution"]["referenceSolution"]
