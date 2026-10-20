"""Validator for the v2 banks.   python validate.py [assessment-0N.json ...]
Checks structure, marks, timing, difficulty ladder, hints, tables-per-SQL, non-overlap, and re-executes every reference solution + starter."""
import glob, hashlib, json, re, sys
from collections import Counter
import oa_lib as L

COUNTS = {1: dict(mcq=25, apt=15, da=12, sql=2, pandas=5, dsa=2), 2: dict(mcq=25, apt=15, da=12, sql=2, pandas=5, dsa=2), 3: dict(mcq=25, apt=15, da=12, sql=3, pandas=5, dsa=2),
          4: dict(mcq=25, apt=15, da=12, sql=3, pandas=5, dsa=2), 5: dict(mcq=25, apt=15, da=12, sql=3, pandas=5, dsa=2)}
MARKS = dict(mcq=400, apt=240, da=300, sql=300, pandas=300, dsa=260)
MIN = {1: [30, 15, 20, 20, 30, 30], 2: [30, 15, 20, 20, 30, 30], 3: [25, 10, 15, 25, 30, 30], 4: [20, 10, 15, 25, 30, 40], 5: [20, 10, 15, 25, 30, 40]}
SQL_TABLES = {1: [1, 2], 2: [1, 2], 3: [2, 3, 4], 4: [2, 3, 4], 5: [2, 3, 4]}
ORDER = ["mcq", "apt", "da", "sql", "pandas", "dsa"]
SCORE = {"easy": 1, "medium": 2, "hard": 3}
errors = []


