import random
from datetime import date, timedelta
import numpy as np
import pandas as pd
from builder import pandas_question, dsa_question

NAN = float("nan")

# ============================== PANDAS ==============================
def px(rows):
    return pd.DataFrame(rows, columns=["symbol", "date", "close", "volume"]).astype({"close": "float64", "volume": "int64"})

def rand_px(seed, syms=("AA", "BB"), n_days=30, p_nan=0.1, p_skip=0.0, weekends=True, start=date(2024, 1, 1)):
    r = random.Random(seed); rows = []
    for s in syms:
        c = r.uniform(20, 80)
        for i in range(n_days):
            d = start + timedelta(days=i)
            if d.weekday() >= 5 and not weekends: continue
            if r.random() < p_skip: continue
            c *= 1 + r.uniform(-0.04, 0.04)
            rows.append((s, d.isoformat(), NAN if r.random() < p_nan else round(c, 2), r.randrange(100, 5000)))
    r.shuffle(rows)
    return px(rows)

REF_P1 = '''import pandas as pd

def weekly_summary(prices):
    df = prices.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"])
    df = df.sort_values(["symbol", "date"], kind="mergesort")
    df["week_end"] = df["date"] + pd.to_timedelta((4 - df["date"].dt.weekday) % 7, unit="D")
    out = (df.groupby(["symbol", "week_end"], as_index=False)
             .agg(close_last=("close", "last"), volume_sum=("volume", "sum"),
                  high_close=("close", "max"), low_close=("close", "min"), n_days=("close", "size")))
    return out.sort_values(["symbol", "week_end"]).reset_index(drop=True)
'''

REF_P2 = '''import pandas as pd

COLS = ["symbol", "date", "close", "was_missing", "ret", "ma5", "vol5"]

def rolling_metrics(prices):
    df = prices.copy()
    df["date"] = pd.to_datetime(df["date"])
    frames = []
    for sym, g in df.groupby("symbol", sort=True):
        s = (g.sort_values("date", kind="mergesort").drop_duplicates("date", keep="last")
              .set_index("date")["close"])
        idx = pd.date_range(s.index.min(), s.index.max(), freq="B")
        s = s.reindex(idx)
        was_missing = s.isna().to_numpy()
        c = s.ffill(limit=2)
        ret = c / c.shift(1) - 1
        frames.append(pd.DataFrame({
            "symbol": sym, "date": idx, "close": c.to_numpy(), "was_missing": was_missing, "ret": ret.to_numpy(),
            "ma5": c.rolling(5, min_periods=5).mean().to_numpy(), "vol5": ret.rolling(5, min_periods=5).std().to_numpy()}))
    if not frames:
        return pd.DataFrame({"symbol": pd.Series([], dtype=object), "date": pd.Series([], dtype="datetime64[ns]"), "close": pd.Series([], dtype="float64"),
                             "was_missing": pd.Series([], dtype=bool), "ret": pd.Series([], dtype="float64"), "ma5": pd.Series([], dtype="float64"), "vol5": pd.Series([], dtype="float64")})
    return pd.concat(frames, ignore_index=True)[COLS]
'''

def rt(rows):
    return pd.DataFrame(rows, columns=["symbol", "date", "ret"]).astype({"ret": "float64"})

def rand_rt(seed, syms=("AA", "BB", "CC"), n=40, p_nan=0.08, p_out=0.06):
    r = random.Random(seed); rows = []
    for s in syms:
        for i in range(n):
            v = round(r.gauss(0, 0.01), 5)
            if r.random() < p_out: v = round(r.choice([-1, 1]) * r.uniform(0.06, 0.2), 5)
            rows.append((s, (date(2024, 3, 1) + timedelta(days=i)).isoformat(), NAN if r.random() < p_nan else v))
    r.shuffle(rows)
    return rt(rows)

REF_P3 = '''import pandas as pd

def clip_outliers(returns):
    df = returns.copy()
    q1 = df.groupby("symbol")["ret"].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby("symbol")["ret"].transform(lambda s: s.quantile(0.75))
    n = df.groupby("symbol")["ret"].transform("count")
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    active = n >= 4
    df["ret_clipped"] = df["ret"].where(~active, df["ret"].clip(lower=lo, upper=hi))
    df["is_outlier"] = (active & ((df["ret"] < lo) | (df["ret"] > hi))).astype(bool)
    return df[["symbol", "date", "ret", "ret_clipped", "is_outlier"]].reset_index(drop=True)
'''

