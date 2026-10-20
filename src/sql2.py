"""New SQL questions for the v2 banks (1-table and 4-table), built with the same builder."""
import random
from fractions import Fraction

import oa1_sql as S1
import oa2_sql as S2
import oa3_sql as S3
import oa4_sql as S4
import oa5_sql as S5
from builder import sql_question
from oa1_sql import _half

TR_SCHEMA = """CREATE TABLE Trades (
  trade_id    INTEGER PRIMARY KEY,
  security_id INTEGER NOT NULL,
  trader_id   INTEGER NOT NULL,
  trade_date  TEXT NOT NULL,          -- 'YYYY-MM-DD'
  side        TEXT NOT NULL CHECK (side IN ('BUY','SELL')),
  quantity    INTEGER NOT NULL CHECK (quantity > 0),
  price       REAL NOT NULL,
  status      TEXT NOT NULL CHECK (status IN ('FILLED','PENDING','REJECTED','CANCELLED'))
);"""
TX_SCHEMA = """CREATE TABLE Transactions (
  txn_id           INTEGER PRIMARY KEY,
  account_id       INTEGER NOT NULL,
  txn_time         TEXT NOT NULL,        -- 'YYYY-MM-DD HH:MM:SS'
  amount           REAL NOT NULL,        -- negative = refund
  channel          TEXT NOT NULL,        -- 'POS', 'ONLINE' or 'ATM'
  merchant_country TEXT NOT NULL
);"""


def trades_only(d):
    return {"Trades": d["Trades"]}


def build_n1():
    """OA1 / 1 table: Trades."""
    sets = [("Sample data from the statement", trades_only(S1.SAMPLE)), ("Second sample", trades_only(S1.SAMPLE2)), ("No trader has two filled trades (empty result)", {"Trades": [(1, 1, 7, "2024-03-01", "BUY", 10, 5.0, "FILLED"), (2, 1, 8, "2024-03-01", "SELL", 10, 5.0, "PENDING")]}),
            ("Tie on total_shares broken by trader_id", {"Trades": [(1, 1, 9, "2024-03-01", "BUY", 50, 5.0, "FILLED"), (2, 1, 9, "2024-03-02", "BUY", 50, 5.0, "FILLED"), (3, 1, 4, "2024-03-01", "BUY", 60, 5.0, "FILLED"), (4, 1, 4, "2024-03-02", "SELL", 40, 5.0, "FILLED"), (5, 1, 4, "2024-03-03", "SELL", 40, 5.0, "REJECTED")]}),
            ("Randomised", trades_only(S1.gen(41, n_trades=60))), ("Randomised larger", trades_only(S1.gen(42, n_trades=150)))]
    ref = """SELECT trader_id,
       COUNT(*)      AS filled_trades,
       SUM(quantity) AS total_shares
FROM Trades
WHERE status = 'FILLED'
GROUP BY trader_id
HAVING COUNT(*) >= 2
ORDER BY total_shares DESC, trader_id ASC;"""
    return sql_question("n1", "select", 100, "Busiest Traders",
"""The operations team wants to know which traders are most active.

Using the `Trades` table, count only trades whose `status` is `'FILLED'`. For each trader who has **at least 2** filled trades return:

`trader_id, filled_trades, total_shares`

* `filled_trades` – number of filled trades
* `total_shares` – the sum of `quantity` over those trades

Sort by `total_shares` from highest to lowest; if two traders have the same total, the smaller `trader_id` comes first.""",
        [S1.TABLES[2]], TR_SCHEMA, sets,
        "SELECT trader_id, COUNT(*) AS filled_trades, SUM(quantity) AS total_shares\nFROM Trades\n-- TODO: keep only FILLED trades, then GROUP BY / HAVING / ORDER BY\nGROUP BY trader_id;",
        ref, "Columns, in order: trader_id, filled_trades, total_shares. Ordered by total_shares DESC, trader_id ASC.",
        ["Filtering on status must happen before grouping (WHERE).", "HAVING is needed for the 'at least 2' rule.", "Tie-break ordering is tested."],
        "WHERE keeps FILLED rows only; GROUP BY trader_id builds one row per trader; HAVING COUNT(*) >= 2 removes traders with a single filled trade; ORDER BY applies the requested ranking.",
        ["single table", "GROUP BY", "HAVING", "ORDER BY"], "easy")


