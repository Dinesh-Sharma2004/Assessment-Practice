import random
import numpy as np
import pandas as pd
from builder import pandas_question, dsa_question

NAN = float("nan")

# ============================== PANDAS ==============================
def vals(v):
    return pd.DataFrame({"value": pd.Series(v, dtype="float64")})

def rnd_vals(seed, n, mu=0.0, sd=1.0, p_nan=0.03):
    r = random.Random(seed)
    return vals([NAN if r.random() < p_nan else round(r.gauss(mu, sd), 3) for _ in range(n)])

REF_P1 = '''import numpy as np
import pandas as pd

def psi_table(train, live, n_bins):
    t = train["value"].dropna()
    l = live["value"].dropna()
    qs = np.linspace(0, 1, n_bins + 1)[1:-1]
    inner = sorted(set(t.quantile(qs).tolist()))
    edges = [-np.inf] + inner + [np.inf]
    tc = pd.cut(t, bins=edges, right=True).value_counts(sort=False)
    lc = pd.cut(l, bins=edges, right=True).value_counts(sort=False)
    train_pct = (tc / len(t)).clip(lower=1e-4).to_numpy()
    live_pct = (lc / len(l)).clip(lower=1e-4).to_numpy()
    out = pd.DataFrame({"bin": np.arange(len(edges) - 1, dtype="int64"), "train_pct": train_pct, "live_pct": live_pct})
    out["psi_component"] = (out["live_pct"] - out["train_pct"]) * np.log(out["live_pct"] / out["train_pct"])
    return out
'''

def pr(rows):
    return pd.DataFrame(rows, columns=["ts", "y_true", "score"]).astype({"y_true": "int64", "score": "float64"})

def rand_pr(seed, n=60, days=4, p_nan=0.05):
    r = random.Random(seed); rows = []
    for _ in range(n):
        y = int(r.random() < 0.3)
        s = min(1, max(0, round(r.gauss(0.65 if y else 0.35, 0.2), 2)))
        rows.append((f"2025-06-0{r.randrange(1, days + 1)} {r.randrange(0, 24):02d}:{r.randrange(0, 60):02d}:00", y, NAN if r.random() < p_nan else s))
    r.shuffle(rows)
    return pr(rows)

REF_P2 = '''import pandas as pd

def daily_metrics(preds, threshold):
    df = preds.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.dropna(subset=["score"])
    df["date"] = df["ts"].dt.normalize()
    pos = df["score"] >= threshold
    y = df["y_true"] == 1
    df["tp"] = (pos & y).astype("int64")
    df["fp"] = (pos & ~y).astype("int64")
    df["fn"] = (~pos & y).astype("int64")
    df["tn"] = (~pos & ~y).astype("int64")
    df["sq"] = (df["score"] - df["y_true"]) ** 2
    g = df.groupby("date", as_index=False).agg(n=("score", "size"), tp=("tp", "sum"), fp=("fp", "sum"), fn=("fn", "sum"), tn=("tn", "sum"), brier=("sq", "mean"))
    g["precision"] = (g["tp"] / (g["tp"] + g["fp"])).where((g["tp"] + g["fp"]) > 0)
    g["recall"] = (g["tp"] / (g["tp"] + g["fn"])).where((g["tp"] + g["fn"]) > 0)
    den = 2 * g["tp"] + g["fp"] + g["fn"]
    g["f1"] = (2 * g["tp"] / den).where(den > 0)
    return g[["date", "n", "tp", "fp", "fn", "tn", "precision", "recall", "f1", "brier"]].sort_values("date").reset_index(drop=True)
'''

def rand_feat(seed, n=80, shift=None, null=None):
    r = random.Random(seed); shift = shift or {}; null = null or {}
    cols = {"age": [], "income": [], "utilisation": [], "tenure": []}
    for _ in range(n):
        cols["age"].append(r.gauss(40 + shift.get("age", 0), 8))
        cols["income"].append(r.gauss(5000 + shift.get("income", 0), 1200))
        cols["utilisation"].append(r.random() * (1 + shift.get("utilisation", 0)))
        cols["tenure"].append(r.gauss(6, 2))
    df = pd.DataFrame(cols)
    for c, p in null.items():
        df.loc[[i for i in range(n) if r.random() < p], c] = NAN
    df["segment"] = [r.choice(["a", "b"]) for _ in range(n)]
    return df

