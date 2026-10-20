"""Generator helpers: turn compact question definitions into schema-conformant JSON,
computing every expected output by *executing* the reference solution."""
import hashlib, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import oa_lib as L
import pandas as pd

MARKS = {"ML": 40, "STAT": 40, "AI": 40, "SQL": 20, "JAVA": 20, "OOP": 20, "TEST": 20, "EXCEL": 20, "FIN": 20}
ORDER = ["ML"] * 6 + ["STAT"] * 5 + ["AI"] * 4 + ["SQL"] * 2 + ["JAVA", "OOP", "TEST", "EXCEL", "FIN"]
TOPIC_NAME = {"ML": "Machine Learning", "STAT": "Statistics and Probability", "AI": "Artificial Intelligence",
              "SQL": "SQL/DBMS Concepts", "JAVA": "Core Java", "OOP": "Object-Oriented Programming",
              "TEST": "Software Testing", "EXCEL": "Excel", "FIN": "Financial Data / Data Quality"}
DEFAULT = {"mcq": 900, "sql": 900, "pandas": 900, "dsa": 1500}
EXTENDED = {"mcq": 1200, "sql": 1200, "pandas": 1200, "dsa": 1800}


def weights(n_pub, n_hid):
    return [round(30 / n_pub, 4)] * n_pub, [round(70 / n_hid, 4)] * n_hid


# ----------------------------------------------------------------------- MCQ
class MCQ:
    def __init__(self, topic, tags, diff, stmt, correct, wrongs, expl):
        assert len(wrongs) == 3, stmt[:50]
        self.topic, self.tags, self.diff, self.stmt = topic, tags, diff, stmt
        self.correct, self.wrongs, self.expl = correct, wrongs, expl


def build_mcqs(oa, items):
    order_idx = {}
    for t in ORDER:
        order_idx.setdefault(t, [m for m in items if m.topic == t])
    cnt = {t: ORDER.count(t) for t in set(ORDER)}
    for t, n in cnt.items():
        assert len(order_idx[t]) == n, f"{oa}: topic {t} has {len(order_idx[t])}, need {n}"
    out = []
    used = {t: 0 for t in cnt}
    for i, t in enumerate(ORDER, 1):
        m = order_idx[t][used[t]]; used[t] += 1
        qid = f"{oa}-mcq-{i:02d}"
        rng = random.Random(qid)
        opts = m.wrongs[:] ; rng.shuffle(opts)
        pos = (i * 7 + rng.randrange(4)) % 4
        opts.insert(pos, m.correct)
        letters = "ABCD"
        out.append({
            "id": qid, "type": "mcq", "topic": TOPIC_NAME[t], "topicCode": t, "tags": m.tags,
            "difficulty": m.diff, "marks": MARKS[t], "statement": m.stmt,
            "options": [{"id": letters[k], "text": o} for k, o in enumerate(opts)],
            "solution": {"correctOptionId": letters[pos], "explanation": m.expl},
        })
    return out


# ------------------------------------------------------------------------ SQL
def lit(v):
    if v is None: return "NULL"
    if isinstance(v, str): return "'" + v.replace("'", "''") + "'"
    return repr(v)


def inserts(data):
    parts = []
    for table, rows in data.items():
        for r in rows:
            parts.append(f"INSERT INTO {table} VALUES ({', '.join(lit(x) for x in r)});")
    return "\n".join(parts)