def build_n2():
    """OA1 / 2 tables: Securities + Trades."""
    def guard(d): return True
    sets = [("Sample data from the statement", S1.SAMPLE), ("Second sample", S1.SAMPLE2), ("No filled trades at all (empty result)", S1.NOVALID | {"Trades": [(1, 1, 1, "2024-03-01", "BUY", 5, 1.0, "PENDING")]}),
            ("A security with trades that are all cancelled is excluded", {"Securities": S1.SECS[:3], "MarketQuotes": [], "Trades": [(1, 1, 1, "2024-03-01", "BUY", 10, 10.25, "FILLED"), (2, 2, 1, "2024-03-01", "BUY", 10, 10.25, "CANCELLED"), (3, 3, 1, "2024-03-01", "SELL", 4, 10.25, "FILLED"), (4, 3, 1, "2024-03-02", "BUY", 4, 11.75, "FILLED")]}),
            ("Randomised", S1.gen(51, n_trades=60)), ("Randomised larger", S1.gen(52, n_sec=10, n_trades=150))]
    ref = """SELECT s.ticker,
       COUNT(*)                              AS filled_trades,
       ROUND(SUM(t.quantity * t.price), 2)   AS total_notional
FROM Securities s
JOIN Trades t ON t.security_id = s.security_id
WHERE t.status = 'FILLED'
GROUP BY s.security_id, s.ticker
ORDER BY total_notional DESC, s.ticker ASC;"""
    return sql_question("n2", "select", 200, "Notional Traded per Ticker",
"""Using `Securities` and `Trades`, report how much value has been traded in each security.

Consider only trades with `status = 'FILLED'`. The **notional** of a trade is `quantity * price`. Return one row for every security that has at least one filled trade:

`ticker, filled_trades, total_notional`

* `filled_trades` – number of filled trades
* `total_notional` – the sum of the notionals, rounded to 2 decimals

Sort by `total_notional` descending, then `ticker` ascending.""",
        S1.TABLES[0:1] + S1.TABLES[2:3], S1.SCHEMA, sets,
        "SELECT s.ticker, COUNT(*) AS filled_trades, 0.0 AS total_notional\nFROM Securities s\nJOIN Trades t ON t.security_id = s.security_id\n-- TODO: filter, aggregate notional, order\nGROUP BY s.ticker;",
        ref, "Columns, in order: ticker, filled_trades, total_notional. Ordered by total_notional DESC, ticker ASC.",
        ["INNER JOIN naturally excludes securities without filled trades.", "Notional uses quantity * price per row before summing."],
        "Join each trade to its security, keep FILLED rows, multiply quantity by price for every row inside SUM, group per security and sort.",
        ["joins", "aggregation"], "easy")


