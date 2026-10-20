import random
import numpy as np
import pandas as pd
from builder import pandas_question, dsa_question

NAN = float("nan")

# =============================== PANDAS ===============================
def ticks_df(rows):
    return pd.DataFrame(rows, columns=["symbol", "ts", "price", "size"]).astype({"price": "float64", "size": "int64"})


def rand_ticks(seed, n=40):
    r = random.Random(seed)
    rows = []
    for _ in range(n):
        sym = r.choice(["aapl", " AAPL", "Msft ", "MSFT", "nvda", "NVDA "])
        ts = f"2024-03-04 09:{r.randrange(30, 36):02d}:{r.randrange(0, 60, 15):02d}"
        if r.random() < 0.06: ts = r.choice(["bad-ts", "2024-13-45 10:00:00", "", "2024/03/04 09:30:00"])
        p = r.choice([NAN, -1.0, 0.0] + [round(r.uniform(100, 200), 2)] * 6) if r.random() < 0.3 else round(r.uniform(100, 200), 2)
        rows.append((sym, ts, p, r.choice([0, 100, 200, 300, 500, -5][: 5 if r.random() < 0.9 else 6])))
    return ticks_df(rows)


T1 = ticks_df([
    ("aapl", "2024-03-04 09:30:00", 180.10, 100), (" AAPL", "2024-03-04 09:30:00", 180.15, 200), ("AAPL", "2024-03-04 09:30:01", NAN, 50),
    ("msft ", "2024-03-04 09:30:00", 410.00, 300), ("MSFT", "not a time", 410.10, 100), ("MSFT", "2024-03-04 09:30:05", -1.0, 100),
    ("MSFT", "2024-03-04 09:30:02", 410.20, 0), ("MSFT", "2024-03-04 09:31:00", 410.30, 150), ("AAPL", "2024-03-04 09:29:59", 179.90, 10)])
T2 = ticks_df([("nvda", "2024-03-04 09:30:00", 875.00, 20), ("NVDA", "2024-03-04 09:30:00", NAN, 20), ("NVDA", "2024-03-04 09:30:10", 875.50, 40),
               ("nvda ", "2024-03-04 09:30:10", 875.60, 40)])
T_EMPTY = ticks_df([("x", "bad", NAN, 0), ("y", "2024-03-04 09:30:00", 0.0, 10)])
T_SINGLE = ticks_df([("tsla", "2024-03-05 15:59:59", 175.25, 12)])

REF_P1 = '''import pandas as pd

def clean_ticks(ticks):
    df = ticks.copy()
    df["symbol"] = df["symbol"].str.strip().str.upper()
    df["ts"] = pd.to_datetime(df["ts"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["ts"])
    df = df.drop_duplicates(subset=["symbol", "ts"], keep="last")
    df = df[df["price"].notna() & (df["price"] > 0) & (df["size"] > 0)]
    df = df.sort_values(["symbol", "ts"], kind="mergesort")
    return df[["symbol", "ts", "price", "size"]].reset_index(drop=True)
'''


def px_df(rows):
    return pd.DataFrame(rows, columns=["symbol", "date", "close"]).astype({"close": "float64"})


def rand_px(seed, syms=("A", "B", "C"), n=8, p_nan=0.25):
    r = random.Random(seed)
    rows = []
    for s in syms:
        c = r.uniform(20, 100)
        days = list(range(1, n + 1)); r.shuffle(days)       # shuffled order
        for d in days:
            c *= 1 + r.uniform(-0.05, 0.05)
            v = NAN if r.random() < p_nan else (-3.0 if r.random() < 0.05 else round(c, 2))
            rows.append((s, f"2024-02-{d:02d}", v))
    return px_df(rows)


PX1 = px_df([("A", "2024-02-02", 11.0), ("A", "2024-02-01", 10.0), ("A", "2024-02-03", NAN), ("A", "2024-02-04", 12.1),
             ("B", "2024-02-01", NAN), ("B", "2024-02-02", 50.0), ("B", "2024-02-03", 55.0), ("B", "2024-02-04", 0.0)])
PX2 = px_df([("Z", "2024-02-01", 5.0), ("Z", "2024-02-02", NAN), ("Z", "2024-02-03", NAN), ("Z", "2024-02-04", 6.0)])
PX_ONE = px_df([("Q", "2024-02-01", NAN)])