REF_P3 = '''import pandas as pd
import numpy as np

def feature_drift(ref, cur):
    feats = [c for c in ref.select_dtypes("number").columns if c in cur.columns and pd.api.types.is_numeric_dtype(cur[c])]
    rows = []
    for f in feats:
        sd = ref[f].std(ddof=1)
        shift = (cur[f].mean() - ref[f].mean()) / sd if pd.notna(sd) and sd > 0 else np.nan
        rows.append({"feature": f, "ref_mean": ref[f].mean(), "cur_mean": cur[f].mean(), "std_shift": shift,
                     "null_rate_ref": ref[f].isna().mean(), "null_rate_cur": cur[f].isna().mean()})
    out = pd.DataFrame(rows, columns=["feature", "ref_mean", "cur_mean", "std_shift", "null_rate_ref", "null_rate_cur"])
    out["drift_flag"] = ((out["std_shift"].abs() > 0.5).fillna(False) | ((out["null_rate_cur"] - out["null_rate_ref"]).abs() > 0.1)).astype(bool)
    out["_k"] = out["std_shift"].abs()
    out = out.sort_values(["_k", "feature"], ascending=[False, True], na_position="last").drop(columns="_k")
    return out.reset_index(drop=True)
'''

def build_pandas():
    qs = []
    d1 = [("Sample: shifted live distribution, 4 bins", {"train": vals([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]), "live": vals([1, 1, 2, 2, 3, 5, 8, 9, 10, 11, 12, 12, 12, 13])}, {"n_bins": 4}),
          ("Heavy ties collapse quantile edges; NaN ignored", {"train": vals([1, 1, 1, 1, 1, 1, 2, 3, NAN, 5]), "live": vals([1, 1, 4, 5, 5, NAN])}, {"n_bins": 5}),
          ("Single bin", {"train": vals([3, 4, 5]), "live": vals([9, 9])}, {"n_bins": 1}),
          ("Live data entirely above training range (empty bins floored)", {"train": rnd_vals(11, 200), "live": rnd_vals(12, 100, 6, 1)}, {"n_bins": 10}),
          ("Same distribution", {"train": rnd_vals(13, 500), "live": rnd_vals(14, 300)}, {"n_bins": 8}),
          ("Moderate shift", {"train": rnd_vals(15, 400, 0, 1), "live": rnd_vals(16, 400, 0.6, 1.3)}, {"n_bins": 6})]
    qs.append(pandas_question("oa05-pd-01", 150, "Population Stability Table",
"""Implement `psi_table(train, live, n_bins)` which builds the per-bin Population Stability Index table for one numeric feature (column `value` in both frames).

1. Drop NaN values from each frame.
2. Take the quantiles of `train.value` at probabilities `linspace(0, 1, n_bins + 1)[1:-1]` (pandas default linear interpolation) and remove duplicate edges. These interior edges define bins `(-inf, e1], (e1, e2], ..., (ek, +inf)` – right-closed.
3. For both samples compute the share of values in each bin (**include empty bins**) and floor each share at `1e-4`.
4. `psi_component = (live_pct - train_pct) * ln(live_pct / train_pct)`.

Return `bin` (0-based int64), `train_pct`, `live_pct`, `psi_component` – one row per bin in order, default index. The PSI is the sum of `psi_component`.""",
        "psi_table", "def psi_table(train: pd.DataFrame, live: pd.DataFrame, n_bins: int) -> pd.DataFrame",
        "import numpy as np\nimport pandas as pd\n\ndef psi_table(train: pd.DataFrame, live: pd.DataFrame, n_bins: int) -> pd.DataFrame:\n    # TODO\n    pass\n",
        {"train": [("value", "float64", "Reference (training) feature values; may contain NaN")], "live": [("value", "float64", "Production feature values; may contain NaN")]},
        d1, REF_P1, "Columns [bin int64, train_pct float64, live_pct float64, psi_component float64]; float tolerance rel 1e-6.",
        ["Quantile edge de-duplication is visible in the tie test.", "Empty bins must appear and be floored at 1e-4."],
        "Use Series.quantile for the interior edges, deduplicate with set/sorted, bin with pd.cut(right=True) using -inf/+inf outer edges; value_counts(sort=False) keeps empty categories. Floor with clip(lower=1e-4) before applying the PSI formula.",
        ["PSI", "binning", "drift"], "hard"))
    p1 = pr([("2025-06-01 09:00:00", 1, 0.90), ("2025-06-01 10:00:00", 0, 0.80), ("2025-06-01 11:00:00", 1, 0.30), ("2025-06-01 12:00:00", 0, 0.10), ("2025-06-02 09:00:00", 0, 0.20),
             ("2025-06-02 23:59:59", 0, 0.50), ("2025-06-02 10:00:00", 1, NAN), ("2025-06-03 00:00:00", 1, 0.5)])
    d2 = [("Sample: threshold tie counts as positive; day with no positives", {"preds": p1}, {"threshold": 0.5}), ("Higher threshold", {"preds": p1}, {"threshold": 0.85}),
          ("All scores missing (empty result)", {"preds": pr([("2025-06-01 00:00:00", 1, NAN)])}, {"threshold": 0.5}),
          ("Randomised", {"preds": rand_pr(21)}, {"threshold": 0.5}), ("Randomised larger", {"preds": rand_pr(22, 200, 6)}, {"threshold": 0.4}), ("Randomised strict", {"preds": rand_pr(23, 120, 5)}, {"threshold": 0.7})]
    qs.append(pandas_question("oa05-pd-02", 150, "Daily Monitoring Metrics",
"""Implement `daily_metrics(preds, threshold)` for a monitoring pipeline.

1. Parse `ts`; drop rows with a missing `score`; define `date` as `ts` normalised to midnight.
2. A row is predicted *positive* when `score >= threshold`. `y_true` is 0/1.
3. For each `date` compute: `n` (rows), `tp`, `fp`, `fn`, `tn` (ints), `precision = tp/(tp+fp)`, `recall = tp/(tp+fn)`, `f1 = 2*tp/(2*tp+fp+fn)` (each `NaN` when its denominator is 0) and `brier` = mean of `(score - y_true)^2`.
4. Return `date, n, tp, fp, fn, tn, precision, recall, f1, brier` sorted by date, default index.""",
        "daily_metrics", "def daily_metrics(preds: pd.DataFrame, threshold: float) -> pd.DataFrame",
        "import pandas as pd\n\ndef daily_metrics(preds: pd.DataFrame, threshold: float) -> pd.DataFrame:\n    df = preds.copy()\n    # TODO\n    return df\n",
        {"preds": [("ts", "str", "Timestamp text 'YYYY-MM-DD HH:MM:SS'"), ("y_true", "int64", "Ground truth label 0/1"), ("score", "float64", "Model score; may be NaN")]},
        d2, REF_P2, "Columns [date datetime64, n int64, tp int64, fp int64, fn int64, tn int64, precision float64, recall float64, f1 float64, brier float64].",
        ["Undefined ratios must be NaN, not 0.", "Midnight (00:00:00) belongs to the new day."],
        "Create boolean masks for the four confusion cells, aggregate them per normalised date with named aggregation and compute ratios with .where(denominator > 0) so undefined metrics are NaN. Brier is a mean of squared errors.",
        ["groupby", "metrics", "monitoring"], "medium"))
    ref0 = rand_feat(31, 100)
    d3 = [("Sample: shifted age and income, utilisation null-rate jump", {"ref": ref0, "cur": rand_feat(32, 90, {"age": 6, "income": 900}, {"utilisation": 0.4})}, {}),
          ("No drift", {"ref": rand_feat(33, 120), "cur": rand_feat(34, 120)}, {}),
          ("Constant reference column and missing column in current", {"ref": pd.DataFrame({"a": [1.0, 1.0, 1.0], "b": [1.0, 2.0, 3.0], "c": [0.0, 1.0, 2.0]}), "cur": pd.DataFrame({"a": [2.0, 2.0], "b": [5.0, 6.0]})}, {}),
          ("Large shifts everywhere", {"ref": rand_feat(35, 80), "cur": rand_feat(36, 80, {"age": 10, "income": 2500, "utilisation": 2.0})}, {}),
          ("All-NaN current column", {"ref": rand_feat(37, 60), "cur": rand_feat(38, 60, null={"tenure": 1.0})}, {}),
          ("Randomised nulls", {"ref": rand_feat(39, 90, null={"age": 0.05}), "cur": rand_feat(40, 90, {"tenure": 1}, {"age": 0.3, "income": 0.12})}, {})]
    qs.append(pandas_question("oa05-pd-03", 100, "Feature Drift Report",
"""Implement `feature_drift(ref, cur)` comparing a reference and a current sample.

Features = columns of `ref` with a numeric dtype that also exist in `cur` as numeric columns (keep `ref`'s column order for ties, see sorting). For each feature compute:

* `ref_mean`, `cur_mean` (NaN ignored), `std_shift = (cur_mean - ref_mean) / ref_std` where `ref_std` is the sample standard deviation (ddof = 1) of the reference column; `NaN` if `ref_std` is 0 or NaN
* `null_rate_ref`, `null_rate_cur` – fraction of NaN values
* `drift_flag` – `True` if `abs(std_shift) > 0.5` **or** `abs(null_rate_cur - null_rate_ref) > 0.1` (a NaN `std_shift` never triggers the first condition)

Return `feature, ref_mean, cur_mean, std_shift, null_rate_ref, null_rate_cur, drift_flag` sorted by `abs(std_shift)` descending (NaN last), ties by `feature` ascending; default index.""",
        "feature_drift", "def feature_drift(ref: pd.DataFrame, cur: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\nimport numpy as np\n\ndef feature_drift(ref: pd.DataFrame, cur: pd.DataFrame) -> pd.DataFrame:\n    # TODO\n    pass\n",
        {"ref": [("age", "float64", "Numeric feature (example)"), ("income", "float64", "Numeric feature (example)"), ("utilisation", "float64", "Numeric feature (example)"), ("tenure", "float64", "Numeric feature (example)"), ("segment", "str", "Non-numeric column to ignore")],
         "cur": [("age", "float64", "Same features as ref (some may be missing)"), ("income", "float64", ""), ("utilisation", "float64", ""), ("tenure", "float64", ""), ("segment", "str", "Ignored")]},
        d3, REF_P3, "Columns [feature str, ref_mean float64, cur_mean float64, std_shift float64, null_rate_ref float64, null_rate_cur float64, drift_flag bool].",
        ["Non-numeric and absent columns are skipped.", "Zero-variance references yield NaN shift (and no crash)."],
        "Select numeric columns of ref that also exist in cur, compute per-column statistics, assemble a result frame and derive the flag from vectorised comparisons (NaN comparisons are False). Sort by a helper key with na_position='last'.",
        ["data quality", "drift", "reshaping"], "medium"))
    return qs