def build_n3():
    """OA2 / 1 table: Transactions."""
    def guard(d):
        by = {}
        for t in d["Transactions"]:
            if t[3] > 0 and "2025-01-01" <= t[2][:10] <= "2025-01-31":
                by.setdefault(t[4], []).append(Fraction(str(t[3])))
        return not any(len(v) >= 2 and _half(sum(v) / len(v), 2) for v in by.values())
    def pick(seed0, **kw):
        for s in range(seed0, seed0 + 500):
            d = {"Transactions": S2.gen(s, **kw)["Transactions"]}
            if guard(d): return d
    sample = {"Transactions": S2.A1["Transactions"]}
    sets = [("Sample data from the statement", sample), ("Second sample", {"Transactions": S2.A2["Transactions"]}), ("No channel has two January purchases (empty result)", {"Transactions": [(1, 1, "2025-01-05 10:00:00", 10.0, "POS", "US"), (2, 1, "2025-02-05 10:00:00", 10.0, "POS", "US"), (3, 1, "2025-01-06 10:00:00", -4.0, "ATM", "US")]}),
            ("Boundary timestamps and refunds", {"Transactions": [(1, 1, "2024-12-31 23:59:59", 10.0, "POS", "US"), (2, 1, "2025-01-01 00:00:00", 20.0, "POS", "US"), (3, 1, "2025-01-31 23:59:59", 30.0, "POS", "US"), (4, 1, "2025-02-01 00:00:00", 90.0, "POS", "US"), (5, 1, "2025-01-15 09:00:00", -50.0, "POS", "US")]}),
            ("Randomised", pick(11, n_txn=60)), ("Randomised larger", pick(33, n_acc=12, n_txn=140))]
    ref = """SELECT channel,
       COUNT(*)              AS purchases,
       ROUND(AVG(amount), 2) AS avg_amount
FROM Transactions
WHERE amount > 0
  AND txn_time >= '2025-01-01 00:00:00'
  AND txn_time <  '2025-02-01 00:00:00'
GROUP BY channel
HAVING COUNT(*) >= 2
ORDER BY avg_amount DESC, channel ASC;"""
    return sql_question("n3", "select", 100, "January Purchases by Channel",
"""The payments team wants an overview of January 2025 spending per channel.

Using the `Transactions` table, consider only **purchases** (`amount > 0`) whose `txn_time` is in January 2025 (from `'2025-01-01 00:00:00'` up to but **not including** `'2025-02-01 00:00:00'`). For each `channel` that has **at least 2** such purchases return:

`channel, purchases, avg_amount`

* `purchases` – number of qualifying purchases
* `avg_amount` – average `amount`, rounded to 2 decimals

Sort by `avg_amount` descending, then `channel` ascending.""",
        [S2.TABLES[1]], TX_SCHEMA, sets,
        "SELECT channel, COUNT(*) AS purchases, ROUND(AVG(amount), 2) AS avg_amount\nFROM Transactions\n-- TODO: WHERE (purchases in January 2025), GROUP BY, HAVING, ORDER BY\nGROUP BY channel;",
        ref, "Columns, in order: channel, purchases, avg_amount. Ordered by avg_amount DESC, channel ASC.",
        ["Half-open date range: 2025-02-01 00:00:00 must be excluded.", "Refunds (negative amounts) are excluded before averaging."],
        "Filter rows first (positive amounts in the half-open January window), group by channel, keep groups with HAVING COUNT(*) >= 2, then order. Using BETWEEN with a date-only upper bound would miss late-January times.",
        ["single table", "date range", "aggregation"], "easy")


