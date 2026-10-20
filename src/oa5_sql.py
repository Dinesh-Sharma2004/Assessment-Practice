import random
from datetime import datetime, timedelta
from fractions import Fraction
from builder import sql_question
from oa1_sql import _half

SCHEMA = """CREATE TABLE ModelRuns (
  run_id     INTEGER PRIMARY KEY,
  model_name TEXT NOT NULL,
  version    TEXT NOT NULL,
  trained_at TEXT NOT NULL,            -- 'YYYY-MM-DD'
  threshold  REAL NOT NULL             -- score >= threshold means "flagged"
);
CREATE TABLE Predictions (
  prediction_id INTEGER PRIMARY KEY,
  run_id        INTEGER NOT NULL REFERENCES ModelRuns(run_id),
  entity_id     INTEGER NOT NULL,
  scored_at     TEXT NOT NULL,         -- 'YYYY-MM-DD HH:MM:SS'
  score         REAL,                  -- NULL when scoring failed
  UNIQUE (run_id, entity_id)
);
CREATE TABLE GroundTruthLabels (
  entity_id  INTEGER PRIMARY KEY,
  label      INTEGER NOT NULL CHECK (label IN (0,1)),
  labeled_at TEXT NOT NULL
);
CREATE TABLE AlertActions (
  action_id     INTEGER PRIMARY KEY,
  prediction_id INTEGER NOT NULL REFERENCES Predictions(prediction_id),
  action        TEXT NOT NULL CHECK (action IN ('OPEN','ESCALATED','DISMISSED','CLOSED')),
  actioned_at   TEXT NOT NULL,
  analyst       TEXT NOT NULL
);"""
TABLES = [
 {"name": "ModelRuns", "description": "One row per trained/deployed model run.", "columns": [
   {"name": "run_id", "type": "INTEGER", "description": "Primary key"}, {"name": "model_name", "type": "TEXT", "description": "Model family"},
   {"name": "version", "type": "TEXT", "description": "Version label"}, {"name": "trained_at", "type": "TEXT", "description": "'YYYY-MM-DD'"},
   {"name": "threshold", "type": "REAL", "description": "Decision threshold: score >= threshold is flagged"}]},
 {"name": "Predictions", "description": "Scores produced by a run; at most one per (run, entity).", "columns": [
   {"name": "prediction_id", "type": "INTEGER", "description": "Primary key"}, {"name": "run_id", "type": "INTEGER", "description": "FK to ModelRuns"},
   {"name": "entity_id", "type": "INTEGER", "description": "Scored entity"}, {"name": "scored_at", "type": "TEXT", "description": "'YYYY-MM-DD HH:MM:SS'"},
   {"name": "score", "type": "REAL", "description": "Model score; NULL if scoring failed"}]},
 {"name": "GroundTruthLabels", "description": "Eventually-known true outcome per entity (may be missing).", "columns": [
   {"name": "entity_id", "type": "INTEGER", "description": "Primary key"}, {"name": "label", "type": "INTEGER", "description": "1 = positive, 0 = negative"},
   {"name": "labeled_at", "type": "TEXT", "description": "'YYYY-MM-DD'"}]},
 {"name": "AlertActions", "description": "Analyst actions taken on predictions.", "columns": [
   {"name": "action_id", "type": "INTEGER", "description": "Primary key"}, {"name": "prediction_id", "type": "INTEGER", "description": "FK to Predictions"},
   {"name": "action", "type": "TEXT", "description": "'OPEN','ESCALATED','DISMISSED','CLOSED'"}, {"name": "actioned_at", "type": "TEXT", "description": "'YYYY-MM-DD HH:MM:SS'"},
   {"name": "analyst", "type": "TEXT", "description": "Analyst name"}]},
]
RUNS = [(1, "risk-gbm", "1.0", "2025-01-10", 0.50), (2, "risk-gbm", "1.1", "2025-02-10", 0.60), (3, "risk-nn", "0.9", "2025-03-10", 0.40), (4, "risk-nn", "1.0", "2025-04-10", 0.70)]


