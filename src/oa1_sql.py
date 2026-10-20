import random
from fractions import Fraction
from builder import sql_question

SCHEMA = """CREATE TABLE Securities (
  security_id INTEGER PRIMARY KEY,
  ticker      TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  sector      TEXT NOT NULL,
  exchange    TEXT NOT NULL
);
CREATE TABLE MarketQuotes (
  quote_id    INTEGER PRIMARY KEY,
  security_id INTEGER NOT NULL REFERENCES Securities(security_id),
  quote_date  TEXT NOT NULL,          -- 'YYYY-MM-DD'
  bid         REAL,                   -- may be NULL (missing)
  ask         REAL,                   -- may be NULL (missing)
  volume      INTEGER NOT NULL,
  UNIQUE (security_id, quote_date)
);
CREATE TABLE Trades (
  trade_id    INTEGER PRIMARY KEY,
  security_id INTEGER NOT NULL REFERENCES Securities(security_id),
  trader_id   INTEGER NOT NULL,
  trade_date  TEXT NOT NULL,          -- 'YYYY-MM-DD'
  side        TEXT NOT NULL CHECK (side IN ('BUY','SELL')),
  quantity    INTEGER NOT NULL CHECK (quantity > 0),
  price       REAL NOT NULL,
  status      TEXT NOT NULL CHECK (status IN ('FILLED','PENDING','REJECTED','CANCELLED'))
);"""

TABLES = [
 {"name": "Securities", "description": "One row per listed security.", "columns": [
   {"name": "security_id", "type": "INTEGER", "description": "Primary key"},
   {"name": "ticker", "type": "TEXT", "description": "Unique ticker symbol"},
   {"name": "name", "type": "TEXT", "description": "Company name"},
   {"name": "sector", "type": "TEXT", "description": "Sector label"},
   {"name": "exchange", "type": "TEXT", "description": "Listing exchange, e.g. 'NASDAQ' or 'NYSE'"}]},
 {"name": "MarketQuotes", "description": "At most one end-of-day quote per security per date.", "columns": [
   {"name": "quote_id", "type": "INTEGER", "description": "Primary key"},
   {"name": "security_id", "type": "INTEGER", "description": "FK to Securities"},
   {"name": "quote_date", "type": "TEXT", "description": "'YYYY-MM-DD'"},
   {"name": "bid", "type": "REAL", "description": "Best bid; NULL when missing"},
   {"name": "ask", "type": "REAL", "description": "Best ask; NULL when missing"},
   {"name": "volume", "type": "INTEGER", "description": "Shares traded that day"}]},
 {"name": "Trades", "description": "Orders executed (or pending) by traders.", "columns": [
   {"name": "trade_id", "type": "INTEGER", "description": "Primary key"},
   {"name": "security_id", "type": "INTEGER", "description": "FK to Securities"},
   {"name": "trader_id", "type": "INTEGER", "description": "Trader identifier"},
   {"name": "trade_date", "type": "TEXT", "description": "'YYYY-MM-DD'"},
   {"name": "side", "type": "TEXT", "description": "'BUY' or 'SELL'"},
   {"name": "quantity", "type": "INTEGER", "description": "Positive share count"},
   {"name": "price", "type": "REAL", "description": "Execution/limit price"},
   {"name": "status", "type": "TEXT", "description": "'FILLED','PENDING','REJECTED' or 'CANCELLED'"}]},
]

C = lambda c: None if c is None else round(c / 100, 2)   # cents -> dollars

SECS = [(1, "AAPL", "Apple Inc.", "Technology", "NASDAQ"), (2, "MSFT", "Microsoft Corp.", "Technology", "NASDAQ"),
        (3, "JPM", "JPMorgan Chase", "Financials", "NYSE"), (4, "NVDA", "NVIDIA Corp.", "Technology", "NASDAQ"),
        (5, "AMGN", "Amgen Inc.", "Healthcare", "NASDAQ"), (6, "XOM", "Exxon Mobil", "Energy", "NYSE"),
        (7, "GILD", "Gilead Sciences", "Healthcare", "NASDAQ"), (8, "BAC", "Bank of America", "Financials", "NYSE"),
        (9, "COST", "Costco Wholesale", "Consumer", "NASDAQ"), (10, "SBUX", "Starbucks", "Consumer", "NASDAQ")]