# ------------------------------------------------------------------ 4-table questions
def build_n4a():
    """OA3: NewsArticles, SentimentScores, Entities, MarketEvents."""
    from datetime import datetime, timedelta
    def guard(d, boundary=True):
        art = {a[0]: a for a in d["NewsArticles"]}; by = {}
        for s in d["SentimentScores"]:
            if art[s[0]][4] == "en": by.setdefault(s[1], []).append(Fraction(str(s[2])))
        if any(_half(sum(v) / len(v), 3) for v in by.values()): return False
        for m in d["MarketEvents"] if boundary else []:     # random data: no event exactly 24h after an article
            for s in d["SentimentScores"]:
                if s[1] == m[1]:
                    a = art[s[0]]
                    if datetime.strptime(m[2], "%Y-%m-%d %H:%M:%S") - datetime.strptime(a[3], "%Y-%m-%d %H:%M:%S") == timedelta(days=1): return False
        return True
    def pick(seed0, **kw):
        for s in range(seed0, seed0 + 800):
            d = S3.gen(s, **kw)
            if guard(d): return d
    sets = [("Sample data from the statement", S3.S1), ("Second sample", S3.S2), ("Nothing English (empty result)", S3.EDGE_EMPTY), ("Boundary sample", S3.EDGE_CAP),
            ("Randomised", pick(300, n_art=30, n_ev=40)), ("Randomised larger", pick(500, n_art=60, p_pair=0.5, n_ev=120))]
    for _, d in sets[:4]: assert guard(d, False)
    for _, d in sets[4:]: assert guard(d)
    ref = """WITH stats AS (
  SELECT s.entity_id, COUNT(*) AS n_articles, ROUND(AVG(s.score), 3) AS avg_score
  FROM SentimentScores s
  JOIN NewsArticles a ON a.article_id = s.article_id
  WHERE a.language = 'en'
  GROUP BY s.entity_id
),
confirmed AS (
  SELECT m.entity_id, COUNT(*) AS confirmed_events
  FROM MarketEvents m
  WHERE m.event_type = 'PRICE_MOVE'
    AND EXISTS (SELECT 1
                FROM SentimentScores s
                JOIN NewsArticles a ON a.article_id = s.article_id
                WHERE s.entity_id = m.entity_id
                  AND a.language = 'en'
                  AND m.event_time >= a.published_at
                  AND m.event_time <= DATETIME(a.published_at, '+1 day'))
  GROUP BY m.entity_id
)
SELECT e.entity_name, st.n_articles, st.avg_score, COALESCE(c.confirmed_events, 0) AS confirmed_events
FROM Entities e
JOIN stats st            ON st.entity_id = e.entity_id
LEFT JOIN confirmed c    ON c.entity_id = e.entity_id
WHERE e.entity_type = 'COMPANY'
ORDER BY confirmed_events DESC, e.entity_name ASC;"""
    return sql_question("n4a", "select", 120, "News Coverage and Market Reaction per Company",
"""Research wants to see how English-language coverage of each **company** lines up with market activity. Use `NewsArticles`, `SentimentScores`, `Entities` and `MarketEvents`.

For every entity with `entity_type = 'COMPANY'` that has at least one sentiment score on an English article (`language = 'en'`), return:

`entity_name, n_articles, avg_score, confirmed_events`

* `n_articles` – number of sentiment-score rows of that entity on English articles
* `avg_score` – average of those `score` values, rounded to 3 decimals
* `confirmed_events` – the number of **distinct** `MarketEvents` rows of that entity with `event_type = 'PRICE_MOVE'` that happened at or after the publication time of **at least one** of its English articles and no later than 24 hours (inclusive) after that publication time; `0` if none

An event must be counted only once, even if several articles precede it. Sort by `confirmed_events` descending, then `entity_name` ascending.""",
        S3.TABLES, S3.SCHEMA, sets,
        "SELECT e.entity_name, COUNT(*) AS n_articles, 0.0 AS avg_score, 0 AS confirmed_events\nFROM Entities e\nJOIN SentimentScores s ON s.entity_id = e.entity_id\nJOIN NewsArticles a ON a.article_id = s.article_id\n-- TODO: English only, companies only; count events with EXISTS (no double counting)\nGROUP BY e.entity_name;",
        ref, "Columns, in order: entity_name, n_articles, avg_score, confirmed_events. Ordered by confirmed_events DESC, entity_name ASC.",
        ["Joining events directly to articles multiplies rows: AVG/COUNT would be wrong (EXISTS or separate CTEs are needed).", "24-hour window inclusive; PRICE_MOVE events only; companies only."],
        "Aggregate sentiment per entity in one CTE and count confirmed events in another so neither join multiplies the other's rows. The EXISTS subquery checks for at least one preceding English article, which guarantees each event is counted once. LEFT JOIN keeps companies with zero confirmed events.",
        ["4 tables", "CTE", "EXISTS", "date arithmetic"], "medium")


