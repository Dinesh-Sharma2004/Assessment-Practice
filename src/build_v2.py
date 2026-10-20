"""Assembles the five v2 assessments (6 sections, difficulty ladder OA1 easy -> OA5 hardest)."""
import copy, json, os, random, re, sqlite3, sys
import builder as B
import oa_lib as L
import sql2, pandas2, dsa2, mcq_pool, gen_apt, gen_da, hints_mcq
import oa1_sql, oa2_sql, oa3_sql, oa4_sql, oa5_sql, oa1_py, oa2_py, oa3_py, oa4_py, oa5_py
from content_text import HINTS, WALK, EXPL

TOPIC = {"ML": "Machine Learning", "STAT": "Statistics and Probability", "AI": "Artificial Intelligence", "CS": "CS Fundamentals",
         "TEST": "Software Testing", "APT": "Aptitude", "DA": "Data Analysis"}
SEC_TITLE = {"mcq": "Section 1: CS Fundamentals, AI, ML, Statistics and Testing", "apt": "Section 2: Aptitude", "da": "Section 3: Data Analysis (charts and tables)",
             "sql": "Section 4: SQL", "pandas": "Section 5: Pandas", "dsa": "Section 6: Data Structures and Algorithms (Python)"}
KINDS = {"mcq": "concept", "apt": "aptitude", "da": "data-analysis"}
MARKS_MCQ = {"mcq": 16, "apt": 16, "da": 25}
SECTION_KEYS = ["mcq", "apt", "da", "sql", "pandas", "dsa"]
MINUTES = {1: dict(mcq=30, apt=15, da=20, sql=20, pandas=30, dsa=30), 2: dict(mcq=30, apt=15, da=20, sql=20, pandas=30, dsa=30),
           3: dict(mcq=25, apt=10, da=15, sql=25, pandas=30, dsa=30), 4: dict(mcq=20, apt=10, da=15, sql=25, pandas=30, dsa=40), 5: dict(mcq=20, apt=10, da=15, sql=25, pandas=30, dsa=40)}
TITLES = {1: ("OA 1 — Foundations", "Easy"), 2: ("OA 2 — Building Skills", "Easy to Medium"), 3: ("OA 3 — Core Practice", "Medium"),
          4: ("OA 4 — Advanced Practice", "Medium to Hard"), 5: ("OA 5 — Expert Challenge", "Hard")}
HINTS_ON = {1, 2, 3}


def mcq_items(oa, key, items, marks):
    out = []
    for i, m in enumerate(items, 1):
        qid = f"oa{oa:02d}-{key}-{i:02d}"
        rng = random.Random(qid)
        opts = m.wrongs[:]; rng.shuffle(opts)
        pos = (i * 7 + rng.randrange(4)) % 4
        opts.insert(pos, m.correct)
        q = {"id": qid, "type": "mcq", "kind": KINDS[key], "topic": TOPIC[m.topic], "topicCode": m.topic, "tags": m.tags, "difficulty": m.diff, "marks": marks,
             "statement": m.stmt, "options": [{"id": "ABCD"[k], "text": o} for k, o in enumerate(opts)], "solution": {"correctOptionId": "ABCD"[pos], "explanation": m.expl}}
        if hasattr(m, "charts"):
            q["charts"] = m.charts
        if oa in HINTS_ON:
            h = getattr(m, "hint", None) or hints_mcq.hint_for(m.stmt)
            assert h, (qid, m.stmt[:60])
            q["hints"] = [h]
        out.append(q)
    return out


def rename(q, new):
    old = q["id"]
    s = json.dumps(q)
    s = s.replace(f'"{old}"', f'"{new}"').replace(f'"{old}-pub-', f'"{new}-pub-').replace(f'"{old}-hid-', f'"{new}-hid-')
    return json.loads(s)


def set_marks(q, m):
    q["marks"] = m
    if "rubric" in q and isinstance(q["rubric"], dict):
        q["rubric"]["formula"] = re.sub(r"earned = [\d.]+ \*", f"earned = {m} *", q["rubric"]["formula"])


