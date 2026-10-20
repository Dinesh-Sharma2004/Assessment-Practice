import json
import pytest
from backend.app import bank, clock, engine, execution
from backend.app.config import SECTIONS
import oa_lib as L
from conftest import new_attempt, goto_section, ref, q_of

AIDS = ["oa01", "oa02", "oa03", "oa04", "oa05"]
MINUTES = {"oa01": [30, 15, 20, 20, 30, 30], "oa02": [30, 15, 20, 20, 30, 30], "oa03": [25, 10, 15, 25, 30, 30], "oa04": [20, 10, 15, 25, 30, 40], "oa05": [20, 10, 15, 25, 30, 40]}
COUNTS = {"oa01": [25, 15, 12, 2, 5, 2], "oa02": [25, 15, 12, 2, 5, 2], "oa03": [25, 15, 12, 3, 5, 2], "oa04": [25, 15, 12, 3, 5, 2], "oa05": [25, 15, 12, 3, 5, 2]}
MARKS = [400, 240, 300, 300, 300, 260]


def submit(client, att, qid, code):
    return client.post(f"/api/attempts/{att}/questions/{qid}/submit", json={"code": code})


# 1, 2 ------------------------------------------------------------------ banks
def test_all_five_banks_load():
    assert sorted(bank.banks()) == AIDS