def build_n4b():
    """OA4: Securities, DailyPrices, SectorMap, Benchmarks."""
    from oa4_sql import F, jan, rets
    def first_last(rows):
        v = [Fraction(str(x[2])) for x in sorted(rows, key=lambda r: r[1]) if x[2] is not None and "2024-01-01" <= x[1] <= "2024-01-31"]
        return (v[0], v[-1], len(v)) if len(v) >= 2 else None
    def guard(d):
        sec = dict(d["SectorMap"]); bret = {}
        for sc in set(sec.values()):
            fl = first_last([(None, b[1], b[2]) for b in d["Benchmarks"] if b[0] == sc])
            if fl and fl[0] > 0: bret[sc] = (fl[1] / fl[0] - 1) * 100
        for sid, sc in sec.items():
            fl = first_last([p for p in d["DailyPrices"] if p[0] == sid])
            if fl and sc in bret and fl[0] > 0:
                sr = (fl[1] / fl[0] - 1) * 100
                if any(_half(x, 2) for x in (sr, bret[sc], sr - bret[sc])): return False
        return True
    def pick(seed0, **kw):
        for s in range(seed0, seed0 + 1500):
            d = S4.gen(s, **kw)
            if guard(d): return d
        raise RuntimeError
    sets = [("Sample data from the statement", S4.W1), ("Second sample", S4.W2), ("No benchmark data (empty result)", S4.EMPTY), ("Two securities share a sector; the better one is returned", S4.TIES | {"Benchmarks": [("Tech", "2024-01-02", 100.0), ("Tech", "2024-01-05", 100.5), ("Health", "2024-01-02", 50.0), ("Health", "2024-01-04", 51.0)]}),
            ("Randomised", pick(1000, n_sec=5, wide=True)), ("Randomised larger", pick(2000, n_sec=6, wide=True, p_null=0.25))]
    for _, d in sets: assert guard(d), _
    ref = """WITH sp AS (
  SELECT security_id, close,
         ROW_NUMBER() OVER (PARTITION BY security_id ORDER BY price_date ASC)  AS rn_first,
         ROW_NUMBER() OVER (PARTITION BY security_id ORDER BY price_date DESC) AS rn_last
  FROM DailyPrices
  WHERE close IS NOT NULL AND price_date BETWEEN '2024-01-01' AND '2024-01-31'
),
sret AS (
  SELECT security_id,
         MAX(CASE WHEN rn_last = 1  THEN close END) * 1.0 / MAX(CASE WHEN rn_first = 1 THEN close END) - 1 AS r
  FROM sp GROUP BY security_id HAVING COUNT(*) >= 2
),
bp AS (
  SELECT sector, bench_close,
         ROW_NUMBER() OVER (PARTITION BY sector ORDER BY bench_date ASC)  AS rn_first,
         ROW_NUMBER() OVER (PARTITION BY sector ORDER BY bench_date DESC) AS rn_last
  FROM Benchmarks
  WHERE bench_close IS NOT NULL AND bench_date BETWEEN '2024-01-01' AND '2024-01-31'
),
bret AS (
  SELECT sector,
         MAX(CASE WHEN rn_last = 1  THEN bench_close END) * 1.0 / MAX(CASE WHEN rn_first = 1 THEN bench_close END) - 1 AS r
  FROM bp GROUP BY sector HAVING COUNT(*) >= 2
),
joined AS (
  SELECT m.sector, s.ticker, sr.r * 100 AS stock_pct, br.r * 100 AS bench_pct, (sr.r - br.r) * 100 AS excess
  FROM Securities s
  JOIN SectorMap m ON m.security_id = s.security_id
  JOIN sret sr     ON sr.security_id = s.security_id
  JOIN bret br     ON br.sector = m.sector
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY sector ORDER BY excess DESC, ticker ASC) AS rk FROM joined
)
SELECT sector, ticker,
       ROUND(stock_pct, 2) AS stock_return_pct,
       ROUND(bench_pct, 2) AS bench_return_pct,
       ROUND(excess, 2)    AS excess_pct
FROM ranked
WHERE rk = 1
ORDER BY sector ASC;"""
    return sql_question("n4b", "select", 120, "Best Stock per Sector versus Its Benchmark",
"""For January 2024 (dates from `'2024-01-01'` to `'2024-01-31'` inclusive) find, in every sector, the security that beat its sector benchmark by the most. Use `Securities`, `DailyPrices`, `SectorMap` and `Benchmarks`.

* A security's **January return** is `last_close / first_close - 1`, where `first_close` / `last_close` are its closes on the earliest / latest January date that has a **non-NULL** `close`. The security needs at least 2 such rows.
* A sector benchmark's January return is defined the same way from `bench_close`, also with at least 2 non-NULL rows.
* `excess = stock return - benchmark return`.

For every sector that has a benchmark return, return the single security with the highest `excess` (ties → smaller `ticker`):

`sector, ticker, stock_return_pct, bench_return_pct, excess_pct`

All three percentages are returns × 100, rounded to 2 decimals. Sort by `sector`. Sectors with no qualifying security or benchmark do not appear.""",
        S4.TABLES, S4.SCHEMA, sets,
        "SELECT m.sector, s.ticker, 0.0 AS stock_return_pct, 0.0 AS bench_return_pct, 0.0 AS excess_pct\nFROM Securities s\nJOIN SectorMap m ON m.security_id = s.security_id\n-- TODO: first/last non-NULL January close for stocks and benchmarks (window functions),\n--       compute returns, rank within sector\n;",
        ref, "Columns, in order: sector, ticker, stock_return_pct, bench_return_pct, excess_pct. One row per sector, ordered by sector.",
        ["First/last non-NULL value per series (ROW_NUMBER ascending and descending) is the core difficulty.", "Ranking inside each sector with a deterministic tie-break.", "Benchmark and stock series must each be restricted to January and to non-NULL values."],
        "Number each non-NULL January row in ascending and descending date order so that the first and last values can be picked with conditional MAX. Compute returns for stocks and for sector benchmarks in separate CTEs, join them through SectorMap, then ROW_NUMBER over (sector ORDER BY excess DESC, ticker) and keep rank 1.",
        ["4 tables", "window functions", "CTE", "returns"], "hard")


