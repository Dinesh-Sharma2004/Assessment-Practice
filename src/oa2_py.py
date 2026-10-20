import random
import numpy as np
import pandas as pd
from builder import pandas_question, dsa_question

NAN = float("nan")
CT = ["US", "GB", "DE", "IN", "JP"]

# ============================ PANDAS ============================
def tx(rows):
    return pd.DataFrame(rows, columns=["txn_id", "account_id", "txn_time", "amount", "merchant_country"]).astype(
        {"txn_id": "int64", "account_id": "int64", "amount": "float64"})

def ac(rows):
    return pd.DataFrame(rows, columns=["account_id", "risk_tier", "home_country"]).astype({"account_id": "int64"})

def rand_tx(seed, n=30, n_acc=5, bad=True):
    r = random.Random(seed); rows = []
    for i in range(1, n + 1):
        t = f"2025-02-{r.randrange(1, 6):02d} {r.randrange(0, 24):02d}:{r.randrange(0, 60):02d}:{r.randrange(0, 60):02d}"
        if bad and r.random() < 0.08: t = r.choice(["N/A", "2025-02-30 10:00:00", ""])
        rows.append((i, r.randrange(1, n_acc + 2), t, round(r.uniform(1, 900), 2), r.choice(CT)))
    if bad and rows:
        rows.append((rows[0][0],) + rows[1][1:])      # duplicated txn_id
    return tx(rows)

def rand_ac(seed, n_acc=5):
    r = random.Random(seed)
    return ac([(i, r.choice(["LOW", "MEDIUM", "HIGH"]), r.choice(CT)) for i in range(1, n_acc + 1)])

REF_P1 = '''import pandas as pd

def join_txn_features(txns, accounts):
    df = txns.copy()
    df["txn_time"] = pd.to_datetime(df["txn_time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["txn_time"]).drop_duplicates(subset="txn_id", keep="first")
    df = df.merge(accounts[["account_id", "risk_tier", "home_country"]], on="account_id", how="left")
    df["hour"] = df["txn_time"].dt.hour.astype("int64")
    df["is_night"] = (df["hour"] < 6) | (df["hour"] >= 22)
    df["is_foreign"] = (df["home_country"].notna() & (df["merchant_country"] != df["home_country"])).astype(bool)
    df["risk_tier"] = df["risk_tier"].fillna("UNKNOWN")
    return df.sort_values("txn_id")[["txn_id", "account_id", "amount", "hour", "is_night", "is_foreign", "risk_tier"]].reset_index(drop=True)
'''
def vel(rows):
    return pd.DataFrame(rows, columns=["txn_id", "account_id", "txn_time", "amount"]).astype({"txn_id": "int64", "account_id": "int64", "amount": "float64"})

def rand_vel(seed, n=30, n_acc=3):
    r = random.Random(seed); rows = []
    for i in range(1, n + 1):
        rows.append((i, r.randrange(1, n_acc + 1), f"2025-03-01 {r.randrange(8, 12):02d}:{r.randrange(0, 60, 5):02d}:00", round(r.uniform(5, 300), 2)))
    r.shuffle(rows)
    return vel(rows)

REF_P2 = '''import pandas as pd

def velocity_features(txns):
    df = txns.copy()
    df["txn_time"] = pd.to_datetime(df["txn_time"])
    df = df.sort_values(["account_id", "txn_time", "txn_id"], kind="mergesort").reset_index(drop=True)
    df["mins_since_prev"] = df.groupby("account_id")["txn_time"].diff().dt.total_seconds() / 60.0
    counts, sums = [], []
    for _, g in df.groupby("account_id", sort=False):
        t = g.set_index("txn_time")["amount"]
        roll = t.rolling("60min")          # window (t-60min, t], rows up to the current position only
        counts.append(roll.count().to_numpy()); sums.append(roll.sum().to_numpy())
    df["txn_count_1h"] = pd.Series(np.concatenate(counts) if counts else [], dtype="float64").astype("int64") if len(df) else pd.Series([], dtype="int64")
    df["amt_sum_1h"] = np.concatenate(sums) if sums else np.array([], dtype="float64")
    return df[["txn_id", "account_id", "mins_since_prev", "txn_count_1h", "amt_sum_1h"]]
'''.replace("import pandas as pd\n", "import pandas as pd\nimport numpy as np\n", 1)

