import random
from datetime import date, timedelta
from fractions import Fraction
from builder import sql_question
from oa1_sql import _half

SCHEMA = """CREATE TABLE Securities (
  security_id INTEGER PRIMARY KEY,
  ticker      TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL
);
CREATE TABLE DailyPrices (
  security_id INTEGER NOT NULL REFERENCES Securities(security_id),
  price_date  TEXT NOT NULL,           -- 'YYYY-MM-DD'
  close       REAL,                    -- NULL when the close is missing
  volume      INTEGER NOT NULL,
  PRIMARY KEY (security_id, price_date)
);
CREATE TABLE SectorMap (
  security_id INTEGER PRIMARY KEY REFERENCES Securities(security_id),
  sector      TEXT NOT NULL
);
CREATE TABLE Benchmarks (
  sector      TEXT NOT NULL,
  bench_date  TEXT NOT NULL,           -- 'YYYY-MM-DD'
  bench_close REAL,                    -- NULL when missing
  PRIMARY KEY (sector, bench_date)
);"""
TABLES = [
 {"name": "Securities", "description": "Listed securities.", "columns": [
   {"name": "security_id", "type": "INTEGER", "description": "Primary key"}, {"name": "ticker", "type": "TEXT", "description": "Unique ticker"}, {"name": "name", "type": "TEXT", "description": "Company name"}]},
 {"name": "DailyPrices", "description": "One row per security per trading date.", "columns": [
   {"name": "security_id", "type": "INTEGER", "description": "FK to Securities (part of PK)"}, {"name": "price_date", "type": "TEXT", "description": "'YYYY-MM-DD' (part of PK)"},
   {"name": "close", "type": "REAL", "description": "Closing price; NULL if missing"}, {"name": "volume", "type": "INTEGER", "description": "Shares traded"}]},
 {"name": "SectorMap", "description": "Sector of each security.", "columns": [
   {"name": "security_id", "type": "INTEGER", "description": "PK and FK to Securities"}, {"name": "sector", "type": "TEXT", "description": "Sector name"}]},
 {"name": "Benchmarks", "description": "Daily sector benchmark index levels.", "columns": [
   {"name": "sector", "type": "TEXT", "description": "Sector name (part of PK)"}, {"name": "bench_date", "type": "TEXT", "description": "'YYYY-MM-DD' (part of PK)"},
   {"name": "bench_close", "type": "REAL", "description": "Index level; NULL if missing"}]},
]
SEC = [(1, "ALFA", "Alfa Systems"), (2, "BRVO", "Bravo Pharma"), (3, "CHRL", "Charlie Energy"), (4, "DLTA", "Delta Logistics"), (5, "ECHO", "Echo Semis"), (6, "FOXT", "Foxtrot Retail")]
SECT = ["Tech", "Health", "Energy"]


def bdays(start, end):
    d, out = start, []
    while d <= end:
        if d.weekday() < 5: out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def gen(seed, n_sec=5, p_null=0.12, p_gap=0.08, wide=True, flat=False):
    r = random.Random(seed)
    secs = SEC[:n_sec]
    days = bdays(date(2023, 12, 27), date(2024, 2, 5)) if wide else bdays(date(2024, 1, 2), date(2024, 1, 19))
    secmap = [(s[0], SECT[(s[0] - 1) % 3]) for s in secs]
    prices, bench = [], []
    for s in secs:
        px = r.randrange(2000, 20000)
        for d in days:
            px = max(100, px + r.randrange(-300, 300))
            if r.random() < p_gap: continue
            prices.append((s[0], d, None if r.random() < p_null else round(px / 100, 2), r.randrange(100, 9000)))
    for sec in SECT:
        lv = r.randrange(50000, 90000)
        for d in days:
            lv = max(1000, lv + r.randrange(-400, 400))
            if r.random() < p_gap / 2: continue
            bench.append((sec, d, None if r.random() < p_null / 2 else round(lv / 100, 2)))
    return {"Securities": secs, "DailyPrices": prices, "SectorMap": secmap, "Benchmarks": bench}