def Q(qid, sec, d, bid_c, spread_c, vol, nb=False, na=False):
    bid = None if nb else C(bid_c)
    ask = None if na else C(bid_c + spread_c)
    return (qid, sec, d, bid, ask, vol)


def gen(seed, n_sec=8, n_days=8, p_quote=0.8, p_null=0.12, n_trades=30, ties=False):
    rng = random.Random(seed)
    secs = SECS[:n_sec]
    quotes, qid = [], 1
    base = {s[0]: rng.randrange(2000, 40000) for s in secs}
    for s in secs:
        for d in range(1, n_days + 1):
            if rng.random() < p_quote:
                b = base[s[0]] + rng.randrange(-300, 300)
                if ties and s[0] in (1, 2):
                    b = 10000 + 100 * d
                sp = 2 * rng.randrange(1, 30) if not (ties and s[0] in (1, 2)) else 20
                quotes.append(Q(qid, s[0], f"2024-03-{d:02d}", b, sp, rng.randrange(100, 5000),
                                rng.random() < p_null, rng.random() < p_null)); qid += 1
    trades = []
    for t in range(1, n_trades + 1):
        s = rng.choice(secs)[0]; d = rng.randrange(1, n_days + 1)
        qs = [q for q in quotes if q[1] == s and q[2] == f"2024-03-{d:02d}" and q[3] is not None and q[4] is not None]
        if qs and rng.random() < 0.85:
            mid = (qs[0][3] + qs[0][4]) / 2
            p = round(mid * (1 + rng.choice([-0.09, -0.04, -0.02, 0, 0.01, 0.03, 0.045, 0.07]) + rng.randrange(-30, 30) / 10000), 2)
        else:
            p = round(base[s] / 100 * rng.uniform(0.9, 1.1), 2)
        trades.append((t, s, rng.randrange(100, 110), f"2024-03-{d:02d}", rng.choice(["BUY", "SELL"]),
                       rng.choice([10, 50, 100, 200, 500]), p,
                       rng.choices(["FILLED", "PENDING", "REJECTED", "CANCELLED"], [5, 4, 1, 1])[0]))
    return {"Securities": secs, "MarketQuotes": quotes, "Trades": trades}