def sql_question(qid, subtype, marks, title, statement, tables, schema_sql, datasets, starter, reference,
                 output_spec, rubric_notes, explanation, tags, diff, check_queries=None, edge_cases=""):
    """datasets: list of (description, {table: rows}); first two are public, rest hidden."""
    assert len(datasets) >= 5, qid
    pub_n = 2
    wp, wh = weights(pub_n, len(datasets) - pub_n)
    tests = []
    q = {"id": qid, "type": "sql", "subtype": subtype, "title": title, "tags": tags, "difficulty": diff,
         "marks": marks, "dialect": "SQLite 3 (>= 3.25, window functions supported)", "statement": statement,
         "tables": tables, "schemaSql": schema_sql, "starterQuery": starter, "outputSpec": output_spec,
         "orderMatters": True, "gradingMode": "result_set" if subtype == "select" else "table_state",
         "checkQueries": check_queries or []}
    for k, (desc, data) in enumerate(datasets):
        data_sql = inserts(data)
        if subtype == "select":
            exp = L.run_sql_select(schema_sql, data_sql, reference)
        else:
            res = L.run_sql_update(schema_sql, data_sql, reference, q["checkQueries"])
            exp = {cq["id"]: res[cq["id"]] for cq in q["checkQueries"]}
        vis = k < pub_n
        tests.append({"id": f"{qid}-{'pub' if vis else 'hid'}-{(k if vis else k - pub_n) + 1}",
                      "visibility": "public" if vis else "hidden", "description": desc,
                      "weight": (wp if vis else wh)[0], "dataSql": data_sql, "expected": exp})
    q["publicTests"] = [t for t in tests if t["visibility"] == "public"]
    q["hiddenTests"] = [t for t in tests if t["visibility"] == "hidden"]
    q["sampleDataSql"] = q["publicTests"][0]["dataSql"]
    q["solution"] = {"referenceSolution": reference, "explanation": explanation}
    q["rubric"] = partial_rubric(marks, "SQL", rubric_notes)
    return q


def partial_rubric(marks, kind, notes):
    return {"scoring": "weighted_tests",
            "formula": f"earned = {marks} * (sum of weights of passed tests) / (sum of all test weights)",
            "publicWeightTotal": 30, "hiddenWeightTotal": 70,
            "rules": ["A submission that only compiles/executes without matching expected output earns 0 for that test.",
                      "A crash, syntax error or timeout fails only the affected test; remaining tests are still scored."] + notes}


# --------------------------------------------------------------------- pandas
def pandas_question(qid, marks, title, statement, fn, signature, starter, inputs_spec, datasets, reference,
                    output_spec, rubric_notes, explanation, tags, diff):
    """datasets: list of (description, {name: DataFrame}, params) ; first 2 public."""
    assert len(datasets) >= 5, qid
    pub_n = 2
    wp, wh = weights(pub_n, len(datasets) - pub_n)
    q = {"id": qid, "type": "pandas", "title": title, "tags": tags, "difficulty": diff, "marks": marks,
         "pandasVersion": ">=2.0 (tested on 2.x and 3.x)", "statement": statement, "functionName": fn,
         "functionSignature": signature, "starterCode": starter, "outputSpec": output_spec,
         "inputs": [{"name": n, "columns": [{"name": c, "dtype": d, "description": ds} for c, d, ds in cols],
                     "exampleRows": L.df_to_json(datasets[0][1][n].head(4))["data"]} for n, cols in inputs_spec.items()],
         "parameters": [{"name": k, "example": v} for k, v in (datasets[0][2] or {}).items()],
         "comparison": {"indexIgnored": True, "columnOrderMatters": True, "rowOrderMatters": True,
                        "floatRelTol": L.REL_TOL, "floatAbsTol": L.ABS_TOL,
                        "dtypePolicy": "Values compared by category: numeric (int/float interchangeable), bool, datetime, str; nulls (NaN/NaT/None/pd.NA) equal each other."}}
    tests = []
    for k, (desc, frames, params) in enumerate(datasets):
        inputs = {n: L.df_to_json(df) for n, df in frames.items()}
        out = L.run_pandas(reference, fn, inputs, params or {})
        vis = k < pub_n
        tests.append({"id": f"{qid}-{'pub' if vis else 'hid'}-{(k if vis else k - pub_n) + 1}",
                      "visibility": "public" if vis else "hidden", "description": desc,
                      "weight": (wp if vis else wh)[0], "inputs": inputs, "params": params or {},
                      "expected": L.df_to_json(out)})
    q["publicTests"] = [t for t in tests if t["visibility"] == "public"]
    q["hiddenTests"] = [t for t in tests if t["visibility"] == "hidden"]
    q["solution"] = {"referenceSolution": reference, "explanation": explanation}
    q["rubric"] = partial_rubric(marks, "pandas", rubric_notes)
    return q