def F(x): return Fraction(str(x))

def jan(d): return "2024-01-01" <= d[1] <= "2024-01-31"

def guard_q1(d):
    by = {}
    for p in d["DailyPrices"]:
        if p[2] is not None and jan(p): by.setdefault(p[0], []).append(F(p[2]))
    for v in by.values():
        if len(v) >= 3 and min(v) > 0 and _half((max(v) - min(v)) * 100 / min(v), 2): return False
    return True

def rets(rows):
    out, prev = {}, None
    for row in rows:
        dt, c = row[1], row[2]
        if c is None: continue
        if prev is not None: out[dt] = F(c) / prev - 1
        prev = F(c)
    return out

def q2_pairs(d):
    sec = dict(d["SectorMap"]); res = {}
    bmap = {}
    for s in set(sec.values()):
        bmap[s] = rets(sorted([(x[0], x[1], x[2]) for x in d["Benchmarks"] if x[0] == s], key=lambda x: x[1]))
    for sid in sec:
        sr = rets(sorted([p for p in d["DailyPrices"] if p[0] == sid], key=lambda p: p[1]))
        res[sid] = [(sr[x], bmap[sec[sid]][x]) for x in sr if x in bmap[sec[sid]]]
    return res

def guard_q2(d):
    for sid, pairs in q2_pairs(d).items():
        for a, b in pairs:
            if abs(a - b) < Fraction(1, 10**8): return False
        if pairs and _half(sum(a - b for a, b in pairs) / len(pairs), 6): return False
    return True

def pick(guard, seed0, **kw):
    for s in range(seed0, seed0 + 800):
        d = gen(s, **kw)
        if guard(d): return d
    raise RuntimeError

W1 = {"Securities": SEC[:4],
      "DailyPrices": [
        (1, "2023-12-29", 49.00, 100), (1, "2024-01-02", 50.00, 900), (1, "2024-01-03", 52.00, 800), (1, "2024-01-04", None, 700), (1, "2024-01-05", 49.50, 650), (1, "2024-01-31", 55.00, 500), (1, "2024-02-01", 90.00, 100),
        (2, "2024-01-02", 20.00, 100), (2, "2024-01-03", 21.00, 100), (2, "2024-01-04", 19.00, 100),
        (3, "2024-01-02", 10.00, 50), (3, "2024-01-03", 12.50, 60), (3, "2024-01-04", 12.50, 70), (3, "2024-01-05", 10.00, 80),
        (4, "2024-01-02", None, 10), (4, "2024-01-03", None, 10), (4, "2024-01-04", 5.00, 10), (4, "2024-01-05", 5.50, 10)],
      "SectorMap": [(1, "Tech"), (2, "Health"), (3, "Energy"), (4, "Energy")],
      "Benchmarks": [("Tech", "2024-01-02", 1000.0), ("Tech", "2024-01-03", 1010.0), ("Tech", "2024-01-04", 1020.1), ("Tech", "2024-01-05", 1000.0),
                     ("Health", "2024-01-02", 200.0), ("Health", "2024-01-03", 202.0), ("Health", "2024-01-04", 198.0),
                     ("Energy", "2024-01-02", 300.0), ("Energy", "2024-01-03", 303.0), ("Energy", "2024-01-04", 306.03), ("Energy", "2024-01-05", 303.0)]}