REF_P2 = '''import pandas as pd
import numpy as np

def fill_and_returns(prices):
    df = prices.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["symbol", "date"], kind="mergesort").reset_index(drop=True)
    df["close"] = df["close"].where(df["close"] > 0)          # non-positive prices are invalid -> missing
    df["close"] = df.groupby("symbol")["close"].ffill()
    prev = df.groupby("symbol")["close"].shift(1)
    df["daily_return"] = df["close"] / prev - 1
    return df[["symbol", "date", "close", "daily_return"]]
'''


def ret_df(rows):
    return pd.DataFrame(rows, columns=["symbol", "date", "ret"]).astype({"ret": "float64"})


def rand_ret(seed, syms=("AA", "BB", "CC", "DD"), n=6, dup=True):
    r = random.Random(seed)
    rows = []
    for s in syms:
        for d in range(1, n + 1):
            if r.random() < 0.8:
                rows.append((s, f"2024-04-{d:02d}", round(r.uniform(-0.03, 0.03), 4) if r.random() > 0.15 else NAN))
                if dup and r.random() < 0.15:
                    rows.append((s, f"2024-04-{d:02d}", round(r.uniform(-0.03, 0.03), 4)))
    r.shuffle(rows)
    return ret_df(rows)


RET1 = ret_df([("MSFT", "2024-04-02", 0.01), ("AAPL", "2024-04-01", 0.02), ("AAPL", "2024-04-02", NAN), ("MSFT", "2024-04-01", -0.01),
               ("NVDA", "2024-04-01", 0.05), ("AAPL", "2024-04-01", 0.04)])
RET2 = ret_df([("B", "2024-05-02", 0.0), ("A", "2024-05-01", NAN), ("B", "2024-05-01", NAN)])
RET_EMPTYISH = ret_df([("Z", "2024-05-01", NAN)])

REF_P3 = '''import pandas as pd

def wide_returns(returns):
    df = returns.copy()
    df["date"] = pd.to_datetime(df["date"])
    wide = df.pivot_table(index="date", columns="symbol", values="ret", aggfunc="mean", dropna=False)
    wide = wide.reindex(sorted(wide.columns), axis=1)
    out = wide.copy()
    out["market_avg"] = wide.mean(axis=1, skipna=True)
    out["n_reporting"] = wide.notna().sum(axis=1).astype("int64")
    out = out.sort_index().reset_index()
    out.columns.name = None
    return out
'''