def rs(rows):
    return pd.DataFrame(rows, columns=["account_id", "amount", "is_night"]).astype({"account_id": "int64", "amount": "float64", "is_night": "bool"})

def rand_rs(seed, n=40, n_acc=6):
    r = random.Random(seed)
    return rs([(r.randrange(1, n_acc + 1), NAN if r.random() < 0.12 else round(r.uniform(1, 500), 2), r.random() < 0.3) for _ in range(n)])

REF_P3 = '''import pandas as pd

def risk_summary(txns):
    df = txns.dropna(subset=["amount"]).copy()
    df["night_amount"] = df["amount"].where(df["is_night"], 0.0)
    out = (df.groupby("account_id", as_index=False)
             .agg(n_txn=("amount", "size"), total_amount=("amount", "sum"), max_amount=("amount", "max"),
                  pct_night=("is_night", "mean"), night_total=("night_amount", "sum")))
    out = out[out["n_txn"] >= 2]
    return out.sort_values(["total_amount", "account_id"], ascending=[False, True]).reset_index(drop=True)
'''

def build_pandas():
    qs = []
    a1 = ac([(1, "LOW", "US"), (2, "HIGH", "DE"), (3, "MEDIUM", "IN")])
    t1 = tx([(5, 1, "2025-02-01 23:30:00", 40.0, "US"), (1, 2, "2025-02-01 05:59:59", 900.0, "FR" if False else "GB"), (2, 2, "2025-02-01 06:00:00", 15.5, "DE"),
             (3, 4, "2025-02-02 12:00:00", 60.0, "US"), (4, 1, "oops", 10.0, "US"), (6, 3, "2025-02-02 22:00:00", 80.0, "JP"), (2, 1, "2025-02-03 01:00:00", 5.0, "US")])
    a2 = ac([(7, "HIGH", "US")])
    t2 = tx([(10, 9, "2025-02-04 00:00:00", 1.0, "US"), (11, 7, "2025-02-04 21:59:59", 2.0, "US")])
    d1 = [("Sample: unknown account, bad timestamp, duplicate id, boundary hours", {"txns": t1, "accounts": a1}, {}),
          ("Unknown account only and a US customer shopping in the US", {"txns": t2, "accounts": a2}, {}),
          ("No transactions", {"txns": tx([]), "accounts": a1}, {}),
          ("Randomised", {"txns": rand_tx(41), "accounts": rand_ac(41)}, {}),
          ("Randomised larger", {"txns": rand_tx(42, 80, 8), "accounts": rand_ac(42, 8)}, {}),
          ("Randomised no bad rows", {"txns": rand_tx(43, 50, 4, bad=False), "accounts": rand_ac(43, 4)}, {})]
    qs.append(pandas_question("oa02-pd-01", 150, "Join Transactions to Account Risk Features",
"""Implement `join_txn_features(txns, accounts)` that enriches transactions with account attributes and simple time/geography flags.

1. Parse `txn_time` using format `%Y-%m-%d %H:%M:%S`; **drop** rows that cannot be parsed.
2. If a `txn_id` occurs more than once, **keep the first occurrence** (in input order).
3. **Left-join** `accounts` (unique `account_id`; columns `risk_tier`, `home_country`) onto the transactions.
4. Create `hour` (0–23, int64), `is_night` (`hour < 6` or `hour >= 22`) and `is_foreign` (`True` only when the account is known and `merchant_country != home_country`; `False` for unknown accounts).
5. Fill missing `risk_tier` with `'UNKNOWN'`.

Return columns `txn_id, account_id, amount, hour, is_night, is_foreign, risk_tier` sorted by `txn_id`, with default index.""",
        "join_txn_features", "def join_txn_features(txns: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef join_txn_features(txns: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:\n    df = txns.copy()\n    # TODO\n    return df\n",
        {"txns": [("txn_id", "int64", "Transaction id (may repeat)"), ("account_id", "int64", "Account id"), ("txn_time", "str", "Timestamp text"), ("amount", "float64", "Amount"), ("merchant_country", "str", "Country code")],
         "accounts": [("account_id", "int64", "Unique account id"), ("risk_tier", "str", "LOW/MEDIUM/HIGH"), ("home_country", "str", "Home country code")]},
        d1, REF_P1, "Columns [txn_id int64, account_id int64, amount float64, hour int64, is_night bool, is_foreign bool, risk_tier str], sorted by txn_id.",
        ["Unknown accounts must remain (left join) with 'UNKNOWN' and is_foreign False.", "Boundary hours 05:59:59 / 06:00:00 / 21:59:59 / 22:00:00 are tested."],
        "Parse with errors='coerce' and drop NaT, deduplicate on txn_id, left-merge accounts. The boolean flags are vectorised comparisons; unknown accounts have NaN home_country so notna() makes is_foreign False.",
        ["merge", "datetime", "boolean features"], "medium"))
    v1 = vel([(1, 1, "2025-03-01 10:00:00", 10.0), (2, 1, "2025-03-01 10:30:00", 20.0), (3, 1, "2025-03-01 11:00:00", 30.0), (4, 1, "2025-03-01 11:01:00", 5.0),
              (5, 2, "2025-03-01 09:00:00", 100.0), (6, 2, "2025-03-01 09:00:00", 50.0), (7, 2, "2025-03-01 12:00:00", 1.0)])
    v2 = vel([(9, 3, "2025-03-02 08:00:00", 7.0)])
    d2 = [("Sample: window excludes exactly 60 minutes old rows; shared timestamps", {"txns": v1}, {}), ("Single transaction", {"txns": v2}, {}),
          ("Empty input", {"txns": vel([])}, {}), ("Randomised", {"txns": rand_vel(61)}, {}), ("Randomised larger", {"txns": rand_vel(62, 80, 5)}, {}),
          ("Randomised dense", {"txns": rand_vel(63, 60, 2)}, {})]
    qs.append(pandas_question("oa02-pd-02", 150, "Velocity Features per Account",
"""Fraud models use *velocity* features. Implement `velocity_features(txns)`.

Parse `txn_time` to datetime and sort by `account_id`, `txn_time`, `txn_id` (this order defines "earlier rows"). For each row compute, **within the same account**:

* `mins_since_prev` – minutes since the previous row of that account (float; `NaN` for the account's first row; 0.0 for equal timestamps);
* `txn_count_1h` – number of rows of that account that are at or before the current row in the sorted order **and** have `txn_time > current_time - 60 minutes` (the current row counts; a row exactly 60 minutes old does not);
* `amt_sum_1h` – the sum of `amount` over those same rows.

Return `txn_id, account_id, mins_since_prev, txn_count_1h (int64), amt_sum_1h` in the sorted order, default index.""",
        "velocity_features", "def velocity_features(txns: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef velocity_features(txns: pd.DataFrame) -> pd.DataFrame:\n    df = txns.copy()\n    # TODO\n    return df\n",
        {"txns": [("txn_id", "int64", "Unique id"), ("account_id", "int64", "Account"), ("txn_time", "str", "'YYYY-MM-DD HH:MM:SS'"), ("amount", "float64", "Amount")]},
        d2, REF_P2, "Columns [txn_id int64, account_id int64, mins_since_prev float64, txn_count_1h int64, amt_sum_1h float64].",
        ["Strict 60-minute window (exactly 60 minutes old is excluded) is tested.", "Rolling must not leak across accounts."],
        "Sort, use groupby().diff() for the gap and a time-based rolling('60min') per account. pandas' default window is (t-60min, t], which matches the specification and excludes rows exactly 60 minutes old; equal timestamps only see earlier rows in the sort order.",
        ["rolling", "groupby", "timestamps"], "hard"))
    r1 = rs([(1, 100.0, False), (1, 50.0, True), (1, NAN, True), (2, 10.0, True), (3, 5.0, False), (3, 7.0, False), (3, 9.0, True), (4, 1000.0, True), (2, 90.0, True)])
    r2 = rs([(5, 20.0, False), (6, 20.0, True), (6, 20.0, False), (5, 20.0, True)])
    d3 = [("Sample: NaN amount dropped, single-transaction account excluded", {"txns": r1}, {}), ("Equal totals tie-break on account_id", {"txns": r2}, {}),
          ("All excluded (empty result)", {"txns": rs([(1, NAN, True), (2, 5.0, False)])}, {}), ("Randomised", {"txns": rand_rs(71)}, {}),
          ("Randomised larger", {"txns": rand_rs(72, 120, 10)}, {}), ("Randomised small", {"txns": rand_rs(73, 15, 6)}, {})]
    qs.append(pandas_question("oa02-pd-03", 100, "Account Risk Summary",
"""Implement `risk_summary(txns)`.

1. Drop rows whose `amount` is missing.
2. Group by `account_id` and compute `n_txn` (row count), `total_amount` (sum), `max_amount` (max), `pct_night` (fraction of rows with `is_night == True`) and `night_total` (sum of `amount` over night rows; 0.0 if none).
3. Keep accounts with `n_txn >= 2`.
4. Sort by `total_amount` descending, then `account_id` ascending; return columns in the order listed above after `account_id`, with default index.""",
        "risk_summary", "def risk_summary(txns: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef risk_summary(txns: pd.DataFrame) -> pd.DataFrame:\n    df = txns.copy()\n    # TODO\n    return df\n",
        {"txns": [("account_id", "int64", "Account"), ("amount", "float64", "Amount; may be NaN"), ("is_night", "bool", "True for night-time transactions")]},
        d3, REF_P3, "Columns [account_id int64, n_txn int64, total_amount float64, max_amount float64, pct_night float64, night_total float64].",
        ["The NaN-drop must happen before counting n_txn.", "Empty result keeps column names."],
        "Named aggregation on the cleaned frame; a helper column masks non-night amounts so night_total is a plain sum. Filtering n_txn >= 2 happens after aggregation.",
        ["groupby", "named aggregation", "sorting"], "medium"))
    return qs

