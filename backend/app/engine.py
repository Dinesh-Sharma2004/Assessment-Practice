"""Attempt state machine. The server clock and persisted absolute deadlines are the only authority."""
import json
import threading
import uuid

from . import bank, clock, db, execution
from .config import PROFILES, SECTIONS

_locks: dict[str, threading.RLock] = {}
_locks_guard = threading.Lock()


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def lock_for(aid: str) -> threading.RLock:
    with _locks_guard:
        return _locks.setdefault(aid, threading.RLock())


# ---------------------------------------------------------------- creation
def create_attempt(assessment_id: str, profile: str) -> str:
    doc = bank.get(assessment_id)
    if not doc:
        raise ApiError(404, "unknown_assessment", "No such assessment")
    if profile not in PROFILES:
        raise ApiError(400, "bad_profile", "Profile must be 'standard'")
    dur = bank.durations(doc, profile)
    aid, t = uuid.uuid4().hex, clock.now()
    with db.tx() as c:
        c.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,NULL)", (aid, assessment_id, profile, "active", 0, t))
        for i, key in enumerate(SECTIONS):
            first = i == 0
            c.execute("INSERT INTO sections VALUES (?,?,?,?,?,?,?,NULL,NULL)",
                      (aid, i, key, "active" if first else "locked", dur[key], t if first else None, t + dur[key] if first else None))
    return aid


# ------------------------------------------------------------ transitions
def _attempt(c, aid):
    a = c.execute("SELECT * FROM attempts WHERE id=?", (aid,)).fetchone()
    if not a:
        raise ApiError(404, "unknown_attempt", "No such attempt")
    return a


def sync(aid: str) -> None:
    """Applies every deadline that has passed (cascading if several did while the app was down)."""
    with lock_for(aid):
        while True:
            with db.read() as c:
                a = _attempt(c, aid)
                if a["status"] == "completed":
                    return
                s = c.execute("SELECT * FROM sections WHERE attempt_id=? AND idx=?", (aid, a["current_section"])).fetchone()
            if clock.now() < s["deadline"]:
                return
            _finalize_section(a, s, s["deadline"])


def _finalize_section(a, s, at):
    """Grades and freezes section `s`. `at` is the moment it ended: its deadline, or the time the candidate finished early."""
    doc = bank.get(a["assessment_id"])
    aid, key = a["id"], s["key"]
    graded = []                                     # grading happens outside the DB transaction (can take seconds)
    with db.read() as c:
        answers = {r["qid"]: r for r in c.execute("SELECT * FROM answers WHERE attempt_id=?", (aid,))}
        subs = {}
        for r in c.execute("SELECT * FROM submissions WHERE attempt_id=? ORDER BY id", (aid,)):
            subs[r["qid"]] = r                       # last one wins = latest valid submission before expiry
    for q in bank.section_questions(doc, key):
        graded.append(_grade_final(doc, q, answers.get(q["id"]), subs.get(q["id"])))
    total = sum(g["earned"] for g in graded)
    with db.tx() as c:
        cur = c.execute("SELECT status FROM sections WHERE attempt_id=? AND idx=?", (aid, s["idx"])).fetchone()
        if cur["status"] == "finalized":
            return
        for g in graded:
            c.execute("INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?)",
                      (aid, g["qid"], g["earned"], g["max"], g["attempted"], g["source"], json.dumps(g["detail"])))
        c.execute("UPDATE sections SET status='finalized', finalized_at=?, score=? WHERE attempt_id=? AND idx=?",
                  (at, round(total, 2), aid, s["idx"]))
        if s["idx"] == len(SECTIONS) - 1:
            c.execute("UPDATE attempts SET status='completed', current_section=NULL, completed_at=? WHERE id=?", (at, aid))
        else:
            n = s["idx"] + 1
            nxt = c.execute("SELECT duration FROM sections WHERE attempt_id=? AND idx=?", (aid, n)).fetchone()
            c.execute("UPDATE sections SET status='active', started_at=?, deadline=? WHERE attempt_id=? AND idx=?",
                      (at, at + nxt["duration"], aid, n))
            c.execute("UPDATE attempts SET current_section=? WHERE id=?", (n, aid))