W2 = {"Securities": SEC[:3],
      "DailyPrices": [(1, "2024-01-08", 10.00, 1), (1, "2024-01-09", 10.40, 1), (1, "2024-01-10", 10.80, 1), (1, "2024-01-11", 11.00, 1), (1, "2024-01-12", 11.40, 1),
                      (2, "2024-01-08", 30.00, 1), (2, "2024-01-10", 31.50, 1), (2, "2024-01-11", 31.00, 1), (2, "2024-01-12", None, 1),
                      (3, "2024-01-08", 8.00, 1), (3, "2024-01-09", None, 1), (3, "2024-01-10", None, 1), (3, "2024-01-11", 8.40, 1), (3, "2024-01-12", 8.80, 1)],
      "SectorMap": [(1, "Tech"), (2, "Health"), (3, "Tech")],
      "Benchmarks": [("Tech", "2024-01-08", 100.0), ("Tech", "2024-01-09", 101.0), ("Tech", "2024-01-10", 103.0), ("Tech", "2024-01-11", 102.0), ("Tech", "2024-01-12", 104.0),
                     ("Health", "2024-01-08", 50.0), ("Health", "2024-01-09", 50.5), ("Health", "2024-01-10", 51.0), ("Health", "2024-01-11", None), ("Health", "2024-01-12", 52.0)]}
EMPTY = {"Securities": SEC[:2], "DailyPrices": [(1, "2024-01-02", 10.0, 1), (1, "2024-01-03", 11.0, 1), (2, "2024-02-01", 10.0, 1)], "SectorMap": [(1, "Tech")], "Benchmarks": []}
TIES = {"Securities": SEC[:3],
        "DailyPrices": [(1, "2024-01-02", 10.0, 1), (1, "2024-01-03", 12.0, 1), (1, "2024-01-04", 11.0, 1), (1, "2024-01-05", 12.0, 1),
                        (2, "2024-01-02", 20.0, 1), (2, "2024-01-03", 24.0, 1), (2, "2024-01-04", 22.0, 1),
                        (3, "2024-01-02", 5.0, 1), (3, "2024-01-03", 6.0, 1), (3, "2024-01-04", 5.5, 1), (3, "2024-01-05", 6.0, 1)],
        "SectorMap": [(1, "Tech"), (2, "Tech"), (3, "Health")], "Benchmarks": [("Tech", "2024-01-02", 100.0), ("Tech", "2024-01-03", 101.0), ("Tech", "2024-01-04", 99.0), ("Tech", "2024-01-05", 100.5)]}