# ============================ DSA ============================
REF_D1 = '''from typing import List
from collections import Counter

def count_balanced_substrings(s: str) -> int:
    bal, seen, total = 0, Counter({0: 1}), 0
    for ch in s:
        if ch == "F":
            bal += 1
        elif ch == "N":
            bal -= 1
        total += seen[bal]
        seen[bal] += 1
    return total
'''
BR_D1 = '''def count_balanced_substrings(s):
    n = len(s); c = 0
    for i in range(n):
        f = nn = 0
        for j in range(i, n):
            f += s[j] == "F"; nn += s[j] == "N"
            c += f == nn
    return c
'''
def gen_d1(r):
    return {"s": "".join(r.choice("FNFNxy") for _ in range(r.randrange(1, 14)))}

REF_D2 = '''from typing import List

def min_audit_times(windows: List[List[int]]) -> int:
    iv = sorted(windows, key=lambda w: (w[1], -w[0]))
    a = b = -10**18            # the two latest chosen times, a < b
    count = 0
    for s, e in iv:
        if s > b:              # no chosen time inside the window
            count += 2; a, b = e - 1, e
        elif s > a:            # only b is inside
            count += 1; a, b = b, e
    return count
'''
BR_D2 = '''from itertools import combinations
def min_audit_times(windows):
    lo = min(w[0] for w in windows); hi = max(w[1] for w in windows)
    times = list(range(lo, hi + 1))
    for k in range(2, len(times) + 1):
        for c in combinations(times, k):
            if all(sum(s <= t <= e for t in c) >= 2 for s, e in windows):
                return k
'''
def gen_d2(r):
    n = r.randrange(1, 6); w = []
    for _ in range(n):
        s = r.randrange(0, 8); e = r.randrange(s + 1, 10); w.append([s, e])
    return {"windows": w}