# ============================== DSA ==============================
REF_D1 = '''from typing import List

def count_valid_portfolios(costs: List[int], conflicts: List[List[int]], budget: int, max_rules: int) -> int:
    n = len(costs)
    bad = [0] * n
    for a, b in conflicts:
        bad[a] |= 1 << b
        bad[b] |= 1 << a
    order = sorted(range(n), key=lambda i: costs[i])      # cheapest first enables early exit
    count = 0

    def go(pos, chosen_mask, spent, size):
        nonlocal count
        for k in range(pos, n):
            i = order[k]
            if spent + costs[i] > budget:
                break                                    # all later rules cost at least as much
            if bad[i] & chosen_mask:
                continue
            if size + 1 > max_rules:
                break
            count += 1                                   # the subset chosen_mask + i is valid
            go(k + 1, chosen_mask | (1 << i), spent + costs[i], size + 1)

    go(0, 0, 0, 0)
    return count
'''
BR_D1 = '''def count_valid_portfolios(costs, conflicts, budget, max_rules):
    n = len(costs); c = 0
    for mask in range(1, 1 << n):
        idx = [i for i in range(n) if mask >> i & 1]
        if len(idx) > max_rules or sum(costs[i] for i in idx) > budget: continue
        s = set(idx)
        if any(a in s and b in s for a, b in conflicts): continue
        c += 1
    return c
'''
def gen_d1(r):
    n = r.randrange(1, 9)
    return {"costs": [r.randrange(1, 10) for _ in range(n)],
            "conflicts": [[a, b] for a in range(n) for b in range(a + 1, n) if r.random() < 0.2],
            "budget": r.randrange(1, 40), "max_rules": r.randrange(1, n + 1)}