def build():
    qs = []
    q1_sets = [("Sample data from the statement", W1), ("Second sample", W2), ("Nothing qualifies (empty result)", EMPTY), ("Ties in range_pct (tie-break by ticker) and repeated highs", TIES),
               ("Randomised", pick(guard_q1, 100)), ("Randomised larger", pick(guard_q1, 300, n_sec=6, wide=True, p_null=0.2))]
    ref1 = """WITH j AS (
  SELECT s.security_id, s.ticker, p.price_date, p.close
  FROM Securities s
  JOIN DailyPrices p ON p.security_id = s.security_id
  WHERE p.close IS NOT NULL
    AND p.price_date BETWEEN '2024-01-01' AND '2024-01-31'
),
agg AS (
  SELECT security_id, ticker, COUNT(*) AS n, MAX(close) AS hi, MIN(close) AS lo
  FROM j GROUP BY security_id, ticker
  HAVING COUNT(*) >= 3 AND MIN(close) > 0
)
SELECT agg.ticker, agg.n AS trading_days, agg.hi AS high_close, agg.lo AS low_close,
       ROUND((agg.hi - agg.lo) * 100.0 / agg.lo, 2) AS range_pct,
       (SELECT MIN(j.price_date) FROM j WHERE j.security_id = agg.security_id AND j.close = agg.hi) AS high_date
FROM agg
ORDER BY range_pct DESC, agg.ticker ASC;"""
    qs.append(sql_question("oa04-sql-01", "select", 200, "January Price Range Report",
"""Using `Securities` and `DailyPrices`, build a January 2024 price-range report. Consider only rows with `price_date` from `'2024-01-01'` to `'2024-01-31'` (inclusive) and a **non-NULL** `close`.

Return one row per security with **at least 3** such rows and a minimum close above 0:

`ticker, trading_days, high_close, low_close, range_pct, high_date`

* `trading_days` – number of qualifying rows
* `high_close` / `low_close` – maximum / minimum close
* `range_pct` – `(high_close - low_close) / low_close * 100`, rounded to 2 decimals
* `high_date` – the **earliest** date on which `high_close` occurred

Sort by `range_pct` descending, then `ticker` ascending.""",
        TABLES[:2], SCHEMA, q1_sets,
        "SELECT s.ticker, COUNT(*) AS trading_days, MAX(p.close) AS high_close, MIN(p.close) AS low_close, 0.0 AS range_pct, '' AS high_date\nFROM Securities s\nJOIN DailyPrices p ON p.security_id = s.security_id\n-- TODO\nGROUP BY s.security_id, s.ticker;",
        ref1, "Columns, in order: ticker, trading_days, high_close, low_close, range_pct, high_date (text). Order: range_pct DESC, ticker ASC.",
        ["Dates outside January (Dec 2023, Feb 2024) are present in tests.", "NULL closes must not count as trading days.", "high_date must be the earliest date when the maximum repeats."],
        "Filter to non-NULL January closes, aggregate per security and keep groups via HAVING; fetch the earliest date of the maximum with a correlated subquery over the filtered rows (or a window function). BETWEEN on ISO date text is inclusive on both ends.",
        ["joins", "aggregation", "correlated subquery", "date filtering"], "medium"))
    q2_sets = [("Sample data from the statement", W1), ("Second sample with gaps and NULL closes", W2), ("No benchmark rows (empty result)", EMPTY), ("Single sector, partial overlap", TIES),
               ("Randomised", pick(guard_q2, 500, n_sec=4, wide=False)), ("Randomised larger", pick(guard_q2, 700, n_sec=6, wide=False, p_null=0.2))]
    ref2 = """WITH sr AS (
  SELECT security_id, price_date,
         close * 1.0 / LAG(close) OVER (PARTITION BY security_id ORDER BY price_date) - 1 AS ret
  FROM DailyPrices WHERE close IS NOT NULL
),
br AS (
  SELECT sector, bench_date,
         bench_close * 1.0 / LAG(bench_close) OVER (PARTITION BY sector ORDER BY bench_date) - 1 AS ret
  FROM Benchmarks WHERE bench_close IS NOT NULL
)
SELECT sr.security_id, m.sector,
       COUNT(*) AS days,
       ROUND(AVG(sr.ret - br.ret), 6) AS avg_excess,
       SUM(CASE WHEN sr.ret > br.ret THEN 1 ELSE 0 END) AS days_outperformed
FROM sr
JOIN SectorMap m ON m.security_id = sr.security_id
JOIN br ON br.sector = m.sector AND br.bench_date = sr.price_date
WHERE sr.ret IS NOT NULL AND br.ret IS NOT NULL
GROUP BY sr.security_id, m.sector
ORDER BY avg_excess DESC, sr.security_id ASC;"""
    qs.append(sql_question("oa04-sql-02", "select", 150, "Excess Return versus Sector Benchmark",
"""Compare each security's daily return with its sector benchmark using `DailyPrices`, `SectorMap` and `Benchmarks`.

* A security's **return** on a date is `close / previous_close - 1`, where `previous_close` is the close of the **previous row of that security that has a non-NULL close** (rows with NULL close are ignored entirely).
* A benchmark's return is defined the same way from `bench_close` per `sector` (ignoring NULL benchmark levels).
* A date is *comparable* when both the security and its sector benchmark have a non-NULL return on that date.

For every security with at least one comparable date return:

`security_id, sector, days, avg_excess, days_outperformed`

* `days` – number of comparable dates
* `avg_excess` – average of `(security return - benchmark return)`, rounded to 6 decimals
* `days_outperformed` – number of comparable dates on which the security return is strictly greater than the benchmark return

Sort by `avg_excess` descending, then `security_id` ascending.""",
        [TABLES[1], TABLES[2], TABLES[3]], SCHEMA, q2_sets,
        "SELECT p.security_id, m.sector, COUNT(*) AS days, 0.0 AS avg_excess, 0 AS days_outperformed\nFROM DailyPrices p\nJOIN SectorMap m ON m.security_id = p.security_id\n-- TODO: LAG-based returns for security and benchmark\nGROUP BY p.security_id, m.sector;",
        ref2, "Columns, in order: security_id, sector, days, avg_excess, days_outperformed. Order: avg_excess DESC, security_id ASC.",
        ["LAG must be applied after removing NULL closes (previous available close).", "Benchmark returns are computed per sector, not across sectors.", "Strict outperformance comparison."],
        "Two CTEs compute returns with LAG over the NULL-filtered rows of each series (partitioned by security and by sector). Joining them on sector/date and averaging the difference gives the requested statistics; windows must be computed before the join so the neighbouring row is the previous *available* observation.",
        ["window functions", "LAG", "joins", "time series"], "hard"))
    q3_sets = [("Sample data from the statement", W1), ("Second sample", W2), ("No NULL closes (no change)", TIES), ("Leading NULLs remain NULL", EMPTY | {"DailyPrices": [(1, "2024-01-02", None, 1), (1, "2024-01-03", None, 1), (1, "2024-01-04", 5.0, 1), (1, "2024-01-05", None, 1), (1, "2024-01-08", None, 1), (2, "2024-01-02", 7.0, 1), (2, "2024-01-03", None, 1)]}),
               ("Randomised", gen(900, p_null=0.3)), ("Randomised larger", gen(901, n_sec=6, p_null=0.4))]
    ref3 = """UPDATE DailyPrices
SET close = (SELECT p2.close
             FROM DailyPrices p2
             WHERE p2.security_id = DailyPrices.security_id
               AND p2.price_date  < DailyPrices.price_date
               AND p2.close IS NOT NULL
             ORDER BY p2.price_date DESC
             LIMIT 1)
WHERE close IS NULL
  AND EXISTS (SELECT 1 FROM DailyPrices p3
              WHERE p3.security_id = DailyPrices.security_id
                AND p3.price_date < DailyPrices.price_date
                AND p3.close IS NOT NULL);"""
    qs.append(sql_question("oa04-sql-03", "update", 100, "Carry Forward Missing Closes",
"""Repair missing closing prices in `DailyPrices` by **carrying forward**: for every row whose `close` is NULL, set `close` to the `close` of the **most recent earlier row (smaller `price_date`) of the same security that has a non-NULL close**.

Rows with no earlier non-NULL close must stay NULL. Rows that already have a close, and all other columns and tables, must not change. A run of several consecutive NULL days all receive the same carried-forward value.""",
        TABLES, SCHEMA, q3_sets,
        "UPDATE DailyPrices\nSET close = close  -- TODO: correlated subquery for the latest earlier non-NULL close\nWHERE close IS NULL;",
        ref3, "Final contents of DailyPrices (all columns) plus Securities, SectorMap and Benchmarks must match the expected state.",
        ["Leading NULLs must remain NULL (not 0, not later values).", "Consecutive NULL runs: all take the last valid value.", "Existing closes must be untouched."],
        "A correlated scalar subquery with ORDER BY price_date DESC LIMIT 1 over earlier non-NULL rows of the same security returns the latest valid close; if none exists it returns NULL, which is exactly the required behaviour for leading gaps (the extra EXISTS only avoids pointless writes). Carry-forward is idempotent, so the order in which rows are updated does not matter.",
        ["UPDATE", "correlated subquery", "time series", "NULL handling"], "medium",
        check_queries=[{"id": "prices", "sql": "SELECT * FROM DailyPrices ORDER BY security_id, price_date"}, {"id": "bench", "sql": "SELECT * FROM Benchmarks ORDER BY sector, bench_date"},
                       {"id": "secs", "sql": "SELECT * FROM Securities ORDER BY security_id"}]))
    return qs
