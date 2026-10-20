"""Shared grading + serialisation library for the mock OA bank.

Used by (a) the generator in src/, (b) validate.py, and (c) as a reference
implementation of the grading rules the assessment website must follow.
Pure standard library + pandas/numpy.
"""
import copy
import json
import math
import signal
import sqlite3

import numpy as np
import pandas as pd

REL_TOL = 1e-6
ABS_TOL = 1e-9

# ----------------------------------------------------------------- pandas I/O
def dtype_label(s):
    if pd.api.types.is_bool_dtype(s):
        return "bool"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "datetime64[ns]"
    if pd.api.types.is_integer_dtype(s):
        return "Int64" if str(s.dtype) == "Int64" else "int64"
    if pd.api.types.is_float_dtype(s):
        return "float64"
    return "str"


def _cell(v, label):
    if v is None or v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if label == "datetime64[ns]":
        return pd.Timestamp(v).strftime("%Y-%m-%d %H:%M:%S")
    if label in ("int64", "Int64"):
        return int(v)
    if label == "float64":
        return float(v)
    if label == "bool":
        return bool(v)
    return str(v)


def df_to_json(df):
    cols = list(df.columns)
    labels = {c: dtype_label(df[c]) for c in cols}
    data = [[_cell(df[c].iloc[i], labels[c]) for c in cols] for i in range(len(df))]
    return {"columns": cols, "dtypes": labels, "data": data}


def json_to_df(obj):
    cols, labels, data = obj["columns"], obj["dtypes"], obj["data"]
    out = {}
    for j, c in enumerate(cols):
        vals = [row[j] for row in data]
        lab = labels[c]
        if lab == "int64":
            out[c] = pd.Series(vals, dtype="int64")
        elif lab == "Int64":
            out[c] = pd.Series(vals, dtype="Int64")
        elif lab == "float64":
            out[c] = pd.Series([np.nan if v is None else v for v in vals], dtype="float64")
        elif lab == "bool":
            out[c] = pd.Series(vals, dtype="bool")
        elif lab == "datetime64[ns]":
            out[c] = pd.Series(pd.to_datetime(vals) if vals else [], dtype="datetime64[ns]").astype("datetime64[ns]")
        else:
            out[c] = pd.Series(vals, dtype=str) if not vals else pd.Series(vals)
    return pd.DataFrame(out, columns=cols)


def _isnull(x):
    return x is None or x is pd.NA or x is pd.NaT or (isinstance(x, float) and math.isnan(x))


def compare_df(actual, expected_obj):
    """Return (ok, message). Index ignored; column names/order must match."""
    if not isinstance(actual, pd.DataFrame):
        return False, "return value is not a DataFrame"
    exp_cols = expected_obj["columns"]
    if list(actual.columns) != exp_cols:
        return False, f"columns {list(actual.columns)} != {exp_cols}"
    data = expected_obj["data"]
    if len(actual) != len(data):
        return False, f"row count {len(actual)} != {len(data)}"
    actual = actual.reset_index(drop=True)
    for j, c in enumerate(exp_cols):
        lab = expected_obj["dtypes"][c]
        ev = [row[j] for row in data]
        av = list(actual[c])
        for i, (a, e) in enumerate(zip(av, ev)):
            if _isnull(a) or e is None:
                if _isnull(a) and e is None:
                    continue
                return False, f"col {c} row {i}: {a!r} vs {e!r}"
            if lab in ("int64", "Int64", "float64"):
                try:
                    ok = math.isclose(float(a), float(e), rel_tol=REL_TOL, abs_tol=ABS_TOL)
                except Exception:
                    ok = False
            elif lab == "bool":
                ok = isinstance(a, (bool, np.bool_)) and bool(a) == e
            elif lab == "datetime64[ns]":
                ok = pd.Timestamp(a) == pd.Timestamp(e)
            else:
                ok = str(a) == e
            if not ok:
                return False, f"col {c} row {i}: {a!r} vs {e!r}"
    return True, "ok"


def run_pandas(source, fn, inputs, params):
    ns = {}
    exec(source, ns)
    kwargs = {k: json_to_df(v) for k, v in inputs.items()}
    kwargs.update(copy.deepcopy(params))
    return ns[fn](**kwargs)


# ------------------------------------------------------------------------ SQL
def _norm_cell(v):
    return v