def _grade_final(doc, q, ans, sub):
    base = {"qid": q["id"], "max": q["marks"], "earned": 0.0, "attempted": 0, "source": "none", "detail": {}}
    if q["type"] == "mcq":
        val = ans["value"] if ans else None
        if val:
            base.update(attempted=1, earned=float(q["marks"]) if val == q["solution"]["correctOptionId"] else 0.0,
                        source="answer", detail={"selected": val})
        return base
    if sub:
        d = json.loads(sub["detail"])
        base.update(attempted=1, earned=sub["earned"], source="submission", detail={**d, "code": sub["code"]})
        return base
    code = ans["value"] if ans else None
    if code and code.strip() and code.strip() != bank.starter(q).strip():     # auto-submit the final draft
        for _ in range(2):
            try:
                tests = execution.execute(doc, q, code, "full")
                base.update(attempted=1, earned=execution.score(q, tests), source="draft",
                            detail={"tests": tests, "code": code})
                return base
            except execution.RuntimeFailure as e:
                base["detail"] = {"gradingError": str(e), "code": code}
        base["attempted"] = 1
        base["source"] = "grading_error"
    return base


# --------------------------------------------------------------- queries
def _section_views(c, aid, now):
    out = []
    for s in c.execute("SELECT * FROM sections WHERE attempt_id=? ORDER BY idx", (aid,)):
        out.append({"index": s["idx"], "key": s["key"], "status": s["status"], "durationSeconds": s["duration"],
                    "startedAt": s["started_at"], "deadline": s["deadline"],
                    "remainingSeconds": max(0.0, s["deadline"] - now) if s["status"] == "active" else None})
    return out


def state(aid: str) -> dict:
    sync(aid)
    now = clock.now()
    with db.read() as c:
        a = _attempt(c, aid)
        doc = bank.get(a["assessment_id"])
        out = {"id": aid, "assessmentId": a["assessment_id"], "title": doc["title"], "profile": a["profile"], "status": a["status"], "hintsEnabled": doc["hintsEnabled"],
               "serverNow": now, "currentSection": a["current_section"], "totalMarks": doc["totalMarks"],
               "sections": _section_views(c, aid, now), "questions": [], "answers": {}}
        if a["status"] == "active":
            key = SECTIONS[a["current_section"]]
            qs = bank.section_questions(doc, key)
            out["questions"] = [bank.public_question(q) for q in qs]
            ids = [q["id"] for q in qs]
            for r in c.execute("SELECT * FROM answers WHERE attempt_id=?", (aid,)):
                if r["qid"] in ids:
                    out["answers"][r["qid"]] = {"value": r["value"], "review": bool(r["review"]), "visited": bool(r["visited"])}
            subs = {}
            for r in c.execute("SELECT qid, MAX(id) mid, COUNT(*) n FROM submissions WHERE attempt_id=? GROUP BY qid", (aid,)):
                if r["qid"] in ids:
                    subs[r["qid"]] = r["n"]
            out["submissionCounts"] = subs
            pending = _unsubmitted(c, aid, qs)
            out["unsubmitted"] = pending
            out["canFinish"] = not pending
            out["isLastSection"] = a["current_section"] == len(SECTIONS) - 1
    return out


def _unsubmitted(c, aid, qs):
    """Questions of the active section that are not yet submitted: MCQ-type = no option chosen, coding = no explicit submission."""
    answered = {r["qid"] for r in c.execute("SELECT qid FROM answers WHERE attempt_id=? AND value IS NOT NULL AND value != ''", (aid,))}
    submitted = {r["qid"] for r in c.execute("SELECT DISTINCT qid FROM submissions WHERE attempt_id=?", (aid,))}
    return [q["id"] for q in qs if (q["id"] not in answered if q["type"] == "mcq" else q["id"] not in submitted)]


def finish_section(aid):
    """Early finish: allowed only when every question of the active section has been submitted. Locks the section for good
    and starts the next one now (or ends the attempt after the last section)."""
    with lock_for(aid):
        sync(aid)
        with db.read() as c:
            a = _attempt(c, aid)
            if a["status"] != "active":
                raise ApiError(409, "attempt_finished", "This attempt has finished")
            s = c.execute("SELECT * FROM sections WHERE attempt_id=? AND idx=?", (aid, a["current_section"])).fetchone()
            doc = bank.get(a["assessment_id"])
            pending = _unsubmitted(c, aid, bank.section_questions(doc, s["key"]))
        if clock.now() >= s["deadline"]:
            raise ApiError(409, "section_closed", "The section deadline has passed")
        if pending:
            raise ApiError(409, "not_all_submitted", f"Submit all questions first ({len(pending)} remaining): {', '.join(pending[:5])}")
        _finalize_section(a, s, clock.now())
    return state(aid)