def gen(seed, n_runs=3, n_ent=25, p_null=0.08, p_label=0.85, p_act=0.6):
    r = random.Random(seed)
    runs = RUNS[:n_runs]
    base = datetime(2025, 5, 1, 8)
    preds, pid = [], 1
    for run in runs:
        for e in range(1, n_ent + 1):
            if r.random() < 0.8:
                t = base + timedelta(minutes=r.randrange(0, 5000))
                preds.append((pid, run[0], e, t.strftime("%Y-%m-%d %H:%M:%S"), None if r.random() < p_null else round(r.random(), 2))); pid += 1
    labels = [(e, int(r.random() < 0.35), "2025-06-01") for e in range(1, n_ent + 1) if r.random() < p_label]
    acts, aid = [], 1
    for p in preds:
        k = 0
        while r.random() < p_act and k < 3:
            acts.append((aid, p[0], r.choice(["OPEN", "OPEN", "ESCALATED", "DISMISSED", "CLOSED"]), p[3], r.choice(["ana", "raj", "mei"]))); aid += 1; k += 1
    return {"ModelRuns": runs, "Predictions": preds, "GroundTruthLabels": labels, "AlertActions": acts}


def F(x): return Fraction(str(x))

def guard_q1(d):
    thr = {r[0]: r[4] for r in d["ModelRuns"]}; by = {}
    for p in d["Predictions"]:
        if p[4] is not None: by.setdefault(p[1], []).append(p)
    for rid, v in by.items():
        fl = sum(1 for p in v if p[4] >= thr[rid])
        if _half(Fraction(fl, len(v)), 4) or _half(sum(F(p[4]) for p in v) / len(v), 4): return False
    return True

def guard_q2(d):
    thr = {r[0]: r[4] for r in d["ModelRuns"]}; lab = {l[0]: l[1] for l in d["GroundTruthLabels"]}; c = {}
    for p in d["Predictions"]:
        if p[4] is None or p[2] not in lab: continue
        k = c.setdefault(p[1], [0, 0, 0, 0]); hi = p[4] >= thr[p[1]]
        k[(0 if hi else 2) + (0 if lab[p[2]] == 1 else 1)] += 1   # tp, fp, fn, tn
    for tp, fp, fn, tn in c.values():
        if tp + fp and _half(Fraction(tp, tp + fp), 4): return False
        if tp + fn and _half(Fraction(tp, tp + fn), 4): return False
    return True

def guard_q3(d):
    thr = {r[0]: r[4] for r in d["ModelRuns"]}
    return not any(p[4] is not None and F(p[4]) == F(thr[p[1]]) + F("0.2") for p in d["Predictions"])

def pick(guard, seed0, **kw):
    for s in range(seed0, seed0 + 800):
        d = gen(s, **kw)
        if guard(d): return d
    raise RuntimeError

M1 = {"ModelRuns": RUNS,
      "Predictions": [(1, 1, 1, "2025-05-01 09:00:00", 0.90), (2, 1, 2, "2025-05-01 09:01:00", 0.50), (3, 1, 3, "2025-05-01 09:02:00", 0.20), (4, 1, 4, "2025-05-01 09:03:00", None),
                      (5, 2, 1, "2025-05-02 09:00:00", 0.65), (6, 2, 2, "2025-05-02 09:01:00", 0.30), (7, 2, 3, "2025-05-02 09:02:00", 0.75), (8, 2, 5, "2025-05-02 09:03:00", 0.10),
                      (9, 3, 1, "2025-05-03 09:00:00", 0.45), (10, 3, 2, "2025-05-03 09:01:00", 0.55), (11, 3, 3, "2025-05-03 09:02:00", 0.95)],
      "GroundTruthLabels": [(1, 1, "2025-06-01"), (2, 0, "2025-06-01"), (3, 1, "2025-06-01"), (5, 0, "2025-06-01")],
      "AlertActions": [(1, 1, "OPEN", "2025-05-01 10:00:00", "ana"), (2, 2, "OPEN", "2025-05-01 10:00:00", "ana"), (3, 5, "OPEN", "2025-05-02 10:00:00", "raj"), (4, 5, "DISMISSED", "2025-05-02 11:00:00", "mei"),
                       (5, 7, "OPEN", "2025-05-02 10:00:00", "raj"), (6, 7, "CLOSED", "2025-05-02 12:00:00", "raj"), (7, 3, "OPEN", "2025-05-01 10:00:00", "ana"), (8, 10, "OPEN", "2025-05-03 10:00:00", "mei"),
                       (9, 11, "OPEN", "2025-05-03 10:00:00", "mei"), (10, 11, "ESCALATED", "2025-05-03 12:00:00", "mei"), (11, 9, "OPEN", "2025-05-03 10:00:00", "ana"), (12, 4, "OPEN", "2025-05-01 10:00:00", "ana")]}