def build_pandas():
    qs = []
    p1 = px([("AAA", "2024-01-02", 10.0, 100), ("AAA", "2024-01-03", 11.0, 200), ("AAA", "2024-01-05", 12.0, 300), ("AAA", "2024-01-06", 13.0, 50),
             ("AAA", "2024-01-08", 14.0, 10), ("AAA", "2024-01-09", NAN, 999), ("AAA", "2024-01-12", 9.0, 20), ("BBB", "2024-01-07", 5.0, 1), ("BBB", "2024-01-08", 6.0, 2)])
    p2 = px([("Z", "2024-02-02", 1.5, 7)])
    d1 = [("Sample: weekend prints roll into the next Friday week; NaN close dropped", {"prices": p1}, {}), ("Single row on a Friday", {"prices": p2}, {}),
          ("Only NaN closes (empty result)", {"prices": px([("Y", "2024-02-02", NAN, 1)])}, {}),
          ("Randomised", {"prices": rand_px(11)}, {}), ("Randomised longer", {"prices": rand_px(12, ("A", "B", "C"), 60, 0.15)}, {}), ("Randomised with gaps", {"prices": rand_px(13, ("Q",), 45, 0.1, 0.4)}, {})]
    qs.append(pandas_question("oa04-pd-01", 150, "Weekly Summary with Friday Week Ends",
"""Daily prices (including occasional weekend prints) must be summarised into weeks that **end on Friday**. Implement `weekly_summary(prices)`.

1. Parse `date` and drop rows with a missing `close`.
2. Define `week_end` as the first Friday on or after the date (Friday → itself, Saturday/Sunday → the following Friday, Monday → the Friday of that week).
3. Group by `symbol` and `week_end`, ordering rows within a group by `date` (stable). Compute `close_last` (close of the latest date), `volume_sum`, `high_close`, `low_close` and `n_days` (rows in the week).
4. Weeks without data do not appear. Return `symbol, week_end, close_last, volume_sum, high_close, low_close, n_days` sorted by `symbol`, `week_end`; default index.""",
        "weekly_summary", "def weekly_summary(prices: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef weekly_summary(prices: pd.DataFrame) -> pd.DataFrame:\n    df = prices.copy()\n    # TODO\n    return df\n",
        {"prices": [("symbol", "str", "Ticker"), ("date", "str", "'YYYY-MM-DD' (may be a weekend)"), ("close", "float64", "Close, may be NaN"), ("volume", "int64", "Shares traded")]},
        d1, REF_P1, "Columns [symbol str, week_end datetime64, close_last float64, volume_sum int64, high_close float64, low_close float64, n_days int64].",
        ["A Saturday print belongs to the following Friday's week.", "Rows are not necessarily sorted in the input: 'last' must follow date order."],
        "Compute week_end with ((4 - weekday) % 7) days offset (equivalent to resample('W-FRI')), sort by date so first/last aggregations are well-defined, then groupby-agg with named aggregations.",
        ["resampling", "groupby", "datetime"], "medium"))
    c1 = px([("S", "2024-01-01", 10.0, 1), ("S", "2024-01-02", 10.5, 1), ("S", "2024-01-03", NAN, 1), ("S", "2024-01-05", 11.0, 1), ("S", "2024-01-06", 99.0, 1),
             ("S", "2024-01-08", 11.5, 1), ("S", "2024-01-09", 12.0, 1), ("S", "2024-01-10", 12.5, 1), ("S", "2024-01-11", 12.0, 1), ("S", "2024-01-12", 13.0, 1)])
    c2 = px([("A", "2024-03-04", 5.0, 1), ("A", "2024-03-04", 6.0, 1), ("A", "2024-03-05", 7.0, 1), ("A", "2024-03-11", 8.0, 1), ("B", "2024-03-04", NAN, 1), ("B", "2024-03-06", 2.0, 1)])
    d2 = [("Sample: missing business days, NaN, weekend row, forward-fill limit", {"prices": c1}, {}), ("Duplicates keep last; gap longer than the fill limit", {"prices": c2}, {}),
          ("Empty input", {"prices": px([])}, {}), ("Randomised", {"prices": rand_px(21, ("AA", "BB"), 40, 0.1, 0.15)}, {}),
          ("Randomised long", {"prices": rand_px(22, ("AA", "BB", "CC"), 70, 0.12, 0.2)}, {}), ("Randomised dense", {"prices": rand_px(23, ("ZZ",), 50, 0.02, 0.02)}, {})]
    qs.append(pandas_question("oa04-pd-02", 150, "Rolling Metrics on a Business-Day Calendar",
"""Price series often have missing days. Implement `rolling_metrics(prices)`.

For each `symbol` (processed independently, symbols in ascending order):

1. Parse `date`; sort by date and, if a date appears more than once, keep the **last** row.
2. Re-index to **every business day (Mon–Fri)** from the symbol's first to last date (`freq='B'`). Weekend rows are discarded.
3. `was_missing` = the close is missing (NaN or newly inserted) **before** filling.
4. Forward-fill `close`, filling **at most 2 consecutive** missing days (`limit=2`); longer gaps stay NaN after the second filled day.
5. `ret = close / previous_row_close - 1` on the filled close (NaN if either is NaN).
6. `ma5` = rolling mean of the filled close over 5 rows and `vol5` = rolling sample standard deviation (ddof = 1) of `ret` over 5 rows; both need a full window of 5 non-NaN values (`min_periods=5`).

Return `symbol, date, close, was_missing, ret, ma5, vol5`, symbols ascending then dates ascending, default index. An empty input gives an empty frame with those columns.""",
        "rolling_metrics", "def rolling_metrics(prices: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef rolling_metrics(prices: pd.DataFrame) -> pd.DataFrame:\n    df = prices.copy()\n    # TODO\n    return df\n",
        {"prices": [("symbol", "str", "Ticker"), ("date", "str", "'YYYY-MM-DD'"), ("close", "float64", "Close, may be NaN"), ("volume", "int64", "Shares traded (unused)")]},
        d2, REF_P2, "Columns [symbol str, date datetime64, close float64, was_missing bool, ret float64, ma5 float64, vol5 float64]; float tolerance rel 1e-6.",
        ["Business-day re-indexing (inserted rows) is checked in every test.", "ffill limit=2 and min_periods=5 behaviours are separately visible in the sample."],
        "Per symbol: sort/dedupe, reindex to a business-day range, record was_missing, ffill(limit=2), compute returns by division with shift(1) and rolling(5, min_periods=5) statistics. Rolling windows count rows, not calendar days, so inserting the missing business days first matters.",
        ["reindex", "rolling", "missing data", "time series"], "hard"))
    o1 = rt([("A", "2024-03-01", 0.01), ("A", "2024-03-02", 0.02), ("A", "2024-03-03", 0.015), ("A", "2024-03-04", 0.012), ("A", "2024-03-05", 0.5), ("A", "2024-03-06", NAN),
             ("B", "2024-03-01", 0.2), ("B", "2024-03-02", -0.2), ("B", "2024-03-03", 0.1)])
    o2 = rt([("C", "2024-03-01", 1.0), ("C", "2024-03-02", 1.0), ("C", "2024-03-03", 1.0), ("C", "2024-03-04", 1.0), ("C", "2024-03-05", 1.0)])
    d3 = [("Sample: outlier flagged, NaN kept, small group untouched", {"returns": o1}, {}), ("Constant series: IQR 0 and no outliers", {"returns": o2}, {}),
          ("Empty input", {"returns": rt([])}, {}), ("Randomised", {"returns": rand_rt(31)}, {}), ("Randomised larger", {"returns": rand_rt(32, ("A", "B", "C", "D", "E"), 80)}, {}),
          ("Randomised, heavy outliers", {"returns": rand_rt(33, ("X", "Y"), 50, 0.1, 0.2)}, {})]
    qs.append(pandas_question("oa04-pd-03", 100, "IQR Outlier Capping per Symbol",
"""Implement `clip_outliers(returns)` which caps extreme returns separately for each symbol.

For each `symbol`, with `q1` and `q3` the 25th and 75th percentiles of its non-NaN `ret` (pandas default linear interpolation) and `iqr = q3 - q1`, the fences are `lo = q1 - 1.5*iqr` and `hi = q3 + 1.5*iqr`.

* Symbols with fewer than 4 non-NaN returns are **not** processed: `ret_clipped = ret` and `is_outlier = False`.
* Otherwise `ret_clipped = ret` clipped to `[lo, hi]` and `is_outlier` is `True` exactly when `ret < lo` or `ret > hi`. NaN returns stay NaN with `is_outlier = False`.

Keep the original row order and return `symbol, date, ret, ret_clipped, is_outlier` with default index.""",
        "clip_outliers", "def clip_outliers(returns: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef clip_outliers(returns: pd.DataFrame) -> pd.DataFrame:\n    df = returns.copy()\n    # TODO\n    return df\n",
        {"returns": [("symbol", "str", "Ticker"), ("date", "str", "'YYYY-MM-DD'"), ("ret", "float64", "Daily return, may be NaN")]},
        d3, REF_P3, "Columns [symbol str, date str, ret float64, ret_clipped float64, is_outlier bool], original row order preserved.",
        ["Group-wise quantiles via transform (no row reordering).", "Small-group rule and NaN handling are tested."],
        "groupby().transform with quantile broadcasts the per-symbol statistics back to the rows, so the original order is kept; Series.clip(lower, upper) takes aligned Series bounds, and boolean masks produce the flag.",
        ["groupby transform", "quantiles", "outliers"], "medium"))
    return qs