@pytest.mark.parametrize("aid", AIDS)
def test_counts_marks_and_timing(aid):
    doc = bank.get(aid)
    assert bank.shape_problems(doc) == []
    assert [s["type"] for s in doc["sections"]] == SECTIONS
    assert [s["questionCount"] for s in doc["sections"]] == COUNTS[aid]
    assert [sum(q["marks"] for q in s["questions"]) for s in doc["sections"]] == MARKS and doc["totalMarks"] == 1800
    assert [s["durationSeconds"] // 60 for s in doc["sections"]] == MINUTES[aid]
    assert doc["timing"]["standard"]["totalSeconds"] == sum(MINUTES[aid]) * 60


@pytest.mark.parametrize("aid", AIDS)
def test_attempt_sections_follow_spec(client, aid):
    st = client.get(f"/api/attempts/{new_attempt(client, aid)}").json()
    assert [s["durationSeconds"] // 60 for s in st["sections"]] == MINUTES[aid]
    assert st["sections"][0]["status"] == "active" and st["hintsEnabled"] == (aid in ("oa01", "oa02", "oa03"))


# content rules ----------------------------------------------------------
def test_hints_only_in_first_three_oas():
    for aid in AIDS:
        doc = bank.get(aid)
        for s in doc["sections"]:
            for q in s["questions"]:
                assert bool(q.get("hints")) == (aid in AIDS[:3]), q["id"]
                if q["type"] != "mcq" and aid in AIDS[:3]:
                    assert len(q["hints"]) == 3


def test_data_analysis_questions_have_charts_and_sql_tables_counts():
    for aid in AIDS:
        doc = bank.get(aid)
        assert all(q["charts"] for q in bank.section_questions(doc, "da"))
        counts = [q["tableCount"] for q in bank.section_questions(doc, "sql")]
        assert counts == ([1, 2] if aid in ("oa01", "oa02") else [2, 3, 4])
        for q in bank.section_questions(doc, "sql"):
            assert q["sampleTables"] and q["walkthrough"]


# 3 ---------------------------------------------------------------- MCQ
def test_mcq_persist_and_grade(client):
    att = new_attempt(client)
    qs = bank.get("oa01")["sections"][0]["questions"]
    for i, q in enumerate(qs):
        val = q["solution"]["correctOptionId"] if i < 10 else ("A" if q["solution"]["correctOptionId"] != "A" else "B")
        assert client.put(f"/api/attempts/{att}/answers/{q['id']}", json={"value": val}).status_code == 200
    assert client.get(f"/api/attempts/{att}").json()["answers"][qs[0]["id"]]["value"] == qs[0]["solution"]["correctOptionId"]
    client.put(f"/api/attempts/{att}/answers/{qs[0]['id']}", json={"value": "C"})                       # answers can change before expiry
    client.put(f"/api/attempts/{att}/answers/{qs[0]['id']}", json={"value": qs[0]["solution"]["correctOptionId"]})
    clock.advance(100000)
    res = client.get(f"/api/attempts/{att}/results").json()
    assert res["sections"][0]["score"] == sum(q["marks"] for q in qs[:10]) and res["sections"][0]["attempted"] == 25


def test_chart_question_is_graded_like_mcq(client):
    att = new_attempt(client)
    goto_section(client, att, 2)
    q = bank.get("oa01")["sections"][2]["questions"][0]
    st = client.get(f"/api/attempts/{att}").json()
    assert st["questions"][0]["charts"] and "solution" not in st["questions"][0]
    client.put(f"/api/attempts/{att}/answers/{q['id']}", json={"value": q["solution"]["correctOptionId"]})
    clock.advance(100000)
    r = client.get(f"/api/attempts/{att}/results").json()
    assert r["sections"][2]["score"] == q["marks"]


# 4, 6, 7, 8 -------------------------------------------------- coding
def test_sql_select_correct_and_incorrect(client):
    att = new_attempt(client)
    goto_section(client, att, 3)
    ok = submit(client, att, "oa01-sql-01", ref("oa01", "oa01-sql-01")).json()
    assert ok["earned"] == 100 and ok["hiddenPassed"] == ok["hiddenTotal"]
    bad = submit(client, att, "oa01-sql-01", "SELECT 1;").json()
    assert bad["earned"] == 0
    assert "message" not in [t for t in bad["tests"] if t["visibility"] == "hidden"][0]


def test_sql_partial_credit_and_four_table_query(client):
    att = new_attempt(client, "oa03")
    goto_section(client, att, 3)
    q = bank.get("oa03")["sections"][3]["questions"][2]
    assert q["tableCount"] == 4
    assert submit(client, att, q["id"], q["solution"]["referenceSolution"]).json()["earned"] == q["marks"]
    p = submit(client, att, q["id"], q["starterQuery"]).json()["earned"]
    assert 0 <= p < q["marks"]


def test_pandas_executed_and_graded(client):
    att = new_attempt(client)
    goto_section(client, att, 4)
    assert submit(client, att, "oa01-pd-01", ref("oa01", "oa01-pd-01")).json()["earned"] == 60
    r = submit(client, att, "oa01-pd-01", "import pandas as pd\ndef buy_blocks(trades):\n    return trades.copy()\n").json()
    assert r["earned"] < 60


def test_dsa_executed_graded_and_partial(client):
    att = new_attempt(client)
    goto_section(client, att, 5)
    assert submit(client, att, "oa01-dsa-01", ref("oa01", "oa01-dsa-01")).json()["earned"] == 100
    brute = "def best_pair_under_budget(prices, budget):\n    best = -1\n    for i in range(len(prices)):\n        for j in range(i + 1, len(prices)):\n            if prices[i] + prices[j] <= budget:\n                best = max(best, prices[i] + prices[j])\n    return best\n"
    r = submit(client, att, "oa01-dsa-01", brute).json()
    assert 0 < r["earned"] < 100 and any(t["kind"] == "timeout" for t in r["tests"])


def test_partial_marks_match_oa_lib(client):
    doc = bank.get("oa03")
    q = q_of("oa03", "oa03-sql-02")
    for cand in (q["starterQuery"], ref("oa03", "oa03-sql-02"), "SELECT 1"):
        assert execution.score(q, execution.execute(doc, q, cand, "full")) == L.grade_question(q, cand)[0]


def test_runtime_failure_is_reported_not_success(client, monkeypatch):
    att = new_attempt(client)
    goto_section(client, att, 3)
    def boom(*a, **k):
        raise execution.RuntimeFailure("sandbox unavailable")
    monkeypatch.setattr(execution, "execute", boom)
    r = submit(client, att, "oa01-sql-01", "SELECT 1")
    assert r.status_code == 500 and "NOT recorded" in r.json()["message"]
    assert client.get(f"/api/attempts/{att}").json()["submissionCounts"] == {}


def test_infinite_loop_times_out(client):
    att = new_attempt(client)
    goto_section(client, att, 5)
    r = client.post(f"/api/attempts/{att}/questions/oa01-dsa-02/run", json={"code": "def first_unique_index(s):\n    while True:\n        pass\n"}).json()
    assert r["passed"] == 0 and all(t["kind"] == "timeout" for t in r["tests"])


# 9, 10, 11 -------------------------------------------------- navigation / locking
def test_navigation_within_active_section(client):
    att = new_attempt(client)
    st = client.get(f"/api/attempts/{att}").json()
    ids = [q["id"] for q in st["questions"]]
    assert len(ids) == 25 and all(i.startswith("oa01-mcq") for i in ids)
    for qid in reversed(ids):
        assert client.put(f"/api/attempts/{att}/answers/{qid}", json={"visited": True, "review": qid.endswith("05")}).status_code == 200
    a = client.get(f"/api/attempts/{att}").json()["answers"]
    assert all(a[i]["visited"] for i in ids) and a["oa01-mcq-05"]["review"]


def test_future_sections_locked(client):
    att = new_attempt(client)
    for qid in ("oa01-apt-01", "oa01-da-01", "oa01-sql-01", "oa01-pd-01", "oa01-dsa-02"):
        r = client.put(f"/api/attempts/{att}/answers/{qid}", json={"value": "x"})
        assert r.status_code == 403 and r.json()["error"] == "section_locked"
    st = client.get(f"/api/attempts/{att}").json()
    assert [s["status"] for s in st["sections"]] == ["active"] + ["locked"] * 5


def test_completed_sections_cannot_reopen(client):
    att = new_attempt(client)
    client.put(f"/api/attempts/{att}/answers/oa01-mcq-01", json={"value": "A"})
    st = goto_section(client, att, 1)
    assert [s["status"] for s in st["sections"]][:2] == ["finalized", "active"]
    assert client.put(f"/api/attempts/{att}/answers/oa01-mcq-01", json={"value": "B"}).status_code == 403
    assert all(q["id"].startswith("oa01-apt") for q in st["questions"])


# 12-15 -------------------------------------------------- timers
def test_expiry_saves_and_transitions(client):
    att = new_attempt(client)
    client.put(f"/api/attempts/{att}/answers/oa01-mcq-01", json={"value": "B"})
    t0 = client.get(f"/api/attempts/{att}").json()["sections"][0]["deadline"]
    clock.advance(1800.5)
    st = client.get(f"/api/attempts/{att}").json()
    assert st["currentSection"] == 1 and st["sections"][0]["status"] == "finalized"
    assert st["sections"][1]["startedAt"] == t0 and st["sections"][1]["deadline"] == t0 + 900
    clock.advance(100000)
    assert next(q for q in client.get(f"/api/attempts/{att}/results").json()["questions"] if q["id"] == "oa01-mcq-01")["selected"] == "B"


def test_refresh_does_not_reset_timer(client):
    att = new_attempt(client)
    a = client.get(f"/api/attempts/{att}").json()
    clock.advance(300)
    b = client.get(f"/api/attempts/{att}").json()
    assert b["sections"][0]["deadline"] == a["sections"][0]["deadline"]
    assert round(b["sections"][0]["remainingSeconds"]) == round(a["sections"][0]["remainingSeconds"] - 300)


def test_cascade_after_long_downtime_and_final_section_ends_attempt(client):
    att = new_attempt(client)
    clock.advance(8700 + 5)
    st = client.get(f"/api/attempts/{att}").json()
    assert st["status"] == "completed" and st["currentSection"] is None and st["questions"] == []
    assert [s["status"] for s in st["sections"]] == ["finalized"] * 6
    for i in range(1, 6):
        assert st["sections"][i]["startedAt"] == st["sections"][i - 1]["deadline"]
    assert client.get(f"/api/attempts/{att}/results").status_code == 200


def test_expired_section_rejects_changes_and_late_grading(client, monkeypatch):
    att = new_attempt(client)
    goto_section(client, att, 3)
    real = execution.execute
    def slow(*a, **k):
        out = real(*a, **k); clock.advance(1300); return out
    monkeypatch.setattr(execution, "execute", slow)
    assert submit(client, att, "oa01-sql-01", ref("oa01", "oa01-sql-01")).status_code in (409, 403)
    with engine.db.read() as c:
        assert c.execute("SELECT COUNT(*) n FROM submissions").fetchone()["n"] == 0
    monkeypatch.setattr(execution, "execute", real)
    assert client.put(f"/api/attempts/{att}/answers/oa01-sql-01", json={"value": "SELECT 1"}).status_code == 403


def test_unsubmitted_draft_is_auto_graded_and_latest_submission_wins(client):
    att = new_attempt(client)
    goto_section(client, att, 3)
    client.put(f"/api/attempts/{att}/answers/oa01-sql-01", json={"value": ref("oa01", "oa01-sql-01")})
    submit(client, att, "oa01-sql-02", ref("oa01", "oa01-sql-02")); submit(client, att, "oa01-sql-02", "SELECT 1")
    clock.advance(5000)
    qs = {x["id"]: x for x in client.get(f"/api/attempts/{att}/results").json()["questions"]}
    assert qs["oa01-sql-01"]["earned"] == 100 and qs["oa01-sql-01"]["source"] == "draft"
    assert qs["oa01-sql-02"]["earned"] == 0 and qs["oa01-sql-02"]["source"] == "submission"


# NEW: early finish ---------------------------------------------------------
def answer_all(client, att, aid="oa01"):
    st = client.get(f"/api/attempts/{att}").json()
    for q in st["questions"]:
        full = bank.find_question(bank.get(aid), q["id"])[1]
        if q["type"] == "mcq":
            client.put(f"/api/attempts/{att}/answers/{q['id']}", json={"value": full["solution"]["correctOptionId"]})
        else:
            assert submit(client, att, q["id"], full["solution"]["referenceSolution"]).status_code == 200


def test_cannot_finish_section_until_everything_is_submitted(client):
    att = new_attempt(client)
    r = client.post(f"/api/attempts/{att}/finish-section")
    assert r.status_code == 409 and r.json()["error"] == "not_all_submitted"
    st = client.get(f"/api/attempts/{att}").json()
    assert st["canFinish"] is False and len(st["unsubmitted"]) == 25
    for q in st["questions"][:-1]:
        client.put(f"/api/attempts/{att}/answers/{q['id']}", json={"value": "A"})
    assert client.post(f"/api/attempts/{att}/finish-section").status_code == 409            # one still open
    client.put(f"/api/attempts/{att}/answers/{st['questions'][-1]['id']}", json={"value": "A"})
    clock.advance(600)
    assert client.get(f"/api/attempts/{att}").json()["canFinish"] is True


def test_early_finish_unlocks_next_section_now_and_locks_the_old_one(client):
    att = new_attempt(client)
    answer_all(client, att)
    clock.advance(600)                                                                         # finished with 20 minutes to spare
    st = client.post(f"/api/attempts/{att}/finish-section").json()
    now = clock.now()
    assert st["currentSection"] == 1 and st["sections"][0]["status"] == "finalized"
    assert abs(st["sections"][1]["startedAt"] - now) < 5 and abs(st["sections"][1]["deadline"] - (now + 900)) < 5       # new window starts now
    assert client.put(f"/api/attempts/{att}/answers/oa01-mcq-01", json={"value": "A"}).status_code == 403    # cannot go back
    clock.advance(100000)
    r = client.get(f"/api/attempts/{att}/results").json()
    assert r["sections"][0]["score"] == 400 and r["sections"][0]["finishedEarly"] is True
    assert 590 <= r["sections"][0]["timeSpentSeconds"] <= 620


def test_end_test_after_last_section_completes_attempt(client):
    att = new_attempt(client)
    goto_section(client, att, 5)
    st = client.get(f"/api/attempts/{att}").json()
    assert st["isLastSection"] is True and st["canFinish"] is False
    assert client.post(f"/api/attempts/{att}/finish-section").status_code == 409
    answer_all(client, att)
    done = client.post(f"/api/attempts/{att}/finish-section").json()
    assert done["status"] == "completed" and done["currentSection"] is None
    assert client.get(f"/api/attempts/{att}/results").json()["sections"][5]["score"] == 260


def test_finish_after_deadline_is_rejected_by_state_machine(client):
    att = new_attempt(client)
    answer_all(client, att)
    clock.advance(1801)                                    # section already expired and auto-transitioned
    r = client.post(f"/api/attempts/{att}/finish-section")
    assert r.status_code == 409 and r.json()["error"] == "not_all_submitted"      # applies to the NEW (apt) section; nothing skipped


# 16, 17 ------------------------------------------------------- secrecy & results
FORBIDDEN = ["referenceSolution", "hiddenTests", "correctOptionId", "\"explanation\"", "\"solution\"", "rubric", "dataSql"]


def test_no_solutions_during_attempt(client):
    att = new_attempt(client)
    for idx in range(6):
        st = goto_section(client, att, idx)
        blob = json.dumps(st)
        for bad in FORBIDDEN:
            assert bad not in blob, (idx, bad)
        assert client.get(f"/api/attempts/{att}/results").status_code == 403
    assert "referenceSolution" not in client.get("/api/assessments").text


def test_results_and_review_after_completion(client):
    att = new_attempt(client)
    client.put(f"/api/attempts/{att}/answers/oa01-mcq-01", json={"value": "A"})
    goto_section(client, att, 3)
    submit(client, att, "oa01-sql-01", ref("oa01", "oa01-sql-01"))
    clock.advance(100000)
    r = client.get(f"/api/attempts/{att}/results").json()
    assert r["max"] == 1800 and len(r["questions"]) == 61 and len(r["sections"]) == 6
    sql = next(q for q in r["questions"] if q["id"] == "oa01-sql-01")
    assert r["questions"][0]["explanation"] and sql["referenceSolution"] and sql["testsPassed"] == sql["testsTotal"] and sql["earned"] == 100
    assert r["topics"] and abs(r["percent"] - 100 * r["total"] / 1800) < 0.1


# 18 --------------------------------------------------------------- retake
def test_retake_creates_separate_attempt(client):
    a1 = new_attempt(client); clock.advance(10000)
    client.get(f"/api/attempts/{a1}")
    a2 = new_attempt(client)
    assert a1 != a2
    cards = {c["id"]: c for c in client.get("/api/assessments").json()}
    assert cards["oa01"]["attempts"] == 2 and cards["oa01"]["completedAttempts"] == 1 and cards["oa01"]["activeAttemptId"] == a2
    assert cards["oa03"]["level"] == "Medium" and cards["oa01"]["timing"]["totalSeconds"] == 8700
    assert client.get(f"/api/attempts/{a1}/results").status_code == 200


def test_bad_inputs(client):
    assert client.post("/api/attempts", json={"assessmentId": "nope", "profile": "standard"}).status_code == 404
    assert client.post("/api/attempts", json={"assessmentId": "oa01", "profile": "strict"}).status_code == 400
    assert client.get("/api/attempts/doesnotexist").status_code == 404