def _cells_equal(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=1e-6)
    return a == b


def rows_equal(actual, expected, order_matters=True):
    if len(actual) != len(expected):
        return False
    if not order_matters:
        key = lambda r: tuple((0, "") if x is None else (1, str(round(x, 6) if isinstance(x, float) else x)) for x in r)
        actual, expected = sorted(actual, key=key), sorted(expected, key=key)
    for ra, re_ in zip(actual, expected):
        if len(ra) != len(re_) or not all(_cells_equal(a, b) for a, b in zip(ra, re_)):
            return False
    return True


def sql_connect(schema_sql, data_sql):
    conn = sqlite3.connect(":memory:")
    conn.executescript(schema_sql)
    conn.executescript(data_sql)
    conn.commit()
    return conn


def schema_snapshot(conn):
    return sorted(r[0] or "" for r in conn.execute("SELECT sql FROM sqlite_master"))


def run_sql_select(schema_sql, data_sql, query):
    conn = sql_connect(schema_sql, data_sql)
    conn.execute("PRAGMA query_only=ON")
    cur = conn.execute(query)
    cols = [d[0] for d in cur.description]
    rows = [list(r) for r in cur.fetchall()]
    conn.close()
    return {"columns": cols, "rows": rows}


def run_sql_update(schema_sql, data_sql, query, check_queries):
    conn = sql_connect(schema_sql, data_sql)
    before = schema_snapshot(conn)
    conn.executescript(query)
    out = {"schemaUnchanged": schema_snapshot(conn) == before}
    for cq in check_queries:
        cur = conn.execute(cq["sql"])
        out[cq["id"]] = {"columns": [d[0] for d in cur.description], "rows": [list(r) for r in cur.fetchall()]}
    conn.close()
    return out


def grade_sql_test(q, test, query):
    try:
        if q["subtype"] == "select":
            got = run_sql_select(q["schemaSql"], test["dataSql"], query)
            exp = test["expected"]
            if [c.lower() for c in got["columns"]] != [c.lower() for c in exp["columns"]]:
                return False, "column names differ"
            return rows_equal(got["rows"], exp["rows"], q["orderMatters"]), "rows"
        got = run_sql_update(q["schemaSql"], test["dataSql"], query, q["checkQueries"])
        if not got["schemaUnchanged"]:
            return False, "schema modified"
        for cq in q["checkQueries"]:
            if not rows_equal(got[cq["id"]]["rows"], test["expected"][cq["id"]]["rows"], True):
                return False, f"table state differs ({cq['id']})"
        return True, "ok"
    except Exception as e:  # syntax errors etc. score zero on this test
        return False, f"error: {e}"


# ------------------------------------------------------------------------ DSA
class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def norm_out(x):
    if isinstance(x, (list, tuple)):
        return [norm_out(i) for i in x]
    if isinstance(x, np.generic):
        return x.item()
    return x


def run_dsa(source, fn, args, timeout=10):
    ns = {}
    exec(source, ns)
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(timeout)
    try:
        return norm_out(ns[fn](**copy.deepcopy(args)))
    finally:
        signal.alarm(0)


def values_equal(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
    return a == b


# -------------------------------------------------------------- generic score
def grade_question(q, candidate):
    """Return (earned_marks, per_test_results). `candidate` is query / source code.

    Score = marks * (sum of weights of passed tests) / (sum of all weights).
    Public and hidden tests are both scored; a crash or timeout fails that test only.
    """
    tests = q["publicTests"] + q["hiddenTests"]
    total = sum(t["weight"] for t in tests)
    got, res = 0.0, []
    for t in tests:
        try:
            if q["type"] == "sql":
                ok, msg = grade_sql_test(q, t, candidate)
            elif q["type"] == "pandas":
                out = run_pandas(candidate, q["functionName"], t["inputs"], t.get("params", {}))
                ok, msg = compare_df(out, t["expected"])
            else:
                out = run_dsa(candidate, q["functionName"], t["input"], q.get("timeLimitSecondsPerTest", 2) * 3)
                ok, msg = values_equal(out, t["expected"]), "value"
        except BaseException as e:  # noqa
            ok, msg = False, f"{type(e).__name__}: {e}"
        res.append((t["id"], ok, msg))
        if ok:
            got += t["weight"]
    return round(q["marks"] * got / total, 2), res