# ============================== DSA ==============================
REF_D1 = '''from bisect import bisect_right
from typing import List

def max_profit(jobs: List[List[int]]) -> int:
    jobs = sorted(jobs, key=lambda j: j[1])
    ends = [j[1] for j in jobs]
    best = [0] * (len(jobs) + 1)              # best[i] = optimum using the first i jobs (by end time)
    for i, (s, e, p) in enumerate(jobs, 1):
        k = bisect_right(ends, s, 0, i - 1)    # number of jobs finishing at or before s
        best[i] = max(best[i - 1], best[k] + p)
    return best[-1]
'''
BR_D1 = '''def max_profit(jobs):
    n = len(jobs); best = 0
    for mask in range(1 << n):
        chosen = [jobs[i] for i in range(n) if mask >> i & 1]
        chosen.sort()
        if all(chosen[i][1] <= chosen[i + 1][0] for i in range(len(chosen) - 1)):
            best = max(best, sum(j[2] for j in chosen))
    return best
'''
def gen_d1(r):
    n = r.randrange(0, 9); jobs = []
    for _ in range(n):
        s = r.randrange(0, 12); jobs.append([s, s + r.randrange(1, 6), r.randrange(1, 20)])
    return {"jobs": jobs}

REF_D2 = '''from typing import List

def min_largest_batch(loads: List[int], m: int) -> int:
    def pieces(cap):
        count, cur = 1, 0
        for x in loads:
            if cur + x > cap:
                count += 1
                cur = x
            else:
                cur += x
        return count
    lo, hi = max(loads), sum(loads)
    while lo < hi:
        mid = (lo + hi) // 2
        if pieces(mid) <= m:
            hi = mid
        else:
            lo = mid + 1
    return lo
'''
BR_D2 = '''from functools import lru_cache
def min_largest_batch(loads, m):
    n = len(loads)
    pre = [0]
    for x in loads: pre.append(pre[-1] + x)
    @lru_cache(None)
    def f(i, k):
        if k == 1: return pre[n] - pre[i]
        return min(max(pre[j] - pre[i], f(j, k - 1)) for j in range(i + 1, n - k + 2))
    return f(0, m)
'''
def gen_d2(r):
    n = r.randrange(1, 9)
    return {"loads": [r.randrange(0, 15) for _ in range(n)], "m": r.randrange(1, n + 1)}