M2 = {"ModelRuns": RUNS[:3],
      "Predictions": [(1, 1, 7, "2025-05-01 09:00:00", 0.50), (2, 1, 8, "2025-05-01 09:01:00", 0.49), (3, 1, 9, "2025-05-01 09:02:00", 0.51), (4, 2, 7, "2025-05-02 09:00:00", 0.60), (5, 2, 8, "2025-05-02 09:01:00", 0.80),
                      (6, 2, 9, "2025-05-02 09:02:00", 0.10)],
      "GroundTruthLabels": [(7, 1, "2025-06-01"), (8, 1, "2025-06-01"), (9, 0, "2025-06-01")],
      "AlertActions": [(1, 3, "OPEN", "2025-05-01 10:00:00", "ana"), (2, 1, "OPEN", "2025-05-01 10:00:00", "ana"), (3, 5, "OPEN", "2025-05-02 10:00:00", "ana"), (4, 4, "OPEN", "2025-05-02 10:00:00", "ana")]}
EMPTYQ = {"ModelRuns": RUNS[:2], "Predictions": [(1, 1, 1, "2025-05-01 09:00:00", None)], "GroundTruthLabels": [], "AlertActions": []}
ONLYNEG = {"ModelRuns": RUNS[:2], "Predictions": [(1, 1, 1, "2025-05-01 09:00:00", 0.1), (2, 1, 2, "2025-05-01 09:00:00", 0.2), (3, 2, 1, "2025-05-01 09:00:00", 0.9), (4, 2, 2, "2025-05-01 09:00:00", 0.3)],
           "GroundTruthLabels": [(1, 0, "2025-06-01"), (2, 0, "2025-06-01")], "AlertActions": [(1, 3, "OPEN", "2025-05-01 10:00:00", "ana")]}