def _active_question(aid, qid):
    """Validates that qid belongs to the currently active, unexpired section; returns (attempt, doc, q)."""
    sync(aid)
    with db.read() as c:
        a = _attempt(c, aid)
        if a["status"] != "active":
            raise ApiError(409, "attempt_finished", "This attempt has finished")
        s = c.execute("SELECT * FROM sections WHERE attempt_id=? AND idx=?", (aid, a["current_section"])).fetchone()
    doc = bank.get(a["assessment_id"])
    idx, q = bank.find_question(doc, qid)
    if q is None:
        raise ApiError(404, "unknown_question", "No such question")
    if idx != a["current_section"]:
        raise ApiError(403, "section_locked", "That question is not in the active section")
    if clock.now() >= s["deadline"]:
        raise ApiError(409, "section_closed", "The section deadline has passed")
    return a, s, doc, q


_UNSET = object()


def save_answer(aid, qid, value=_UNSET, review=None, visited=None):
    with lock_for(aid):
        a, s, doc, q = _active_question(aid, qid)
        if value is not _UNSET and q["type"] == "mcq" and value is not None and value not in [o["id"] for o in q["options"]]:
            raise ApiError(400, "bad_option", "Invalid option")
        with db.tx() as c:
            if clock.now() >= s["deadline"]:
                raise ApiError(409, "section_closed", "The section deadline has passed")
            c.execute("INSERT OR IGNORE INTO answers(attempt_id,qid,updated_at) VALUES (?,?,?)", (aid, qid, clock.now()))
            if value is not _UNSET:
                c.execute("UPDATE answers SET value=?, updated_at=? WHERE attempt_id=? AND qid=?", (value, clock.now(), aid, qid))
            if review is not None:
                c.execute("UPDATE answers SET review=? WHERE attempt_id=? AND qid=?", (int(review), aid, qid))
            if visited is not None:
                c.execute("UPDATE answers SET visited=? WHERE attempt_id=? AND qid=?", (int(visited), aid, qid))
    return {"saved": True}


def run_public(aid, qid, code):
    a, s, doc, q = _active_question(aid, qid)
    if q["type"] == "mcq":
        raise ApiError(400, "not_code", "Not a coding question")
    try:
        tests = execution.execute(doc, q, code, "public")
    except execution.RuntimeFailure as e:
        raise ApiError(500, "runtime_failure", str(e))
    if clock.now() >= s["deadline"]:
        raise ApiError(409, "section_closed", "The section deadline passed while the code was running")
    return {"tests": execution.present(tests, False), "passed": sum(t["passed"] for t in tests), "total": len(tests)}


def submit(aid, qid, code):
    a, s, doc, q = _active_question(aid, qid)
    if q["type"] == "mcq":
        raise ApiError(400, "not_code", "Not a coding question")
    try:
        tests = execution.execute(doc, q, code, "full")
    except execution.RuntimeFailure as e:
        raise ApiError(500, "runtime_failure", str(e) + " Your submission was NOT recorded.")
    with lock_for(aid):
        with db.tx() as c:
            if clock.now() >= s["deadline"]:       # grading finished too late: result is discarded
                raise ApiError(409, "section_closed", "The section deadline passed before grading finished; this submission was not counted")
            earned = execution.score(q, tests)
            c.execute("INSERT INTO submissions(attempt_id,qid,code,submitted_at,earned,detail) VALUES (?,?,?,?,?,?)",
                      (aid, qid, code, clock.now(), earned, json.dumps({"tests": tests})))
            c.execute("INSERT OR IGNORE INTO answers(attempt_id,qid,updated_at) VALUES (?,?,?)", (aid, qid, clock.now()))
            c.execute("UPDATE answers SET value=?, updated_at=? WHERE attempt_id=? AND qid=?", (code, clock.now(), aid, qid))
    pub = [t for t in tests if t["visibility"] == "public"]
    return {"earned": earned, "marks": q["marks"], "publicPassed": sum(t["passed"] for t in pub), "publicTotal": len(pub),
            "hiddenPassed": sum(t["passed"] for t in tests if t["visibility"] == "hidden"),
            "hiddenTotal": sum(t["visibility"] == "hidden" for t in tests), "tests": execution.present(tests, False)}