def build_pandas():
    qs = []
    # ---- P1
    d1 = [("Sample: mixed case/whitespace, duplicates, bad timestamps and prices", {"ticks": T1}, {}),
          ("Duplicate key whose last row has NaN price removes the key", {"ticks": T2}, {}),
          ("Everything invalid -> empty result with correct columns", {"ticks": T_EMPTY}, {}),
          ("Single clean row", {"ticks": T_SINGLE}, {}),
          ("Randomised 40 ticks", {"ticks": rand_ticks(11, 40)}, {}),
          ("Randomised 80 ticks", {"ticks": rand_ticks(12, 80)}, {})]
    qs.append(pandas_question("oa01-pd-01", 150, "Clean a Raw Tick Feed",
"""Raw ticks arrive with inconsistent symbols, bad timestamps, duplicated messages and invalid prices. Implement `clean_ticks(ticks)` which returns a clean tick table.

Apply these steps **in this order**:

1. Normalise `symbol` with `str.strip()` and `str.upper()`.
2. Parse `ts` with format `%Y-%m-%d %H:%M:%S`; unparseable values become `NaT`; **drop** those rows.
3. Remove duplicate `(symbol, ts)` pairs, **keeping the last** row in the original input order.
4. Drop rows where `price` is missing or `<= 0`, or where `size <= 0`.
5. Sort by `symbol` then `ts` ascending and reset the index.

Return exactly the columns `symbol, ts, price, size` (`ts` as datetime64). Do not modify the input DataFrame.""",
        "clean_ticks", "def clean_ticks(ticks: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef clean_ticks(ticks: pd.DataFrame) -> pd.DataFrame:\n    \"\"\"Return the cleaned tick table (see problem statement).\"\"\"\n    df = ticks.copy()\n    # TODO\n    return df\n",
        {"ticks": [("symbol", "str", "Raw symbol, may contain spaces/lower case"), ("ts", "str", "Timestamp text 'YYYY-MM-DD HH:MM:SS' or garbage"),
                   ("price", "float64", "Trade price; may be NaN, zero or negative"), ("size", "int64", "Shares traded")]},
        d1, REF_P1, "DataFrame with columns [symbol (str), ts (datetime64), price (float64), size (int64)], sorted by symbol, ts; default RangeIndex (index is ignored by the grader).",
        ["Duplicate handling before price filtering is verified by a dedicated test.", "Empty-result test checks that column names are preserved."],
        "Normalise first so ' AAPL' and 'aapl' collide; parse with errors='coerce' and drop NaT; drop_duplicates(keep='last') on the normalised key; then filter invalid prices/sizes. Because duplicates are removed before price filtering, a last duplicate with a NaN price eliminates the key entirely (a different order would resurrect the earlier row).",
        ["data cleaning", "datetime parsing", "duplicates", "missing values"], "medium"))
    # ---- P2
    d2 = [("Sample: unsorted input, NaN gap, zero price", {"prices": PX1}, {}), ("Leading NaN and consecutive gaps", {"prices": PX2}, {}),
          ("Single NaN row", {"prices": PX_ONE}, {}), ("Randomised 3 symbols", {"prices": rand_px(21)}, {}),
          ("Randomised 5 symbols, long", {"prices": rand_px(22, ("P", "Q", "R", "S", "T"), 15, 0.3)}, {}),
          ("Randomised, few gaps", {"prices": rand_px(23, ("U", "V"), 20, 0.05)}, {})]
    qs.append(pandas_question("oa01-pd-02", 150, "Forward-Fill Closes and Compute Daily Returns",
"""A price table has missing or invalid closes. Implement `fill_and_returns(prices)`:

1. Convert `date` to datetime and sort by `symbol`, `date` (stable sort).
2. Treat any `close <= 0` as missing.
3. **Within each symbol**, forward-fill missing closes. Leading missing values stay missing – never fill across symbols and never back-fill.
4. `daily_return = close / previous_close_of_same_symbol - 1`, using the filled closes. It is `NaN` for the first row of each symbol and whenever the current or previous filled close is missing.

Return the columns `symbol, date, close, daily_return`, one row per input row, in sorted order, with default index. Do not use `pct_change`'s deprecated filling behaviour.""",
        "fill_and_returns", "def fill_and_returns(prices: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\nimport numpy as np\n\ndef fill_and_returns(prices: pd.DataFrame) -> pd.DataFrame:\n    df = prices.copy()\n    # TODO\n    return df\n",
        {"prices": [("symbol", "str", "Ticker"), ("date", "str", "'YYYY-MM-DD'"), ("close", "float64", "Closing price; NaN or <= 0 means missing")]},
        d2, REF_P2, "Columns [symbol, date (datetime64), close (float64), daily_return (float64)]; float tolerance rel 1e-6.",
        ["Group-wise ffill (no leakage between symbols) is tested.", "Non-positive prices as missing is tested in the sample test."],
        "groupby('symbol')['close'].ffill() fills only within symbols; computing the return as close / groupby.shift(1) - 1 gives NaN for first rows and for rows next to a leading gap. Masking close <= 0 before filling makes a zero price behave like a missing one.",
        ["groupby", "ffill", "returns", "vectorised"], "medium"))
    # ---- P3
    d3 = [("Sample: duplicates are averaged, NaN returns", {"returns": RET1}, {}), ("All NaN in a date and a symbol", {"returns": RET2}, {}),
          ("Only NaN", {"returns": RET_EMPTYISH}, {}), ("Randomised 4 symbols", {"returns": rand_ret(31)}, {}),
          ("Randomised 5 symbols 10 days", {"returns": rand_ret(32, ("A1", "B2", "C3", "D4", "E5"), 10)}, {}),
          ("Randomised no duplicates", {"returns": rand_ret(33, dup=False)}, {})]
    qs.append(pandas_question("oa01-pd-03", 100, "Reshape Returns into a Wide Panel",
"""Implement `wide_returns(returns)` to reshape a long table of daily returns into a date-by-symbol panel and add two data-quality columns.

* Convert `date` to datetime.
* If a `(date, symbol)` pair appears more than once, use the **mean** of its `ret` values (NaN values are ignored by the mean; a pair whose values are all NaN is NaN).
* Output one row per distinct date (ascending). First column `date`, then one column per symbol in **alphabetical order**, then
  * `market_avg` – mean across symbols on that date, skipping NaN (NaN if every symbol is NaN/absent), and
  * `n_reporting` – number of symbols with a non-NaN return on that date (int64).
* Reset the index; column labels must be plain strings (no `columns.name`).""",
        "wide_returns", "def wide_returns(returns: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef wide_returns(returns: pd.DataFrame) -> pd.DataFrame:\n    df = returns.copy()\n    # TODO\n    return df\n",
        {"returns": [("symbol", "str", "Ticker"), ("date", "str", "'YYYY-MM-DD'"), ("ret", "float64", "Daily return, may be NaN")]},
        d3, REF_P3, "Columns [date (datetime64), <symbols alphabetical> (float64), market_avg (float64), n_reporting (int64)].",
        ["Duplicates must be averaged, not summed or dropped.", "Alphabetical column order matters (column order is compared)."],
        "pivot_table with aggfunc='mean' collapses duplicates; dropna=False keeps all-NaN cells. Mean with skipna handles missing symbols; notna().sum(axis=1) counts reporting symbols.",
        ["reshape", "pivot", "data quality"], "medium"))
    return qs