def err(m):
    errors.append(m); print("  ERROR:", m)


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def check(path):
    d = json.load(open(path)); n = int(d["assessmentId"][2:]); print(path)
    ids = set(); stats = {}
    if [s["type"] for s in d["sections"]] != ORDER: err("section order")
    if [s["durationSeconds"] // 60 for s in d["sections"]] != MIN[n]: err("timing minutes")
    if d["timing"]["standard"]["totalSeconds"] != sum(MIN[n]) * 60: err("timing total")
    if d["totalMarks"] != 1800 or d["totalQuestions"] != sum(COUNTS[n].values()): err("totals")
    for s in d["sections"]:
        k = s["type"]; qs = s["questions"]
        if len(qs) != COUNTS[n][k] or s["questionCount"] != len(qs): err(f"{k} count {len(qs)}")
        if sum(q["marks"] for q in qs) != MARKS[k] or s["totalMarks"] != MARKS[k]: err(f"{k} marks")
        stats[k] = sum(SCORE[q["difficulty"]] for q in qs) / len(qs)
        tags0 = Counter()
        for q in qs:
            if q["id"] in ids: err("dup id " + q["id"])
            ids.add(q["id"])
            if d["hintsEnabled"] != (n <= 3): err("hintsEnabled")
            if d["hintsEnabled"] and not q.get("hints"): err("missing hints " + q["id"])
            if not d["hintsEnabled"] and q.get("hints"): err("unexpected hints " + q["id"])
            if q["type"] == "mcq":
                if [o["id"] for o in q["options"]] != list("ABCD") or len({o["text"] for o in q["options"]}) != 4: err("options " + q["id"])
                if q["solution"]["correctOptionId"] not in "ABCD" or not q["solution"]["explanation"]: err("key " + q["id"])
                if k == "da":
                    if not q.get("charts"): err("no chart " + q["id"])
                tags0[q["tags"][0]] += 1
            else:
                if len(q["publicTests"]) < 2 or len(q["hiddenTests"]) < 3: err("tests " + q["id"])
                if abs(sum(t["weight"] for t in q["publicTests"] + q["hiddenTests"]) - 100) > 0.01: err("weights " + q["id"])
                if not q.get("walkthrough") and q["type"] != "dsa": err("walkthrough " + q["id"])
                if q["type"] == "dsa" and not all(e.get("steps") for e in q["examples"]): err("dsa explanation " + q["id"])
                if d["hintsEnabled"] and len(q["hints"]) != 3: err("coding hints " + q["id"])
                if q["type"] == "sql":
                    ref = q["solution"]["referenceSolution"].lower()
                    used = [t["name"] for t in q["tables"] if re.search(r"\b" + t["name"].lower() + r"\b", ref)]
                    if len(used) != SQL_TABLES[n][len(used) and [qq["id"] for qq in qs].index(q["id"])]: err(f"{q['id']} uses {len(used)} tables")
                    if not q.get("sampleTables"): err("sampleTables " + q["id"])
                e, res = L.grade_question(q, q["solution"]["referenceSolution"])
                if e != q["marks"]: err(f"reference fails {q['id']}: {[r for r in res if not r[1]][:2]}")
                st = q.get("starterQuery") or q.get("starterCode")
                if L.grade_question(q, st)[0] >= q["marks"]: err("starter passes everything " + q["id"])
        if k in ("mcq", "apt"):      # non-overlap: no two questions in an OA share the same primary concept tag
            dup = [t for t, c in tags0.items() if c > 1]
            if dup and k == "apt": err(f"{k}: repeated aptitude family {dup}")
            if dup and k == "mcq": print(f"  note: {k} shares primary tag(s) {dup}")
        if k == "da":                      # no two questions on the same chart may be the same kind of question
            by = {}
            for q in qs:
                tpl = re.sub(r"\b[A-Z][A-Za-z0-9]*\b|\d+(\.\d+)?", "#", q["statement"])
                key = (json.dumps(q["charts"], sort_keys=True), tpl)
                if key in by: err(f"same kind of question twice on one chart: {q['id']} / {by[key]}")
                by[key] = q["id"]
        print(f"  {k:7s} questions={len(qs):2d} marks={sum(q['marks'] for q in qs):4d} difficulty-score={stats[k]:.2f}")
    return d, stats


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob("assessment-0?.json"))
    docs, allstats = [], {}
    for f in files:
        d, st = check(f); docs.append(d); allstats[d["assessmentId"]] = st
    # difficulty ladder across OAs (only when all five are present)
    if len(docs) == 5:
        for k in ORDER:
            seq = [allstats[f"oa0{i}"][k] for i in range(1, 6)]
            if any(b < a for a, b in zip(seq, seq[1:])) or seq[0] >= seq[-1]: err(f"difficulty ladder violated for {k}: {seq}")
        tot = [sum(allstats[f"oa0{i}"].values()) for i in range(1, 6)]
        if any(b <= a for a, b in zip(tot, tot[1:])): err(f"overall ladder {tot}")
        print("difficulty per OA:", [round(t / 6, 2) for t in tot])
    # non-overlap: statements, coding sources and test data are unique across all assessments, and inside each one
    seen = {}
    for d in docs:
        for s in d["sections"]:
            for q in s["questions"]:
                key = norm(q["statement"]) + (json.dumps(q.get("charts"), sort_keys=True) if q.get("charts") else "")   # chart questions: wording + data
                if key in seen: err(f"overlapping statement {q['id']} / {seen[key]}")
                seen[key] = q["id"]
        srcs = [q["sourceId"] for s in d["sections"] for q in s["questions"] if "sourceId" in q]
        if len(srcs) != len(set(srcs)): err("repeated coding source in " + d["assessmentId"])
    allsrc = Counter(q["sourceId"] for d in docs for s in d["sections"] for q in s["questions"] if "sourceId" in q)
    if any(c > 1 for c in allsrc.values()): err(f"coding source reused across OAs: {[k for k,c in allsrc.items() if c>1]}")
    titles = Counter(q.get("title") for d in docs for s in d["sections"] for q in s["questions"] if q["type"] != "mcq")
    if any(c > 1 for c in titles.values()): err("duplicate coding titles")
    print("FAILED" if errors else "ALL CHECKS PASSED", len(errors))
    sys.exit(1 if errors else 0)