# --------------------------------------------------------------- results
def results(aid: str) -> dict:
    sync(aid)
    with db.read() as c:
        a = _attempt(c, aid)
        if a["status"] != "completed":
            raise ApiError(403, "not_finished", "Results and solutions are available only after the whole attempt has finished")
        doc = bank.get(a["assessment_id"])
        res = {r["qid"]: r for r in c.execute("SELECT * FROM results WHERE attempt_id=?", (aid,))}
        ans = {r["qid"]: r for r in c.execute("SELECT * FROM answers WHERE attempt_id=?", (aid,))}
        secs = list(c.execute("SELECT * FROM sections WHERE attempt_id=? ORDER BY idx", (aid,)))
    sections, questions, tags = [], [], {}
    for s in secs:
        qs = bank.section_questions(doc, s["key"])
        mx = sum(q["marks"] for q in qs)
        att = sum(res[q["id"]]["attempted"] for q in qs)
        last = max([ans[q["id"]]["updated_at"] for q in qs if q["id"] in ans and ans[q["id"]]["updated_at"]] or [s["started_at"]])
        sections.append({"key": s["key"], "title": bank.sections(doc)[s["key"]]["title"], "score": s["score"], "max": mx,
                         "percent": round(100 * s["score"] / mx, 1), "attempted": att, "unanswered": len(qs) - att,
                         "reviewed": sum(bool(ans[q["id"]]["review"]) for q in qs if q["id"] in ans),
                         "timeAllottedSeconds": s["duration"], "timeSpentSeconds": round(max(0.0, s["finalized_at"] - s["started_at"])),
                         "finishedEarly": s["finalized_at"] < s["deadline"] - 0.5,
                         "lastActivitySeconds": round(max(0.0, last - s["started_at"]), 1)})
        for q in qs:
            r = res[q["id"]]
            d = json.loads(r["detail"] or "{}")
            item = {"id": q["id"], "section": s["key"], "type": q["type"], "title": q.get("title") or q["statement"][:90],
                    "statement": q["statement"], "marks": q["marks"], "earned": r["earned"], "attempted": bool(r["attempted"]),
                    "source": r["source"], "tags": q["tags"], "review": bool(ans[q["id"]]["review"]) if q["id"] in ans else False,
                    "explanation": q["solution"]["explanation"], "rubric": q.get("rubric")}
            if q["type"] == "mcq":
                item.update(options=q["options"], selected=d.get("selected"), correct=q["solution"]["correctOptionId"], kind=q["kind"], charts=q.get("charts"))
            else:
                tests = d.get("tests", [])
                allt = {t["id"]: t for t in q["publicTests"] + q["hiddenTests"]}
                item.update(referenceSolution=q["solution"]["referenceSolution"], submittedCode=d.get("code"), gradingError=d.get("gradingError"),
                            testsPassed=sum(t["passed"] for t in tests), testsTotal=len(tests) or len(allt),
                            tests=[{"id": t["id"], "visibility": t["visibility"], "passed": t["passed"], "kind": t["kind"],
                                    "weight": t["weight"], "description": allt[t["id"]]["description"]} for t in tests],
                            sampleExpected=q["publicTests"][0].get("expected"))
            questions.append(item)
            for tg in q["tags"]:
                e = tags.setdefault(tg, [0.0, 0.0, 0])
                e[0] += r["earned"]; e[1] += q["marks"]; e[2] += 1
    total = sum(s["score"] for s in sections)
    topics = sorted(({"tag": k, "earned": round(v[0], 1), "max": v[1], "percent": round(100 * v[0] / v[1], 1), "questions": v[2]} for k, v in tags.items()),
                    key=lambda x: (-x["percent"], x["tag"]))
    return {"attemptId": aid, "assessmentId": doc["assessmentId"], "title": doc["title"], "profile": a["profile"], "total": round(total, 2),
            "max": doc["totalMarks"], "percent": round(100 * total / doc["totalMarks"], 1), "completedAt": a["completed_at"],
            "sections": sections, "topics": topics, "questions": questions}


def dashboard() -> list[dict]:
    out = []
    with db.read() as c:
        for aid, doc in bank.banks().items():
            rows = list(c.execute("SELECT id, status, profile, created_at FROM attempts WHERE assessment_id=? ORDER BY created_at", (aid,)))
            scores = []
            for r in rows:
                if r["status"] == "completed":
                    sc = c.execute("SELECT SUM(score) s FROM sections WHERE attempt_id=?", (r["id"],)).fetchone()["s"]
                    scores.append((r["id"], sc))
            active = [r["id"] for r in rows if r["status"] == "active"]
            out.append({"id": aid, "title": doc["title"], "description": doc["description"], "difficulty": bank.difficulty_label(doc),
                        "questionCount": doc["totalQuestions"], "totalMarks": doc["totalMarks"],
                        "level": doc.get("level"), "hintsEnabled": doc["hintsEnabled"],
                        "sections": [{"key": s["type"], "title": s["title"], "questions": s["questionCount"], "marks": s["totalMarks"], "seconds": s["durationSeconds"]} for s in doc["sections"]],
                        "timing": {"totalSeconds": doc["timing"]["standard"]["totalSeconds"], "sectionSeconds": doc["timing"]["standard"]["sectionSeconds"]},
                        "attempts": len(rows), "completedAttempts": len(scores), "activeAttemptId": active[-1] if active else None,
                        "latestScore": scores[-1][1] if scores else None, "latestAttemptId": scores[-1][0] if scores else None,
                        "bestScore": max((s for _, s in scores), default=None)})
    return out