# =============================== DSA ===============================
REF_D1 = '''from typing import List

def closest_triplet_sum(nums: List[int], target: int) -> int:
    a = sorted(nums)
    n = len(a)
    best = None
    for i in range(n - 2):
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = a[i] + a[lo] + a[hi]
            if best is None or abs(s - target) < abs(best - target) or (abs(s - target) == abs(best - target) and s < best):
                best = s
            if s == target:
                return s
            if s < target:
                lo += 1
            else:
                hi -= 1
    return best
'''
BR_D1 = '''from itertools import combinations
def closest_triplet_sum(nums, target):
    best = None
    for c in combinations(nums, 3):
        s = sum(c)
        if best is None or abs(s - target) < abs(best - target) or (abs(s - target) == abs(best - target) and s < best):
            best = s
    return best
'''
def gen_d1(r):
    n = r.randrange(3, 9)
    return {"nums": [r.randrange(-10, 11) for _ in range(n)], "target": r.randrange(-30, 31)}

REF_D2 = '''from typing import List
from collections import deque

def longest_stable_window(prices: List[int], k: int) -> int:
    mx, mn = deque(), deque()          # indices; values decreasing / increasing
    left = best = 0
    for right, v in enumerate(prices):
        while mx and prices[mx[-1]] <= v:
            mx.pop()
        mx.append(right)
        while mn and prices[mn[-1]] >= v:
            mn.pop()
        mn.append(right)
        while prices[mx[0]] - prices[mn[0]] > k:
            left += 1
            if mx[0] < left:
                mx.popleft()
            if mn[0] < left:
                mn.popleft()
        best = max(best, right - left + 1)
    return best
'''
BR_D2 = '''def longest_stable_window(prices, k):
    n = len(prices); best = 0
    for i in range(n):
        lo = hi = prices[i]
        for j in range(i, n):
            lo = min(lo, prices[j]); hi = max(hi, prices[j])
            if hi - lo > k: break
            best = max(best, j - i + 1)
    return best
'''
def gen_d2(r):
    n = r.randrange(1, 14)
    return {"prices": [r.randrange(0, 20) for _ in range(n)], "k": r.randrange(0, 8)}