REF_D2 = '''import heapq
from typing import List

def min_cost_with_waiver(n: int, edges: List[List[int]], src: int, dst: int) -> int:
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
    INF = float("inf")
    dist = [[INF, INF] for _ in range(n)]          # dist[node][used_waiver]
    dist[src][0] = 0
    heap = [(0, src, 0)]
    while heap:
        d, u, used = heapq.heappop(heap)
        if d > dist[u][used]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v][used]:
                dist[v][used] = d + w
                heapq.heappush(heap, (d + w, v, used))
            if not used and d < dist[v][1]:
                dist[v][1] = d
                heapq.heappush(heap, (d, v, 1))
    best = min(dist[dst])
    return -1 if best == INF else best
'''
BR_D2 = '''def min_cost_with_waiver(n, edges, src, dst):
    INF = float("inf")
    D = [[INF] * n for _ in range(n)]
    for i in range(n): D[i][i] = 0
    for u, v, w in edges: D[u][v] = min(D[u][v], w)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if D[i][k] + D[k][j] < D[i][j]: D[i][j] = D[i][k] + D[k][j]
    best = D[src][dst]
    for u, v, w in edges:
        best = min(best, D[src][u] + D[v][dst])
    return -1 if best == INF else best
'''
def gen_d2(r):
    n = r.randrange(1, 8)
    edges = [[r.randrange(n), r.randrange(n), r.randrange(1, 10)] for _ in range(r.randrange(0, 14))]
    edges = [e for e in edges if e[0] != e[1]]
    return {"n": n, "edges": edges, "src": r.randrange(n), "dst": r.randrange(n)}