def sample_tables(q):
    c = sqlite3.connect(":memory:"); c.executescript(q["schemaSql"]); c.executescript(q["publicTests"][0]["dataSql"])
    out = []
    for t in q["tables"]:
        cur = c.execute(f"SELECT * FROM {t['name']}")
        out.append({"name": t["name"], "columns": [d[0] for d in cur.description], "rows": [list(r) for r in cur.fetchall()]})
    return out


def finish_coding(q, new_id, oa, pos, marks, diff, src_id):
    q = rename(q, new_id)
    set_marks(q, marks)
    q["difficulty"] = diff
    q["sourceId"] = src_id
    if src_id in WALK:
        q["walkthrough"] = WALK[src_id]
    if oa in HINTS_ON:
        q["hints"] = HINTS[src_id]
        assert len(q["hints"]) == 3, src_id
    if q["type"] == "sql":
        q["sampleTables"] = sample_tables(q)
        q["tableCount"] = len(q["tables"])
    if q["type"] == "dsa" and src_id in EXPL:
        for ex, steps in zip(q["examples"], EXPL[src_id]):
            ex["steps"] = steps
    if q["type"] == "dsa" and src_id == "oa01-dsa-01":
        q["examples"][0]["description"] = "Two different sums are equally close to the target"
        q["examples"][1]["description"] = "Sums 2 and 4 tie again; the smaller one wins"
    return q


# ---- source pools (rebuilt once)
_cache = {}


def src(name, builder_fn, key=None):
    if name not in _cache:
        _cache[name] = builder_fn()
    return _cache[name]


def pool_questions():
    P = {}
    for q in oa1_sql.build() + oa2_sql.build() + oa3_sql.build() + oa4_sql.build() + oa5_sql.build():
        P[q["id"]] = q
    for q in oa1_py.build_pandas() + oa2_py.build_pandas() + oa3_py.build_pandas() + oa4_py.build_pandas() + oa5_py.build_pandas():
        P[q["id"]] = q
    for q in oa1_py.build_dsa() + oa2_py.build_dsa() + oa3_py.build_dsa() + oa4_py.build_dsa() + oa5_py.build_dsa():
        P[q["id"]] = q
    for f in (sql2.build_n1, sql2.build_n2, sql2.build_n3, sql2.build_n4a, sql2.build_n4b, sql2.build_n4c):
        q = f(); P[q["id"]] = q
    for q in pandas2.build_oa1() + pandas2.build_oa2() + [pandas2.build_oa4_h1(), pandas2.build_oa5_h2()]:
        P[q["id"]] = q
    for q in dsa2.build():
        P[q["id"]] = q
    return P


PLAN = {  # (source id, marks, difficulty)
    1: dict(sql=[("n1", 100, "easy"), ("n2", 200, "easy")],
            pandas=[("e1", 60, "easy"), ("e2", 60, "easy"), ("e3", 60, "easy"), ("e4", 60, "easy"), ("e5", 60, "easy")],
            dsa=[("da", 100, "easy"), ("db", 160, "easy")]),
    2: dict(sql=[("n3", 100, "easy"), ("oa02-sql-01", 200, "medium")],
            pandas=[("m1", 60, "easy"), ("m2", 60, "easy"), ("oa01-pd-03", 60, "medium"), ("m3", 60, "medium"), ("oa02-pd-03", 60, "medium")],
            dsa=[("dc", 100, "easy"), ("oa03-dsa-01", 160, "medium")]),
    3: dict(sql=[("oa05-sql-01", 80, "medium"), ("oa02-sql-02", 100, "medium"), ("n4a", 120, "medium")],
            pandas=[("oa01-pd-01", 60, "medium"), ("oa05-pd-02", 60, "medium"), ("oa03-pd-03", 60, "medium"), ("oa04-pd-03", 60, "medium"), ("oa01-pd-02", 60, "medium")],
            dsa=[("oa01-dsa-01", 100, "medium"), ("oa02-dsa-01", 160, "medium")]),
    4: dict(sql=[("oa01-sql-01", 80, "medium"), ("oa05-sql-02", 100, "medium"), ("n4b", 120, "hard")],
            pandas=[("oa04-pd-01", 60, "medium"), ("oa03-pd-01", 60, "medium"), ("oa02-pd-01", 60, "medium"), ("oa05-pd-03", 60, "hard"), ("h1", 60, "hard")],
            dsa=[("oa01-dsa-02", 100, "medium"), ("oa03-dsa-02", 160, "hard")]),
    5: dict(sql=[("oa04-sql-01", 80, "hard"), ("oa04-sql-02", 100, "hard"), ("n4c", 120, "hard")],
            pandas=[("oa05-pd-01", 60, "hard"), ("oa03-pd-02", 60, "hard"), ("oa02-pd-02", 60, "hard"), ("oa04-pd-02", 60, "hard"), ("h2", 60, "hard")],
            dsa=[("oa05-dsa-02", 100, "hard"), ("oa05-dsa-01", 160, "hard")]),
}
SHORT = {"sql": "sql", "pandas": "pd", "dsa": "dsa"}