# ------------------------------------------------------------------------ DSA
def dsa_question(qid, marks, title, statement, constraints, examples, fn, signature, starter, datasets, reference,
                 brute, rand_gen, complexity, rubric_notes, explanation, tags, diff, n_random=300):
    """datasets: list of (description, args). First 2 public. Verifies ref == brute on random small cases."""
    assert len(datasets) >= 6, qid
    rng = random.Random(qid)
    ns_ref, ns_br = {}, {}
    exec(reference, ns_ref); exec(brute, ns_br)
    f_ref, f_br = ns_ref[fn], ns_br[fn]
    import copy
    for _ in range(n_random):
        a = rand_gen(rng)
        r1, r2 = L.norm_out(f_ref(**copy.deepcopy(a))), L.norm_out(f_br(**copy.deepcopy(a)))
        assert L.values_equal(r1, r2), (qid, a, r1, r2)
    pub_n = 2
    wp, wh = weights(pub_n, len(datasets) - pub_n)
    ex_out = []
    for desc, args in examples:
        ex_out.append({"description": desc, "input": args, "output": L.run_dsa(reference, fn, args)})
    tests = []
    for k, (desc, args) in enumerate(datasets):
        out = L.run_dsa(reference, fn, args)
        vis = k < pub_n
        tests.append({"id": f"{qid}-{'pub' if vis else 'hid'}-{(k if vis else k - pub_n) + 1}",
                      "visibility": "public" if vis else "hidden", "description": desc,
                      "weight": (wp if vis else wh)[0], "input": args, "expected": out})
    q = {"id": qid, "type": "dsa", "title": title, "tags": tags, "difficulty": diff, "marks": marks,
         "language": "python3", "statement": statement, "constraints": constraints, "examples": ex_out,
         "functionName": fn, "functionSignature": signature, "starterCode": starter,
         "expectedComplexity": complexity, "timeLimitSecondsPerTest": 2,
         "publicTests": [t for t in tests if t["visibility"] == "public"],
         "hiddenTests": [t for t in tests if t["visibility"] == "hidden"],
         "solution": {"referenceSolution": reference, "explanation": explanation},
         "rubric": partial_rubric(marks, "DSA", rubric_notes + ["Tests include large inputs: a correct but O(n^2) solution passes the small tests and fails the performance tests (partial credit)."])}
    return q


# ------------------------------------------------------------------- assembly
def assemble(num, title, description, mcqs, sqls, pandass, dsas):
    oa = f"oa{num:02d}"
    assert len(mcqs) == 22 and len(sqls) == 3 and len(pandass) == 3 and len(dsas) == 2
    secs = []
    for sid, typ, stitle, qs in [("mcq", "mcq", "Section 1: Conceptual MCQs", mcqs), ("sql", "sql", "Section 2: SQL", sqls),
                                 ("pandas", "pandas", "Section 3: Pandas", pandass), ("dsa", "dsa", "Section 4: Data Structures & Algorithms (Python)", dsas)]:
        secs.append({"sectionId": f"{oa}-{sid}", "type": typ, "title": stitle, "questionCount": len(qs),
                     "defaultDurationSeconds": DEFAULT[sid], "extendedDurationSeconds": EXTENDED[sid],
                     "totalMarks": sum(q["marks"] for q in qs), "questions": qs})
    doc = {
        "schemaVersion": "1.0", "assessmentId": f"{oa}", "title": title, "description": description,
        "disclaimer": "Independent practice material informed by publicly reported role requirements and general internship-assessment patterns. Not official Nasdaq questions.",
        "totalQuestions": sum(s["questionCount"] for s in secs), "totalMarks": sum(s["totalMarks"] for s in secs),
        "timing": {"default": {"totalSeconds": sum(DEFAULT.values()), "sectionSeconds": DEFAULT},
                   "extended": {"totalSeconds": sum(EXTENDED.values()), "sectionSeconds": EXTENDED}},
        "revealPolicy": {"privateFields": ["questions[*].solution", "questions[*].hiddenTests"],
                         "rule": "Never send private fields to the candidate's browser; reveal solutions only after the whole attempt has been submitted or timed out."},
        "sections": secs,
    }
    assert doc["totalMarks"] == 2040 and doc["totalQuestions"] == 30, doc["totalMarks"]
    return doc


def write(doc, num):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"assessment-{num:02d}.json")
    with open(path, "w") as f:
        json.dump(doc, f, separators=(",", ":"), ensure_ascii=False)
    return path