def build():
    qs = []
    q1_sets = [("Sample data from the statement", M1), ("Second sample (score equal to threshold counts as flagged)", M2), ("Runs without usable scores", EMPTYQ),
               ("Single-class flagged / not flagged", ONLYNEG), ("Randomised", pick(guard_q1, 100, n_runs=4)), ("Randomised larger", pick(guard_q1, 300, n_runs=4, n_ent=60, p_null=0.2))]
    ref1 = """SELECT r.run_id, r.model_name, r.version,
       COUNT(p.score) AS n_predictions,
       COALESCE(SUM(CASE WHEN p.score >= r.threshold THEN 1 ELSE 0 END), 0) AS n_flagged,
       CASE WHEN COUNT(p.score) = 0 THEN 0.0
            ELSE ROUND(1.0 * SUM(CASE WHEN p.score >= r.threshold THEN 1 ELSE 0 END) / COUNT(p.score), 4) END AS flag_rate,
       ROUND(AVG(p.score), 4) AS avg_score
FROM ModelRuns r
LEFT JOIN Predictions p ON p.run_id = r.run_id
GROUP BY r.run_id, r.model_name, r.version
ORDER BY r.run_id;"""
    qs.append(sql_question("oa05-sql-01", "select", 200, "Flag Rate per Model Run",
"""MLOps wants a monitoring table for every model run, including runs that produced no usable predictions. Use `ModelRuns` and `Predictions`.

For **every** run return:

`run_id, model_name, version, n_predictions, n_flagged, flag_rate, avg_score`

* `n_predictions` – predictions of the run with a **non-NULL** `score`
* `n_flagged` – those with `score >= threshold` (the run's `threshold`); `0` if none
* `flag_rate` – `n_flagged / n_predictions` rounded to 4 decimals, or `0.0` when `n_predictions = 0`
* `avg_score` – average non-NULL score rounded to 4 decimals (`NULL` when there is none)

Sort by `run_id`.""",
        TABLES[:2], SCHEMA, q1_sets,
        "SELECT r.run_id, r.model_name, r.version, COUNT(p.prediction_id) AS n_predictions, 0 AS n_flagged, 0.0 AS flag_rate, NULL AS avg_score\nFROM ModelRuns r\nJOIN Predictions p ON p.run_id = r.run_id\nGROUP BY r.run_id, r.model_name, r.version;",
        ref1, "Columns, in order: run_id, model_name, version, n_predictions, n_flagged, flag_rate, avg_score. One row per run, ordered by run_id.",
        ["INNER JOIN drops runs without predictions (LEFT JOIN is required).", "COUNT(score) vs COUNT(*) separates NULL scores.", "Division-by-zero guard for empty runs."],
        "LEFT JOIN keeps runs without predictions. COUNT(p.score) ignores NULL scores; the flagged count uses a conditional SUM (COALESCE turns the NULL sum of an empty group into 0). A CASE guards the division. AVG ignores NULLs and returns NULL for an empty group.",
        ["LEFT JOIN", "conditional aggregation", "NULL handling"], "medium"))
    q2_sets = [("Sample data from the statement", M1), ("Second sample with threshold ties", M2), ("No labelled predictions (empty result)", EMPTYQ),
               ("Run with only negatives: precision defined, recall undefined (NULL)", ONLYNEG), ("Randomised", pick(guard_q2, 500, n_runs=4)), ("Randomised larger", pick(guard_q2, 700, n_runs=4, n_ent=70))]
    ref2 = """SELECT r.run_id,
       SUM(CASE WHEN p.score >= r.threshold AND g.label = 1 THEN 1 ELSE 0 END) AS tp,
       SUM(CASE WHEN p.score >= r.threshold AND g.label = 0 THEN 1 ELSE 0 END) AS fp,
       SUM(CASE WHEN p.score <  r.threshold AND g.label = 1 THEN 1 ELSE 0 END) AS fn,
       SUM(CASE WHEN p.score <  r.threshold AND g.label = 0 THEN 1 ELSE 0 END) AS tn,
       ROUND(1.0 * SUM(CASE WHEN p.score >= r.threshold AND g.label = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN p.score >= r.threshold THEN 1 ELSE 0 END), 0), 4) AS precision,
       ROUND(1.0 * SUM(CASE WHEN p.score >= r.threshold AND g.label = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN g.label = 1 THEN 1 ELSE 0 END), 0), 4) AS recall
FROM Predictions p
JOIN ModelRuns r         ON r.run_id = p.run_id
JOIN GroundTruthLabels g ON g.entity_id = p.entity_id
WHERE p.score IS NOT NULL
GROUP BY r.run_id
ORDER BY r.run_id;"""
    qs.append(sql_question("oa05-sql-02", "select", 150, "Confusion Matrix per Run",
"""Evaluate each run against the ground truth. Using `Predictions`, `GroundTruthLabels` and `ModelRuns`, consider only predictions with a **non-NULL** score whose `entity_id` has a label. A prediction is *positive* when `score >= threshold`.

For every run with at least one such prediction return:

`run_id, tp, fp, fn, tn, precision, recall`

* `tp` – positive predictions with `label = 1`; `fp` – positive with `label = 0`; `fn` – negative predictions with `label = 1`; `tn` – negative with `label = 0`
* `precision = tp / (tp + fp)` and `recall = tp / (tp + fn)`, each rounded to 4 decimals, or `NULL` when the denominator is 0

Sort by `run_id`. (All four counts are integers, `0` when empty.)""",
        [TABLES[0], TABLES[1], TABLES[2]], SCHEMA, q2_sets,
        "SELECT r.run_id, 0 AS tp, 0 AS fp, 0 AS fn, 0 AS tn, NULL AS precision, NULL AS recall\nFROM Predictions p\nJOIN ModelRuns r ON r.run_id = p.run_id\nJOIN GroundTruthLabels g ON g.entity_id = p.entity_id\nGROUP BY r.run_id;",
        ref2, "Columns, in order: run_id, tp, fp, fn, tn, precision, recall. Order: run_id.",
        ["Conditional aggregation with the run-specific threshold.", "NULLIF protects against division by zero; precision/recall NULL when undefined.", "Unlabelled and NULL-score predictions are excluded."],
        "Join predictions to the run (threshold) and labels, then count the four confusion cells with conditional SUMs. NULLIF(denominator, 0) turns a zero denominator into NULL so the division returns NULL instead of an error.",
        ["conditional aggregation", "joins", "metrics"], "medium"))
    q3_sets = [("Sample data from the statement", M1), ("Second sample", M2), ("No actions", EMPTYQ), ("Dismissed predictions are protected", ONLYNEG),
               ("Randomised", pick(guard_q3, 900, n_runs=4, n_ent=40)), ("Randomised larger", pick(guard_q3, 1100, n_runs=4, n_ent=80, p_act=0.7))]
    ref3 = """UPDATE AlertActions
SET action = 'ESCALATED'
WHERE action = 'OPEN'
  AND prediction_id IN (SELECT p.prediction_id
                        FROM Predictions p
                        JOIN ModelRuns r ON r.run_id = p.run_id
                        WHERE p.score >= r.threshold + 0.2)
  AND NOT EXISTS (SELECT 1 FROM AlertActions d
                  WHERE d.prediction_id = AlertActions.prediction_id AND d.action = 'DISMISSED');"""
    qs.append(sql_question("oa05-sql-03", "update", 100, "Escalate Confident Open Alerts",
"""Analysts should immediately escalate open alerts on very confident predictions.

Update `AlertActions` so that `action` becomes `'ESCALATED'` for every row with `action = 'OPEN'` that satisfies **both**:

* its prediction's `score` is at least `0.2` **above** the threshold of the prediction's run, i.e. `score >= threshold + 0.2` (predictions with NULL score never qualify);
* there is **no** `'DISMISSED'` row in `AlertActions` for the same `prediction_id`.

Rows with other actions, and all other tables and columns, must remain unchanged.""",
        TABLES, SCHEMA, q3_sets,
        "UPDATE AlertActions\nSET action = 'ESCALATED'\nWHERE action = 'OPEN'\n  AND 1 = 0;  -- TODO: confident prediction and no DISMISSED sibling",
        ref3, "Final contents of AlertActions, Predictions and ModelRuns must equal the expected post-update state.",
        ["IN-subquery over joined tables for the threshold condition.", "NOT EXISTS for the DISMISSED guard (NULL-safe)."],
        "The IN subquery finds predictions with score >= threshold + 0.2 (NULL scores never satisfy the comparison). NOT EXISTS excludes predictions that have any DISMISSED action; because DISMISSED rows are never modified by this UPDATE, evaluation order does not matter.",
        ["UPDATE", "IN subquery", "NOT EXISTS"], "medium",
        check_queries=[{"id": "actions", "sql": "SELECT * FROM AlertActions ORDER BY action_id"}, {"id": "preds", "sql": "SELECT * FROM Predictions ORDER BY prediction_id"},
                       {"id": "runs", "sql": "SELECT * FROM ModelRuns ORDER BY run_id"}]))
    return qs