# ---- tie guards (exact rational arithmetic) -------------------------------------
def _half(fr, digits):
    x = fr * 10 ** digits
    return (x - (x.numerator // x.denominator)) == Fraction(1, 2)


def valid_q(data):
    return [q for q in data["MarketQuotes"] if q[3] is not None and q[4] is not None]


def guard_q1(data):
    byS = {}
    sec = {s[0]: s for s in data["Securities"]}
    for q in valid_q(data):
        byS.setdefault(q[1], []).append((Fraction(str(q[3])) + Fraction(str(q[4]))) / 2)
    return not any(_half(sum(v) / len(v), 2) for v in byS.values())


def _mid(data, t):
    for q in valid_q(data):
        if q[1] == t[1] and q[2] == t[3]:
            return (Fraction(str(q[3])) + Fraction(str(q[4]))) / 2
    return None


def guard_q2(data):
    agg = {}
    for t in data["Trades"]:
        if t[7] != "FILLED": continue
        m = _mid(data, t)
        if m is None: continue
        p = Fraction(str(t[6]))
        agg.setdefault(t[1], []).append(p - m if t[4] == "BUY" else m - p)
    return not any(_half(sum(v) / len(v), 4) for v in agg.values())


def guard_q3(data):
    for t in data["Trades"]:
        m = _mid(data, t)
        if m is None: continue
        if abs(Fraction(str(t[6])) - m) == Fraction(5, 100) * m: return False
    return True


def pick(guard, seed0, **kw):
    for s in range(seed0, seed0 + 500):
        d = gen(s, **kw)
        if guard(d): return d
    raise RuntimeError("no safe seed")


SAMPLE = {
 "Securities": SECS[:5],
 "MarketQuotes": [
  Q(1, 1, "2024-03-01", 18000, 20, 1000), Q(2, 1, "2024-03-04", 18100, 40, 1500), Q(3, 1, "2024-03-05", 0, 20, 800, nb=True),
  Q(4, 2, "2024-03-01", 41000, 40, 700), Q(5, 2, "2024-03-04", 41100, 40, 900), Q(6, 2, "2024-03-05", 41300, 60, 1200),
  Q(7, 3, "2024-03-01", 19500, 20, 3000), Q(8, 3, "2024-03-04", 19600, 20, 2500),
  Q(9, 4, "2024-03-04", 87000, 100, 5000),
  Q(10, 4, "2024-03-05", 88000, 100, 4800, na=True),
  Q(11, 5, "2024-03-01", 31000, 20, 400), Q(12, 5, "2024-03-04", 31200, 40, 650)],
 "Trades": [
  (1, 1, 101, "2024-03-01", "BUY", 100, 180.15, "FILLED"), (2, 1, 101, "2024-03-04", "SELL", 50, 181.10, "FILLED"),
  (3, 2, 102, "2024-03-01", "BUY", 200, 410.30, "FILLED"), (4, 2, 102, "2024-03-04", "SELL", 100, 411.10, "FILLED"),
  (5, 2, 103, "2024-03-05", "BUY", 100, 413.80, "PENDING"), (6, 3, 101, "2024-03-01", "BUY", 300, 195.10, "FILLED"),
  (7, 4, 104, "2024-03-04", "BUY", 10, 870.50, "FILLED"), (8, 4, 104, "2024-03-05", "BUY", 10, 880.00, "PENDING"),
  (9, 5, 105, "2024-03-01", "SELL", 70, 310.50, "PENDING"), (10, 5, 105, "2024-03-04", "BUY", 90, 340.00, "PENDING"),
  (11, 5, 105, "2024-03-06", "BUY", 10, 312.00, "PENDING"), (12, 1, 106, "2024-03-01", "SELL", 20, 180.00, "CANCELLED")],
}
SAMPLE2 = {
 "Securities": SECS[:6],
 "MarketQuotes": [
  Q(1, 1, "2024-03-11", 17500, 20, 900), Q(2, 1, "2024-03-12", 17600, 20, 1100),
  Q(3, 2, "2024-03-11", 40500, 100, 300), Q(4, 2, "2024-03-12", 40800, 60, 2000), Q(5, 2, "2024-03-13", 41000, 60, 1000),
  Q(6, 4, "2024-03-11", 86000, 200, 100), Q(7, 4, "2024-03-12", 85800, 100, 7000),
  Q(8, 5, "2024-03-11", 30000, 40, 50),
  Q(9, 6, "2024-03-11", 11000, 20, 4000), Q(10, 6, "2024-03-12", 11200, 20, 4100)],
 "Trades": [
  (1, 1, 201, "2024-03-11", "BUY", 100, 175.20, "FILLED"), (2, 1, 201, "2024-03-12", "BUY", 100, 176.30, "FILLED"),
  (3, 1, 202, "2024-03-12", "SELL", 50, 176.00, "FILLED"), (4, 2, 203, "2024-03-12", "SELL", 25, 408.00, "FILLED"),
  (5, 2, 203, "2024-03-13", "BUY", 25, 410.10, "PENDING"), (6, 4, 204, "2024-03-11", "BUY", 5, 861.00, "FILLED"),
  (7, 4, 204, "2024-03-12", "SELL", 5, 858.00, "FILLED"), (8, 5, 205, "2024-03-11", "BUY", 40, 300.20, "FILLED"),
  (9, 6, 206, "2024-03-11", "BUY", 60, 110.10, "PENDING"), (10, 6, 206, "2024-03-12", "BUY", 60, 150.00, "PENDING")],
}
EMPTY_TRADES = {"Securities": SECS[:3], "MarketQuotes": [Q(1, 1, "2024-03-01", 100, 2, 10, nb=True), Q(2, 3, "2024-03-01", 200, 4, 10)], "Trades": []}
NOVALID = {"Securities": SECS[:4],
           "MarketQuotes": [Q(1, 1, "2024-03-01", 100, 2, 10, nb=True), Q(2, 1, "2024-03-02", 100, 2, 10, na=True), Q(3, 2, "2024-03-01", 500, 4, 90)],
           "Trades": [(1, 1, 1, "2024-03-01", "BUY", 1, 1.0, "PENDING"), (2, 2, 1, "2024-03-01", "SELL", 5, 5.04, "PENDING"),
                      (3, 2, 1, "2024-03-02", "SELL", 5, 5.04, "PENDING"),
                      (4, 1, 1, "2024-03-01", "BUY", 1, 1.0, "FILLED"), (5, 2, 1, "2024-03-01", "BUY", 5, 5.02, "FILLED"),
                      (6, 2, 1, "2024-03-03", "BUY", 5, 5.02, "FILLED")]}
TIE2 = {"Securities": [SECS[0], SECS[1], SECS[3], SECS[2]],
        "MarketQuotes": [Q(1, 1, "2024-03-01", 9990, 20, 10), Q(2, 2, "2024-03-01", 19990, 20, 10), Q(3, 4, "2024-03-01", 29990, 20, 10),
                         Q(4, 3, "2024-03-01", 15000, 20, 10)],
        "Trades": [(1, 1, 1, "2024-03-01", "BUY", 10, 100.10, "FILLED"), (2, 2, 1, "2024-03-01", "BUY", 10, 200.10, "FILLED"),
                   (3, 4, 1, "2024-03-01", "SELL", 10, 299.80, "FILLED"), (4, 3, 1, "2024-03-01", "SELL", 10, 150.50, "FILLED")]}


def build():
    qs = []
    # --- Q1 ---------------------------------------------------------------
    tie = next(d for d in (gen(sd, ties=True, n_days=6, p_null=0.0, p_quote=1.0) for sd in range(5, 200)) if guard_q1(d))
    q1_sets = [("Sample data from the statement", SAMPLE), ("Second sample with a single-quote security and a spread-heavy day", SAMPLE2),
               ("No valid quotes for NASDAQ securities (empty result expected)", EMPTY_TRADES),
               ("Ties in avg_mid between two securities (tie-break on ticker)", tie),
               ("Randomised 8 securities, many NULL bid/ask values", pick(guard_q1, 100, p_null=0.3)),
               ("Randomised 10 securities, 10 days", pick(guard_q1, 300, n_sec=10, n_days=10, p_quote=0.9))]
    for _, d in q1_sets: assert guard_q1(d)
    ref1 = """SELECT s.ticker,
       COUNT(*)                          AS valid_quotes,
       ROUND(AVG((q.bid + q.ask) / 2.0), 2) AS avg_mid,
       MAX(q.volume)                     AS max_volume
FROM Securities s
JOIN MarketQuotes q ON q.security_id = s.security_id
WHERE s.exchange = 'NASDAQ'
  AND q.bid IS NOT NULL AND q.ask IS NOT NULL
GROUP BY s.security_id, s.ticker
HAVING COUNT(*) >= 2
ORDER BY avg_mid DESC, s.ticker ASC;"""
    qs.append(sql_question("oa01-sql-01", "select", 200, "Average Mid-Price per NASDAQ Security",
"""A data engineer needs a quality-checked summary of end-of-day quotes for NASDAQ-listed securities.

Write one `SELECT` that joins `Securities` and `MarketQuotes` and returns, for each security with `exchange = 'NASDAQ'`:

* `ticker`
* `valid_quotes` – number of quotes in which **both** `bid` and `ask` are non-NULL
* `avg_mid` – the average of the mid-price `(bid + ask) / 2` over those valid quotes, rounded to 2 decimals
* `max_volume` – the largest `volume` among those valid quotes

Rules: ignore quotes with a missing bid or ask entirely (they must not count towards any column); return only securities with **at least 2** valid quotes. Sort by `avg_mid` descending, then `ticker` ascending.""",
        TABLES[:2], SCHEMA, [(d, x) for d, x in q1_sets],
"SELECT s.ticker, COUNT(*) AS valid_quotes, 0.0 AS avg_mid, 0 AS max_volume\nFROM Securities s\nJOIN MarketQuotes q ON q.security_id = s.security_id\n-- TODO: filters, GROUP BY, HAVING, ORDER BY\n;",
        ref1, "Columns, in order: ticker, valid_quotes, avg_mid, max_volume. Ordered by avg_mid DESC, ticker ASC.",
        ["Correct join and NASDAQ filter: required to pass any non-empty test.", "NULL bid/ask handling: tests with many NULLs fail if invalid quotes are counted.", "HAVING vs WHERE and tie-break ordering are exercised by hidden tests."],
        "Join the tables, drop quotes with a NULL bid or ask in WHERE (so they affect no aggregate), group by security, keep groups with HAVING COUNT(*) >= 2, and order by the rounded average then ticker. Using COUNT(q.quote_id) without the NULL filter over-counts; filtering with HAVING instead of WHERE would leave NULL quotes inside the aggregates.",
        ["joins", "aggregation", "NULL handling", "HAVING"], "medium"))
    # --- Q2 ---------------------------------------------------------------
    q2_sets = [("Sample data from the statement", SAMPLE), ("Second sample", SAMPLE2), ("No trades at all (empty result)", EMPTY_TRADES),
               ("Trades without same-day quote or with NULL bid/ask are excluded", NOVALID),
               ("Two securities in one sector with equal slippage (RANK ties) plus a single-security sector", TIE2),
               ("Randomised: mixed sectors, many trades", pick(guard_q2, 700, n_sec=9, n_days=6, n_trades=60)),
               ("Randomised larger", pick(guard_q2, 900, n_sec=10, n_days=10, n_trades=120, p_null=0.2))]
    for _, d in q2_sets: assert guard_q2(d)
    ref2 = """WITH matched AS (
  SELECT s.sector, s.ticker,
         CASE t.side WHEN 'BUY'  THEN t.price - (q.bid + q.ask) / 2.0
                     ELSE (q.bid + q.ask) / 2.0 - t.price END AS slip
  FROM Trades t
  JOIN Securities   s ON s.security_id = t.security_id
  JOIN MarketQuotes q ON q.security_id = t.security_id AND q.quote_date = t.trade_date
  WHERE t.status = 'FILLED' AND q.bid IS NOT NULL AND q.ask IS NOT NULL
),
agg AS (
  SELECT sector, ticker, COUNT(*) AS matched_trades, ROUND(AVG(slip), 4) AS avg_slippage
  FROM matched GROUP BY sector, ticker
)
SELECT sector, ticker, matched_trades, avg_slippage,
       RANK() OVER (PARTITION BY sector ORDER BY avg_slippage ASC) AS sector_rank
FROM agg
ORDER BY sector, sector_rank, ticker;"""
    qs.append(sql_question("oa01-sql-02", "select", 150, "Execution Slippage versus Same-Day Mid",
"""The best-execution team compares each **filled** trade with the mid-price quoted for the same security on the same date.

For a trade matched to a quote with non-NULL `bid` and `ask`, define `mid = (bid + ask) / 2` and the **slippage** (positive = worse for the trader):

* `BUY`: `price - mid`
* `SELL`: `mid - price`

Using `Trades`, `Securities` and `MarketQuotes` (match quotes on `security_id` and `quote_date = trade_date`), return one row per security that has at least one matched filled trade:

`sector, ticker, matched_trades, avg_slippage, sector_rank`

* `matched_trades` – count of matched filled trades
* `avg_slippage` – average slippage rounded to 4 decimals
* `sector_rank` – `RANK()` of the security **within its sector**, ordered by the reported `avg_slippage` **ascending** (lowest slippage = rank 1; ties share a rank)

Only trades with `status = 'FILLED'` count. Sort by `sector`, `sector_rank`, `ticker`.""",
        TABLES, SCHEMA, q2_sets,
"WITH matched AS (\n  SELECT s.sector, s.ticker, 0.0 AS slip\n  FROM Trades t\n  JOIN Securities s ON s.security_id = t.security_id\n  -- TODO: join MarketQuotes, compute slippage per side\n)\nSELECT sector, ticker, COUNT(*) AS matched_trades, 0.0 AS avg_slippage, 1 AS sector_rank\nFROM matched\nGROUP BY sector, ticker;",
        ref2, "Columns, in order: sector, ticker, matched_trades, avg_slippage, sector_rank. Order: sector, sector_rank, ticker.",
        ["Correct three-table join keys (security_id AND date).", "Side-dependent sign of slippage.", "RANK() (not ROW_NUMBER/DENSE_RANK) with partition by sector; ties tested in hidden data."],
        "Three-way join on security and date; CASE flips the sign for SELL. Aggregate per security first (CTE), then apply RANK() OVER (PARTITION BY sector ORDER BY avg_slippage). Ranking after rounding means equal reported slippages share a rank.",
        ["joins", "CTE", "window functions", "aggregation"], "medium"))
    # --- Q3 ---------------------------------------------------------------
    q3_sets = [("Sample data from the statement", SAMPLE), ("Second sample", SAMPLE2), ("No pending trades have a valid quote (all rejected)", NOVALID),
               ("Empty Trades table (no change)", EMPTY_TRADES),
               ("Randomised: mixed statuses and NULL quotes", pick(guard_q3, 1100, n_trades=70, p_null=0.25)),
               ("Randomised larger", pick(guard_q3, 1300, n_sec=10, n_days=10, n_trades=150))]
    for _, d in q3_sets: assert guard_q3(d)
    ref3 = """UPDATE Trades
SET status = 'REJECTED'
WHERE status = 'PENDING'
  AND NOT EXISTS (
        SELECT 1
        FROM MarketQuotes q
        WHERE q.security_id = Trades.security_id
          AND q.quote_date  = Trades.trade_date
          AND q.bid IS NOT NULL AND q.ask IS NOT NULL
          AND ABS(Trades.price - (q.bid + q.ask) / 2.0) <= 0.05 * ((q.bid + q.ask) / 2.0)
  );"""
    qs.append(sql_question("oa01-sql-03", "update", 100, "Reject Stale or Off-Market Pending Trades",
"""A nightly clean-up job must reject pending trades that cannot be validated against the market.

Write SQL (one or more statements) that sets `status = 'REJECTED'` for every `Trades` row where `status = 'PENDING'` **and there is no valid supporting quote**. A quote supports a trade when all of the following hold:

* it belongs to the same `security_id` and `quote_date = trade_date`;
* both `bid` and `ask` are non-NULL;
* the trade `price` is within **5% of the quote mid-price** `(bid + ask) / 2`, i.e. `ABS(price - mid) <= 0.05 * mid`.

Do not change trades whose status is not `'PENDING'`, pending trades that do have a supporting quote, or any other table or column. (The grader compares the full `Trades` and `MarketQuotes` tables afterwards.)""",
        TABLES, SCHEMA, q3_sets,
"UPDATE Trades\nSET status = 'REJECTED'\nWHERE status = 'PENDING'\n  -- TODO: only when no supporting quote exists\n  AND 1 = 0;",
        ref3, "No result set is read. The final contents of Trades (all columns) and MarketQuotes must equal the expected post-update state.",
        ["Sub-tests with NULL bid/ask quotes punish NOT IN / NULL-unsafe logic.", "Over-updating non-PENDING rows loses all credit on tests that contain them.", "Schema must not be altered."],
        "A correlated NOT EXISTS subquery looks for a supporting quote; if none exists the pending trade is rejected. EXISTS is NULL-safe, whereas `price NOT BETWEEN ...` computed over a LEFT JOIN or `NOT IN` over NULLs would misclassify missing quotes.",
        ["UPDATE", "NOT EXISTS", "correlated subquery", "NULL handling"], "medium",
        check_queries=[{"id": "trades", "sql": "SELECT * FROM Trades ORDER BY trade_id"},
                       {"id": "quotes", "sql": "SELECT * FROM MarketQuotes ORDER BY quote_id"}]))
    return qs