def build_n4c():
    """OA5: ModelRuns, Predictions, GroundTruthLabels, AlertActions."""
    def guard(d):
        lab = {l[0]: l[1] for l in d["GroundTruthLabels"]}; esc = {a[1] for a in d["AlertActions"] if a[2] == "ESCALATED"}; c = {}
        for p in d["Predictions"]:
            if p[4] is None or p[2] not in lab or p[0] not in esc: continue
            e = c.setdefault(p[1], [0, 0]); e[0] += 1; e[1] += lab[p[2]]
        return not any(_half(Fraction(tp, n), 4) for n, tp in c.values())
    def pick(seed0, **kw):
        for s in range(seed0, seed0 + 800):
            d = S5.gen(s, **kw)
            if guard(d): return d
    M1b = {**S5.M1, "AlertActions": S5.M1["AlertActions"] + [(13, 2, "ESCALATED", "2025-05-01 12:00:00", "ana"), (14, 5, "ESCALATED", "2025-05-02 12:00:00", "raj"), (15, 7, "ESCALATED", "2025-05-02 12:00:00", "mei"), (16, 7, "ESCALATED", "2025-05-02 13:00:00", "mei"), (17, 10, "ESCALATED", "2025-05-03 12:00:00", "ana")]}
    M2b = {**S5.M2, "AlertActions": S5.M2["AlertActions"] + [(5, 1, "ESCALATED", "2025-05-01 12:00:00", "ana"), (6, 3, "ESCALATED", "2025-05-01 12:00:00", "ana"), (7, 2, "ESCALATED", "2025-05-01 12:00:00", "raj")]}
    sets = [("Sample data from the statement", M1b), ("Second sample", M2b), ("Nothing escalated (empty result)", S5.EMPTYQ), ("Duplicate escalations count once; unlabelled predictions ignored", S5.ONLYNEG | {"AlertActions": [(1, 3, "ESCALATED", "2025-05-01 10:00:00", "a"), (2, 3, "ESCALATED", "2025-05-01 11:00:00", "b"), (3, 4, "ESCALATED", "2025-05-01 12:00:00", "a"), (4, 1, "ESCALATED", "2025-05-01 12:00:00", "a")], "GroundTruthLabels": [(1, 0, "2025-06-01"), (2, 1, "2025-06-01")]}),
            ("Randomised", pick(100, n_runs=4, n_ent=40)), ("Randomised larger", pick(300, n_runs=4, n_ent=80, p_act=0.8))]
    for _, d in sets: assert guard(d), _
    ref = """WITH lab AS (
  SELECT p.prediction_id, p.run_id, g.label
  FROM Predictions p
  JOIN GroundTruthLabels g ON g.entity_id = p.entity_id
  WHERE p.score IS NOT NULL
),
esc AS (
  SELECT DISTINCT prediction_id FROM AlertActions WHERE action = 'ESCALATED'
)
SELECT r.run_id, r.model_name,
       COUNT(esc.prediction_id)                                                       AS escalated,
       SUM(CASE WHEN esc.prediction_id IS NOT NULL AND lab.label = 1 THEN 1 ELSE 0 END) AS escalated_tp,
       ROUND(1.0 * SUM(CASE WHEN esc.prediction_id IS NOT NULL AND lab.label = 1 THEN 1 ELSE 0 END)
             / COUNT(esc.prediction_id), 4)                                           AS escalation_precision,
       SUM(CASE WHEN esc.prediction_id IS NULL AND lab.label = 1 THEN 1 ELSE 0 END)   AS missed_positives
FROM ModelRuns r
JOIN lab            ON lab.run_id = r.run_id
LEFT JOIN esc       ON esc.prediction_id = lab.prediction_id
GROUP BY r.run_id, r.model_name
HAVING COUNT(esc.prediction_id) > 0
ORDER BY r.run_id;"""
    return sql_question("n4c", "select", 120, "Escalation Quality per Model Run",
"""Analysts escalate some alerts. Measure how good the escalations are, per model run, using `ModelRuns`, `Predictions`, `GroundTruthLabels` and `AlertActions`.

Consider only predictions whose `score` is **not NULL** and whose `entity_id` has a row in `GroundTruthLabels`. A prediction is *escalated* when it has **at least one** `AlertActions` row with `action = 'ESCALATED'` (several escalation rows still count once).

For every run that has at least one escalated prediction return:

`run_id, model_name, escalated, escalated_tp, escalation_precision, missed_positives`

* `escalated` – number of escalated predictions
* `escalated_tp` – escalated predictions whose `label = 1`
* `escalation_precision` – `escalated_tp / escalated`, rounded to 4 decimals
* `missed_positives` – predictions with `label = 1` that were **not** escalated

Sort by `run_id`.""",
        S5.TABLES, S5.SCHEMA, sets,
        "SELECT r.run_id, r.model_name, 0 AS escalated, 0 AS escalated_tp, 0.0 AS escalation_precision, 0 AS missed_positives\nFROM ModelRuns r\n-- TODO: join predictions, labels and DISTINCT escalated predictions; conditional aggregation\n;",
        ref, "Columns, in order: run_id, model_name, escalated, escalated_tp, escalation_precision, missed_positives. Ordered by run_id.",
        ["Joining AlertActions directly multiplies rows when a prediction has several escalation rows (needs DISTINCT / EXISTS).", "Runs without escalations are removed with HAVING.", "Unlabelled and NULL-score predictions are excluded before counting."],
        "Pre-select the labelled, scored predictions and a DISTINCT set of escalated prediction ids so that duplicates cannot inflate counts. A LEFT JOIN to the escalation set lets one pass compute both escalated and non-escalated (missed) counts with conditional SUMs; HAVING removes runs with no escalation.",
        ["4 tables", "CTE", "conditional aggregation", "DISTINCT"], "hard")