def build_oa(oa, POOL):
    sections = {}
    sections["mcq"] = mcq_items(oa, "mcq", mcq_pool.build_mcq(oa), MARKS_MCQ["mcq"])
    sections["apt"] = mcq_items(oa, "apt", gen_apt.build_aptitude(oa), MARKS_MCQ["apt"])
    sections["da"] = mcq_items(oa, "da", gen_da.build_da(oa), MARKS_MCQ["da"])
    for key in ("sql", "pandas", "dsa"):
        qs = []
        for i, (sid, marks, diff) in enumerate(PLAN[oa][key], 1):
            qs.append(finish_coding(copy.deepcopy(POOL[sid]), f"oa{oa:02d}-{SHORT[key]}-{i:02d}", oa, i, marks, diff, sid))
        sections[key] = qs
    mins = MINUTES[oa]
    secs = []
    for key in SECTION_KEYS:
        qs = sections[key]
        secs.append({"sectionId": f"oa{oa:02d}-{key}", "type": key, "title": SEC_TITLE[key], "questionCount": len(qs), "durationSeconds": mins[key] * 60,
                     "totalMarks": sum(q["marks"] for q in qs), "questions": qs})
    title, level = TITLES[oa]
    total_sec = sum(s["durationSeconds"] for s in secs)
    doc = {"schemaVersion": "2.0", "assessmentId": f"oa{oa:02d}", "title": f"{title} ({level})", "level": level,
           "description": f"{level} mock data-science internship assessment: CS/AI/ML/statistics/testing MCQs, aptitude, chart-based data analysis, SQL, pandas and DSA.",
           "disclaimer": "Independent practice material informed by publicly reported role requirements and general internship-assessment patterns. Not official Nasdaq questions.",
           "hintsEnabled": oa in HINTS_ON, "totalQuestions": sum(s["questionCount"] for s in secs), "totalMarks": sum(s["totalMarks"] for s in secs),
           "timing": {"standard": {"totalSeconds": total_sec, "sectionSeconds": {s["type"]: s["durationSeconds"] for s in secs}}},
           "revealPolicy": {"privateFields": ["questions[*].solution", "questions[*].hiddenTests"], "rule": "Never send private fields to the candidate before the whole attempt has finished."},
           "sections": secs}
    return doc


if __name__ == "__main__":
    POOL = pool_questions()
    for oa in range(1, 6):
        doc = build_oa(oa, POOL)
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"assessment-{oa:02d}.json")
        with open(path, "w") as f:
            json.dump(doc, f, separators=(",", ":"), ensure_ascii=False)
        print(path, doc["totalQuestions"], doc["totalMarks"], doc["timing"]["standard"]["totalSeconds"] // 60, "min", os.path.getsize(path) // 1024, "KB")