def build_dsa():
    r = random.Random(77)
    big_s = "".join(r.choice("FNFNabc") for _ in range(100000))
    runs = "F" * 50000 + "N" * 50000
    alt = "FN" * 50000
    d1 = [("Example 1", {"s": "FNFN"}), ("Example 2", {"s": "FFNNx"}), ("No F or N at all", {"s": "abcd"}), ("Only F", {"s": "FFFF"}),
          ("Single N", {"s": "N"}), ("Interleaved noise", {"s": "aFbNcNdFeFfNg"}), ("All F then all N, n=100000", {"s": runs}),
          ("Alternating, n=100000", {"s": alt}), ("Random noise, n=100000", {"s": big_s}), ("All letters, n=100000", {"s": "z" * 100000})]
    q1 = dsa_question("oa02-dsa-01", 200, "Balanced Fraud/Normal Windows",
"""A stream of events is encoded as a string: `'F'` = flagged-fraud event, `'N'` = confirmed-normal event, and any other lowercase letter is an unrelated event. A **window** is a non-empty contiguous substring.

Return the number of windows that contain **exactly as many `'F'` as `'N'` characters** (windows containing neither count, because 0 = 0). Count windows by position: identical substrings at different positions are different windows.""",
        ["1 <= len(s) <= 2 * 10^5", "s consists of lowercase letters and uppercase 'F' and 'N'"],
        [("Windows: FN, NF, FN and FNFN -> 4", {"s": "FNFN"}), ("see below", {"s": "FFNNx"})],
        "count_balanced_substrings", "def count_balanced_substrings(s: str) -> int",
        "def count_balanced_substrings(s: str) -> int:\n    # TODO\n    pass\n",
        d1, REF_D1, BR_D1, gen_d1, "O(n) time, O(n) space (prefix balance + hash map)",
        ["An O(n^2) enumeration passes small tests and fails the n = 100000 tests.", "All-neutral strings test that zero-balance windows are counted."],
        "Let balance = (#F - #N) over a prefix. A window (i, j] is balanced exactly when prefix balances at i and j are equal. Scan once, keeping a hash map from balance to number of earlier prefixes with that balance; each new prefix adds that many windows.",
        ["strings", "hash map", "prefix sums"], "medium")
    # fix example descriptions with accurate text
    q1["examples"][1]["description"] = "'FFNN' (whole minus x), 'FN' (middle) and 'x' alone are balanced, plus 'FFNNx' itself -> 4 windows"
    q1["examples"][0]["description"] = "Balanced windows: 'FN' (twice), 'NF', and 'FNFN' -> 4"
    big = [[(a := r.randrange(0, 10**9 - 10**6)), a + r.randrange(1, 10**6)] for _ in range(40000)]
    mid = [[(a := r.randrange(0, 5000)), a + r.randrange(1, 40)] for _ in range(30000)]
    d2 = [("Example 1", {"windows": [[1, 3], [3, 7], [5, 8]]}), ("Example 2", {"windows": [[1, 2], [1, 2], [1, 2]]}), ("Single window", {"windows": [[4, 9]]}),
          ("Nested windows", {"windows": [[0, 10], [2, 3], [1, 8], [4, 5]]}), ("Same end different starts", {"windows": [[1, 5], [3, 5], [4, 5], [0, 5]]}),
          ("Chain of adjacent windows", {"windows": [[i, i + 1] for i in range(0, 200, 2)]}), ("Overlapping chain", {"windows": [[i, i + 3] for i in range(100)]}),
          ("Random n=30000 small coordinates", {"windows": mid}), ("Random n=40000 large coordinates", {"windows": big}),
          ("Unsorted input", {"windows": [[8, 9], [0, 1], [4, 6], [2, 7], [5, 9]]})]
    q2 = dsa_question("oa02-dsa-02", 250, "Minimum Audit Checkpoints",
"""Each transaction batch has an audit window `[start, end]` (inclusive integer times, `start < end`). An auditor can sample the system at chosen **distinct integer times**. Every window must contain **at least two** of the chosen times.

Return the minimum number of distinct times that must be chosen so that every window contains at least two of them. Windows may be given in any order and may repeat.""",
        ["1 <= len(windows) <= 10^5", "0 <= start < end <= 10^9"],
        [("Choosing times 2, 3, 5, 6 puts two chosen times in each window; three times are not enough -> 4", {"windows": [[1, 3], [3, 7], [5, 8]]}), ("Identical windows share the same two times", {"windows": [[1, 2], [1, 2], [1, 2]]})],
        "min_audit_times", "def min_audit_times(windows: List[List[int]]) -> int",
        "from typing import List\n\ndef min_audit_times(windows: List[List[int]]) -> int:\n    # TODO\n    pass\n",
        d2, REF_D2, BR_D2, gen_d2, "O(n log n) time (sorting), O(1) extra space",
        ["Brute force over subsets only works for tiny coordinate ranges and times out on the large tests.", "Common mistakes (tracking only the latest chosen time, or choosing only the right endpoint) are exercised by the nested and same-end tests."],
        "Greedy: sort windows by right end (ties: larger start first). Maintain the two most recently chosen times a < b. If the next window contains neither, choose its last two points (e-1, e); if it contains only b, choose e. Choosing as late as possible leaves maximum overlap with later windows, which is optimal by an exchange argument.",
        ["greedy", "intervals", "sorting"], "hard")
    return [q1, q2]