def build_dsa():
    r = random.Random(404)
    jobs_big = [[(s := r.randrange(0, 10**6)), s + r.randrange(1, 5000), r.randrange(1, 1000)] for _ in range(40000)]
    jobs_mid = [[(s := r.randrange(0, 3000)), s + r.randrange(1, 60), r.randrange(1, 100)] for _ in range(20000)]
    d1 = [("Example 1", {"jobs": [[1, 3, 5], [2, 5, 6], [4, 6, 5], [6, 7, 4]]}), ("Example 2: touching jobs allowed", {"jobs": [[0, 2, 3], [2, 4, 3], [1, 3, 5]]}),
          ("No jobs", {"jobs": []}), ("Single job", {"jobs": [[5, 9, 11]]}), ("One huge job beats many small", {"jobs": [[0, 100, 500], [0, 10, 100], [10, 20, 100], [20, 30, 100], [30, 40, 100]]}),
          ("All overlapping", {"jobs": [[0, 10, 4], [1, 11, 9], [2, 12, 7]]}), ("Identical windows", {"jobs": [[3, 6, 2], [3, 6, 8], [3, 6, 5]]}),
          ("Random n=20000 dense", {"jobs": jobs_mid}), ("Random n=40000 sparse", {"jobs": jobs_big}),
          ("Chain of 30000 back-to-back jobs", {"jobs": [[i, i + 1, 1 + (i % 7)] for i in range(30000)]})]
    q1 = dsa_question("oa04-dsa-01", 200, "Maximum Profit from Non-Overlapping Trade Windows",
"""A desk can run at most one strategy at a time. Each candidate strategy is `[start, end, profit]`, occupying the half-open interval `[start, end)` – a strategy may start exactly when another ends. Choose a set of strategies with no overlaps that maximises total profit and return that maximum.""",
        ["0 <= len(jobs) <= 10^5", "0 <= start < end <= 10^9", "1 <= profit <= 10^6"],
        [("Choose [1,3,5] and [4,6,5] and [6,7,4] -> 14", {"jobs": [[1, 3, 5], [2, 5, 6], [4, 6, 5], [6, 7, 4]]}), ("[0,2] and [2,4] touch and are compatible -> 6 beats [1,3] alone (5)", {"jobs": [[0, 2, 3], [2, 4, 3], [1, 3, 5]]})],
        "max_profit", "def max_profit(jobs: List[List[int]]) -> int",
        "from typing import List\n\ndef max_profit(jobs: List[List[int]]) -> int:\n    # TODO\n    pass\n",
        d1, REF_D1, BR_D1, gen_d1, "O(n log n) time (sort + binary search), O(n) space",
        ["Greedy by earliest end or highest profit fails several tests (partial credit for small cases only).", "O(n^2) DP times out on n = 40000."],
        "Weighted interval scheduling. Sort by end time; best[i] = max(best[i-1], profit_i + best[k]) where k is the number of jobs ending at or before start_i, found with bisect_right on the sorted end times.",
        ["dynamic programming", "binary search", "intervals"], "medium")
    big = [r.randrange(0, 10**9) for _ in range(40000)]
    d2 = [("Example 1", {"loads": [7, 2, 5, 10, 8], "m": 2}), ("Example 2", {"loads": [1, 2, 3, 4, 5], "m": 5}), ("m = 1", {"loads": [4, 4, 4], "m": 1}),
          ("Zeros", {"loads": [0, 0, 0, 0], "m": 2}), ("Single huge element", {"loads": [1, 1, 100, 1, 1], "m": 3}), ("Increasing", {"loads": list(range(1, 101)), "m": 7}),
          ("Random n=40000, m=1000", {"loads": big, "m": 1000}), ("Random n=40000, m=2", {"loads": big, "m": 2}), ("Random n=40000, m=40000", {"loads": big, "m": 40000}),
          ("Equal loads", {"loads": [10**9] * 50000, "m": 7})]
    q2 = dsa_question("oa04-dsa-02", 250, "Balance the Heaviest Processing Batch",
"""A feed of `n` message loads (`loads[i]` = work units, in arrival order) must be processed in exactly `m` consecutive, non-empty batches. The cost of a split is the **largest total load of any batch**. Return the minimum possible cost.""",
        ["1 <= m <= len(loads) <= 10^5", "0 <= loads[i] <= 10^9"],
        [("Best split [7,2,5] [10,8] has batches 14 and 18 -> 18", {"loads": [7, 2, 5, 10, 8], "m": 2}), ("Five batches of one message each -> max load 5", {"loads": [1, 2, 3, 4, 5], "m": 5})],
        "min_largest_batch", "def min_largest_batch(loads: List[int], m: int) -> int",
        "from typing import List\n\ndef min_largest_batch(loads: List[int], m: int) -> int:\n    # TODO\n    pass\n",
        d2, REF_D2, BR_D2, gen_d2, "O(n log(sum(loads))) time, O(1) extra space (binary search on the answer)",
        ["Recursive/DP solutions O(n^2 m) pass only tiny tests.", "The bounds max(loads) .. sum(loads) are exercised by the m = 1 and m = n tests."],
        "Binary search on the capacity C: greedily pack messages into batches without exceeding C; feasibility (pieces <= m) is monotonic in C. Since n >= m, a feasible 'at most m' split can always be refined into exactly m non-empty batches without raising the maximum. Search range is [max(loads), sum(loads)].",
        ["binary search on answer", "greedy", "arrays"], "hard")
    return [q1, q2]