def build_dsa():
    r = random.Random(505)
    costs18 = [r.randrange(1, 6) for _ in range(18)]
    conf18 = [[a, b] for a in range(18) for b in range(a + 1, 18) if r.random() < 0.08]
    d1 = [("Example 1", {"costs": [3, 4, 5], "conflicts": [[0, 1]], "budget": 8, "max_rules": 2}), ("Example 2", {"costs": [2, 2, 2], "conflicts": [], "budget": 100, "max_rules": 3}),
          ("Nothing affordable", {"costs": [5, 6], "conflicts": [], "budget": 4, "max_rules": 2}), ("max_rules = 1 counts affordable single rules", {"costs": [1, 2, 3, 9], "conflicts": [[0, 1]], "budget": 5, "max_rules": 1}),
          ("Everything conflicts", {"costs": [1, 1, 1, 1], "conflicts": [[a, b] for a in range(4) for b in range(a + 1, 4)], "budget": 10, "max_rules": 4}),
          ("Duplicate costs and a duplicated conflict pair", {"costs": [2, 2, 2, 2, 7], "conflicts": [[0, 1], [1, 0], [2, 3]], "budget": 9, "max_rules": 3}),
          ("n=18, loose budget (all subsets minus conflicts)", {"costs": costs18, "conflicts": conf18, "budget": 10**6, "max_rules": 18}),
          ("n=18, tight budget", {"costs": costs18, "conflicts": conf18, "budget": 20, "max_rules": 6}),
          ("n=18, no conflicts, no limits (2^18 - 1)", {"costs": [1] * 18, "conflicts": [], "budget": 100, "max_rules": 18}),
          ("n=16, many conflicts", {"costs": [r.randrange(1, 9) for _ in range(16)], "conflicts": [[a, b] for a in range(16) for b in range(a + 1, 16) if (a * b) % 3 == 0], "budget": 30, "max_rules": 8})]
    q1 = dsa_question("oa05-dsa-01", 200, "Count Compliant Rule Portfolios",
"""An alerting platform has `n` candidate rules (numbered `0..n-1`) where `costs[i]` is the review effort of rule `i`. Two rules listed in `conflicts` (pairs `[a, b]`) must never be enabled together. A **portfolio** is a non-empty set of rules.

Count the portfolios that (1) contain at most `max_rules` rules, (2) have total cost at most `budget`, and (3) contain no conflicting pair. Conflict pairs may repeat or be given in either order.""",
        ["1 <= n <= 18", "1 <= costs[i] <= 10^6", "0 <= len(conflicts) <= n(n-1)/2 * 2; a != b", "1 <= budget <= 10^9, 1 <= max_rules <= n"],
        [("Valid sets: {0},{1},{2},{0,2}; {0,1} conflicts, {1,2} costs 9 > 8, and {0,1,2} exceeds the size limit -> 4", {"costs": [3, 4, 5], "conflicts": [[0, 1]], "budget": 8, "max_rules": 2}),
         ("All 7 non-empty subsets are allowed", {"costs": [2, 2, 2], "conflicts": [], "budget": 100, "max_rules": 3})],
        "count_valid_portfolios", "def count_valid_portfolios(costs: List[int], conflicts: List[List[int]], budget: int, max_rules: int) -> int",
        "from typing import List\n\ndef count_valid_portfolios(costs: List[int], conflicts: List[List[int]], budget: int, max_rules: int) -> int:\n    # TODO\n    pass\n",
        d1, REF_D1, BR_D1, gen_d1, "O(number of valid portfolios * n) with pruning; worst case about 2^n * n (n <= 18)",
        ["Enumerating all 2^n subsets with an O(n^2) validity check is too slow for the n = 18 tests.", "Pruning on budget/size/conflicts is rewarded by the hidden performance tests."],
        "Backtracking over rules sorted by cost: add rule i only if cost, size and conflict constraints stay satisfied. Every node of the recursion tree is a valid portfolio (count it). Sorting by cost lets the loop break as soon as one rule is unaffordable, because later rules cost at least as much.",
        ["backtracking", "bitmask", "pruning"], "medium")
    n_big = 20000
    big_e = [[r.randrange(n_big), r.randrange(n_big), r.randrange(1, 10**5)] for _ in range(50000)]
    big_e = [e for e in big_e if e[0] != e[1]]
    chain = [[i, i + 1, 10] for i in range(29999)] + [[i, i + 2, 25] for i in range(0, 29998, 2)]
    d2 = [("Example 1", {"n": 4, "edges": [[0, 1, 5], [1, 2, 10], [2, 3, 1], [3, 2, 50]], "src": 0, "dst": 3}), ("Example 2", {"n": 3, "edges": [[0, 1, 8], [1, 2, 8]], "src": 0, "dst": 2}),
          ("src == dst", {"n": 2, "edges": [[0, 1, 4]], "src": 1, "dst": 1}), ("Unreachable", {"n": 4, "edges": [[0, 1, 3], [2, 3, 3]], "src": 0, "dst": 3}),
          ("Directed: reverse edges unusable", {"n": 3, "edges": [[1, 0, 2], [2, 1, 2]], "src": 0, "dst": 2}), ("Parallel edges", {"n": 3, "edges": [[0, 1, 9], [0, 1, 3], [1, 2, 7], [1, 2, 2]], "src": 0, "dst": 2}),
          ("Waiving on a longer route beats waiving on the shortest route", {"n": 4, "edges": [[0, 1, 5], [1, 3, 5], [0, 2, 1], [2, 3, 10]], "src": 0, "dst": 3}),
          ("Waiver on the most expensive edge", {"n": 5, "edges": [[0, 1, 1], [1, 2, 100], [2, 3, 1], [3, 4, 1], [0, 4, 50]], "src": 0, "dst": 4}),
          ("Chain with shortcuts, n=30000", {"n": 30000, "edges": chain, "src": 0, "dst": 29999}), ("Random n=20000 m=50000", {"n": n_big, "edges": big_e, "src": 0, "dst": n_big - 1}),
          ("Random n=20000, other pair", {"n": n_big, "edges": big_e, "src": 7, "dst": 13337})]
    q2 = dsa_question("oa05-dsa-02", 250, "Cheapest Route with One Free Hop",
"""A data pipeline routes a request through `n` services (numbered `0..n-1`) along **directed** links `[u, v, cost]`. A coupon lets you skip the cost of **at most one** link on your route (that link costs 0).

Return the minimum total cost to get from `src` to `dst`, or `-1` if `dst` is unreachable. A route may revisit services, and `src == dst` costs 0.""",
        ["1 <= n <= 10^5", "0 <= len(edges) <= 2 * 10^5", "0 <= u, v < n, u != v; parallel edges allowed", "1 <= cost <= 10^6"],
        [("Waive the 10-cost link: 5 + 0 + 1 = 6 (the link 3->2 cannot help)", d2[0][1]), ("Waive one 8-cost link -> 8", d2[1][1])],
        "min_cost_with_waiver", "def min_cost_with_waiver(n: int, edges: List[List[int]], src: int, dst: int) -> int",
        "from typing import List\n\ndef min_cost_with_waiver(n: int, edges: List[List[int]], src: int, dst: int) -> int:\n    # TODO\n    pass\n",
        d2, REF_D2, BR_D2, gen_d2, "O((n + m) log n) Dijkstra on a doubled state space (node, coupon_used)",
        ["Running Dijkstra once per waived edge is O(m (n + m) log n) and times out on large tests.", "Greedy 'waive the largest edge of the shortest path' is wrong (see the dedicated hidden test)."],
        "Model the coupon as a second layer: state (v, 0) means coupon unused, (v, 1) used. Each edge u->v has a normal transition (cost w, same layer) and, from layer 0, a free transition to layer 1. Dijkstra on this layered graph gives min(dist[dst][0], dist[dst][1]). Waiving the most expensive edge of the unconstrained shortest path is not always optimal because waiving a different edge can enable a different route.",
        ["graph", "Dijkstra", "shortest path", "state space"], "hard")
    return [q1, q2]