def build_dsa():
    r = random.Random(1001)
    big = [r.randrange(-10**6, 10**6) for _ in range(2000)]
    dup = [5] * 1500
    d1 = [("Example 1", {"nums": [-4, 2, 1, -1, 7], "target": 3}), ("Example 2: tie between sums 2 and 4 -> smaller", {"nums": [0, 0, 2, 4], "target": 3}),
          ("Exactly three elements", {"nums": [5, -2, 9], "target": 100}), ("Exact hit available", {"nums": [10, -3, 4, 8, 1, 0], "target": 9}),
          ("All negatives", {"nums": [-8, -3, -5, -1, -9], "target": 0}), ("Heavy duplicates, n=1500", {"nums": dup, "target": 14}),
          ("Large values random n=2000", {"nums": big, "target": 12345}), ("Large n=2000, far target", {"nums": big[::-1], "target": -3 * 10**6 - 7}),
          ("Tie on both sides", {"nums": [0, 0, 5, -5, 1, -1], "target": 0})]
    ex1 = [("Triplet (2, 1, -1) sums to 2, which is 1 away from 3; no triplet gets closer", {"nums": [-4, 2, 1, -1, 7], "target": 3}),
           ("Sums 2 (0+0+2) and 4 (0+0+4) are both 1 away from 3; the smaller sum is returned", {"nums": [0, 0, 2, 4], "target": 3})]
    q1 = dsa_question("oa01-dsa-01", 200, "Closest Triplet Notional",
"""A risk desk wants to pick exactly **three distinct positions** (three different indices) from a book so that their combined notional is as close as possible to a hedge target.

Given integer array `nums` and integer `target`, return the sum of three elements at distinct indices whose sum is closest to `target`. If two different sums are equally close, return the **smaller** sum.""",
        ["3 <= len(nums) <= 2000", "-10^6 <= nums[i] <= 10^6", "-4*10^6 <= target <= 4*10^6"], ex1,
        "closest_triplet_sum", "def closest_triplet_sum(nums: List[int], target: int) -> int",
        "from typing import List\n\ndef closest_triplet_sum(nums: List[int], target: int) -> int:\n    # TODO\n    pass\n",
        d1, REF_D1, BR_D1, gen_d1, "O(n^2) time after sorting, O(1) extra space",
        ["Brute force O(n^3) passes only the small tests.", "The tie rule (return smaller sum) is covered by dedicated tests."],
        "Sort, fix the first element, move two pointers inward: if the sum is below target advance the left pointer, otherwise retreat the right pointer, tracking the best (distance, then smaller sum). Total O(n^2). The three-pointer brute force is O(n^3) = 8*10^9 for n=2000.",
        ["arrays", "two pointers", "sorting"], "medium")
    r2 = random.Random(2002)
    walk, v = [], 1000
    for _ in range(30000):
        v += r2.randrange(-3, 4); walk.append(v)
    d2 = [("Example 1", {"prices": [10, 12, 11, 15, 13, 12, 16], "k": 3}), ("Example 2: all equal", {"prices": [7, 7, 7, 7], "k": 0}),
          ("Single element", {"prices": [42], "k": 0}), ("k=0 distinct values", {"prices": [1, 2, 3, 4], "k": 0}),
          ("Window is whole array", {"prices": [5, 9, 7, 6, 8], "k": 4}), ("Strictly increasing", {"prices": list(range(1, 200)), "k": 10}),
          ("Zigzag with large k", {"prices": [0, 100] * 50, "k": 99}), ("Random walk n=30000, k=5", {"prices": walk, "k": 5}),
          ("Random walk n=30000, k=40", {"prices": walk, "k": 40}), ("Constant n=30000", {"prices": [3] * 30000, "k": 0}), ("Whole array stable, n=30000 (k huge)", {"prices": walk, "k": 10**9}), ("Slow ramp, n=30000, k=100000", {"prices": list(range(30000)), "k": 100000})]
    ex2 = [("Windows [10,12,11] and [15,13,12] have spread <= 3 (length 3); every length-4 window has spread >= 4", {"prices": [10, 12, 11, 15, 13, 12, 16], "k": 3}),
           ("All prices equal, so the whole array is stable", {"prices": [7, 7, 7, 7], "k": 0})]
    q2 = dsa_question("oa01-dsa-02", 250, "Longest Stable Price Window",
"""A surveillance system looks for the longest period in which a stock's price stayed "stable". Given a list of integer prices (one per tick, in time order) and an integer `k`, return the **length of the longest contiguous subarray** whose `max - min <= k`.""",
        ["1 <= len(prices) <= 10^5", "0 <= prices[i] <= 10^9", "0 <= k <= 10^9"], ex2,
        "longest_stable_window", "def longest_stable_window(prices: List[int], k: int) -> int",
        "from typing import List\n\ndef longest_stable_window(prices: List[int], k: int) -> int:\n    # TODO\n    pass\n",
        d2, REF_D2, BR_D2, gen_d2, "O(n) amortised using monotonic deques, O(n) space",
        ["An O(n^2) scan passes small tests but times out on n=30000 tests.", "Windows of length 1 and k=0 edge cases are covered."],
        "Sliding window with two monotonic deques: one tracks the window maximum (decreasing values), one the minimum (increasing). Extend the right end; while max - min > k move the left end and pop expired indices. Each index enters and leaves each deque once, so the total is O(n).",
        ["sliding window", "monotonic deque", "arrays"], "medium")
    # make example descriptions accurate after computing outputs
    return [q1, q2]
