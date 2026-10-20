import random
from fractions import Fraction
from builder import sql_question
from oa1_sql import _half

SCHEMA = """CREATE TABLE Accounts (
  account_id    INTEGER PRIMARY KEY,
  customer_name TEXT NOT NULL,
  country       TEXT NOT NULL,
  open_date     TEXT NOT NULL,
  status        TEXT NOT NULL CHECK (status IN ('ACTIVE','CLOSED','FROZEN'))
);
CREATE TABLE Transactions (
  txn_id           INTEGER PRIMARY KEY,
  account_id       INTEGER NOT NULL REFERENCES Accounts(account_id),
  txn_time         TEXT NOT NULL,        -- 'YYYY-MM-DD HH:MM:SS'
  amount           REAL NOT NULL,        -- negative = refund
  channel          TEXT NOT NULL,
  merchant_country TEXT NOT NULL
);
CREATE TABLE AccountProfiles (
  account_id         INTEGER PRIMARY KEY REFERENCES Accounts(account_id),
  risk_tier          TEXT NOT NULL CHECK (risk_tier IN ('LOW','MEDIUM','HIGH')),
  avg_monthly_spend  REAL,               -- NULL when unknown
  home_country       TEXT NOT NULL
);
CREATE TABLE RiskAlerts (
  alert_id   INTEGER PRIMARY KEY,
  txn_id     INTEGER NOT NULL REFERENCES Transactions(txn_id),
  alert_type TEXT NOT NULL,
  severity   TEXT NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
  created_at TEXT NOT NULL,
  resolved   INTEGER NOT NULL CHECK (resolved IN (0,1))
);"""

TABLES = [
 {"name": "Accounts", "description": "Customer accounts.", "columns": [
   {"name": "account_id", "type": "INTEGER", "description": "Primary key"}, {"name": "customer_name", "type": "TEXT", "description": "Customer name"},
   {"name": "country", "type": "TEXT", "description": "Country of registration"}, {"name": "open_date", "type": "TEXT", "description": "'YYYY-MM-DD'"},
   {"name": "status", "type": "TEXT", "description": "'ACTIVE','CLOSED' or 'FROZEN'"}]},
 {"name": "Transactions", "description": "Card/bank transactions; negative amounts are refunds.", "columns": [
   {"name": "txn_id", "type": "INTEGER", "description": "Primary key"}, {"name": "account_id", "type": "INTEGER", "description": "FK to Accounts"},
   {"name": "txn_time", "type": "TEXT", "description": "'YYYY-MM-DD HH:MM:SS' (24h)"}, {"name": "amount", "type": "REAL", "description": "Amount; negative for refunds"},
   {"name": "channel", "type": "TEXT", "description": "'POS','ONLINE','ATM'"}, {"name": "merchant_country", "type": "TEXT", "description": "Country code of merchant"}]},
 {"name": "AccountProfiles", "description": "At most one profile per account (some accounts have none).", "columns": [
   {"name": "account_id", "type": "INTEGER", "description": "PK and FK to Accounts"}, {"name": "risk_tier", "type": "TEXT", "description": "'LOW','MEDIUM','HIGH'"},
   {"name": "avg_monthly_spend", "type": "REAL", "description": "Typical monthly spend; NULL if unknown"}, {"name": "home_country", "type": "TEXT", "description": "Customer home country"}]},
 {"name": "RiskAlerts", "description": "Zero or more alerts per transaction.", "columns": [
   {"name": "alert_id", "type": "INTEGER", "description": "Primary key"}, {"name": "txn_id", "type": "INTEGER", "description": "FK to Transactions"},
   {"name": "alert_type", "type": "TEXT", "description": "e.g. 'VELOCITY','GEO','AMOUNT'"}, {"name": "severity", "type": "TEXT", "description": "'LOW','MEDIUM','HIGH','CRITICAL'"},
   {"name": "created_at", "type": "TEXT", "description": "'YYYY-MM-DD HH:MM:SS'"}, {"name": "resolved", "type": "INTEGER", "description": "0 = open, 1 = resolved"}]},
]
NAMES = ["Asha Rao", "Ben Ortiz", "Chen Wei", "Dara Cole", "Eli Haas", "Farah Nasir", "Gus Lund", "Hana Ito", "Ivo Petrov", "Jada Moore", "Kofi Mensah", "Lena Voss"]
CTRY = ["US", "GB", "DE", "IN", "JP"]


def gen(seed, n_acc=8, n_txn=40, boundary=True, p_noprof=0.2, p_nullavg=0.2, p_alert=0.35, avg_rng=(200, 3000)):
    r = random.Random(seed)
    acc = [(i, NAMES[i - 1], r.choice(CTRY), f"20{r.randrange(15, 24)}-0{r.randrange(1, 9)}-1{r.randrange(0, 9)}",
            r.choices(["ACTIVE", "CLOSED", "FROZEN"], [6, 1, 1])[0]) for i in range(1, n_acc + 1)]
    prof = []
    for a in acc:
        if r.random() > p_noprof:
            prof.append((a[0], r.choice(["LOW", "MEDIUM", "HIGH"]), None if r.random() < p_nullavg else round(r.uniform(*avg_rng), 2), a[2]))
    txn = []
    for t in range(1, n_txn + 1):
        a = r.choice(acc)
        day = r.randrange(1, 32)
        times = [f"2025-01-{day:02d} {r.randrange(0, 24):02d}:{r.randrange(0, 60):02d}:{r.randrange(0, 60):02d}"]
        if boundary and r.random() < 0.08: times = [r.choice(["2024-12-31 23:59:59", "2025-02-01 00:00:00", "2025-01-01 00:00:00", "2025-01-31 23:59:59"])]
        amt = round(r.choice([r.uniform(5, 400), r.uniform(5, 400), r.uniform(400, 9000), -r.uniform(5, 120)]), 2)
        txn.append((t, a[0], times[0], amt, r.choice(["POS", "ONLINE", "ATM"]), r.choice(CTRY)))
    alerts, aid = [], 1
    for t in txn:
        k = 0
        while r.random() < p_alert and k < 3:
            alerts.append((aid, t[0], r.choice(["VELOCITY", "GEO", "AMOUNT"]), r.choice(["LOW", "MEDIUM", "HIGH", "HIGH", "CRITICAL"]),
                           t[2], r.choice([0, 0, 1]))); aid += 1; k += 1
    return {"Accounts": acc, "Transactions": txn, "AccountProfiles": prof, "RiskAlerts": alerts}


def guard_q2(d):
    prof = {p[0]: p[1] for p in d["AccountProfiles"]}
    fl = {a[1] for a in d["RiskAlerts"]}
    by = {}
    for t in d["Transactions"]:
        if t[3] > 0 and t[1] in prof:
            n, f = by.get(prof[t[1]], (0, 0)); by[prof[t[1]]] = (n + 1, f + (t[0] in fl))
    return not any(_half(Fraction(f, n), 4) for n, f in by.values())


def guard_q3(d):
    prof = {p[0]: p[2] for p in d["AccountProfiles"]}
    tx = {t[0]: t for t in d["Transactions"]}
    for a in d["RiskAlerts"]:
        t = tx[a[1]]; av = prof.get(t[1])
        if av is not None and Fraction(str(t[3])) == 3 * Fraction(str(av)): return False
    return True


def pick(guard, seed0, **kw):
    for s in range(seed0, seed0 + 500):
        d = gen(s, **kw)
        if guard(d): return d
    raise RuntimeError


A1 = {"Accounts": [(1, "Asha Rao", "US", "2019-03-14", "ACTIVE"), (2, "Ben Ortiz", "GB", "2020-07-01", "ACTIVE"), (3, "Chen Wei", "DE", "2018-11-30", "CLOSED"),
                   (4, "Dara Cole", "IN", "2021-02-02", "ACTIVE"), (5, "Eli Haas", "JP", "2022-05-19", "FROZEN")],
      "Transactions": [
        (1, 1, "2025-01-03 10:15:00", 120.50, "POS", "US"), (2, 1, "2025-01-15 22:40:10", 980.00, "ONLINE", "GB"), (3, 1, "2025-01-31 23:59:59", 45.25, "POS", "US"),
        (4, 1, "2025-01-20 09:00:00", -30.00, "POS", "US"), (5, 1, "2025-02-01 00:00:00", 600.00, "ONLINE", "US"),
        (6, 2, "2025-01-05 08:00:00", 310.00, "ATM", "GB"), (7, 2, "2025-01-06 08:30:00", 15.75, "POS", "GB"), (8, 2, "2025-01-07 09:10:00", 22.10, "POS", "GB"),
        (9, 3, "2025-01-09 12:00:00", 800.00, "ONLINE", "DE"), (10, 3, "2025-01-10 12:00:00", 150.00, "ONLINE", "DE"), (11, 3, "2025-01-11 12:00:00", 260.00, "ONLINE", "DE"),
        (12, 4, "2025-01-12 01:05:00", 70.00, "POS", "IN"), (13, 4, "2025-01-13 01:15:00", 80.00, "POS", "IN"), (14, 4, "2024-12-31 23:59:59", 500.00, "POS", "IN"),
        (15, 5, "2025-01-14 14:00:00", 40.00, "POS", "JP")],
      "AccountProfiles": [(1, "MEDIUM", 400.00, "US"), (2, "LOW", 250.00, "GB"), (3, "HIGH", None, "DE"), (4, "HIGH", 90.00, "IN")],
      "RiskAlerts": [(1, 2, "GEO", "HIGH", "2025-01-15 22:41:00", 0), (2, 2, "AMOUNT", "MEDIUM", "2025-01-15 22:41:05", 0), (3, 6, "AMOUNT", "HIGH", "2025-01-05 08:01:00", 0),
                     (4, 9, "AMOUNT", "HIGH", "2025-01-09 12:01:00", 0), (5, 12, "VELOCITY", "HIGH", "2025-01-12 01:06:00", 0), (6, 13, "VELOCITY", "HIGH", "2025-01-13 01:16:00", 1),
                     (7, 13, "GEO", "LOW", "2025-01-13 01:16:30", 0), (8, 15, "GEO", "HIGH", "2025-01-14 14:01:00", 0), (9, 14, "AMOUNT", "HIGH", "2024-12-31 23:59:59", 0)]}
A2 = {"Accounts": [(1, "Gus Lund", "US", "2017-01-10", "ACTIVE"), (2, "Hana Ito", "JP", "2023-04-04", "ACTIVE"), (3, "Ivo Petrov", "DE", "2016-09-09", "ACTIVE")],
      "Transactions": [(1, 1, "2025-01-02 00:00:00", 100.00, "POS", "US"), (2, 1, "2025-01-02 00:00:01", 100.00, "POS", "US"), (3, 1, "2025-01-31 12:00:00", 100.00, "POS", "US"),
                       (4, 2, "2025-01-10 10:00:00", 5000.00, "ONLINE", "JP"), (5, 2, "2025-01-11 10:00:00", 50.00, "ONLINE", "JP"), (6, 2, "2025-01-12 10:00:00", 50.00, "ONLINE", "JP"),
                       (7, 3, "2025-01-12 10:00:00", 75.00, "ATM", "DE"), (8, 3, "2025-01-13 10:00:00", 25.00, "ATM", "DE"), (9, 3, "2025-01-14 10:00:00", 25.00, "ATM", "DE")],
      "AccountProfiles": [(1, "LOW", 100.00, "US"), (2, "LOW", 1000.00, "JP"), (3, "MEDIUM", 20.00, "DE")],
      "RiskAlerts": [(1, 4, "AMOUNT", "HIGH", "2025-01-10 10:01:00", 0), (2, 7, "GEO", "HIGH", "2025-01-12 10:01:00", 0), (3, 8, "GEO", "HIGH", "2025-01-13 10:01:00", 0),
                     (4, 9, "GEO", "LOW", "2025-01-14 10:01:00", 0), (5, 3, "VELOCITY", "HIGH", "2025-01-31 12:01:00", 1), (6, 5, "VELOCITY", "HIGH", "2025-01-11 10:02:00", 0)]}
EMPTYQ = {"Accounts": [(1, "Kofi Mensah", "US", "2020-01-01", "CLOSED"), (2, "Lena Voss", "DE", "2020-01-01", "ACTIVE")],
          "Transactions": [(1, 2, "2025-01-05 10:00:00", 10.0, "POS", "DE"), (2, 2, "2025-01-06 10:00:00", -10.0, "POS", "DE"), (3, 2, "2025-01-07 10:00:00", 10.0, "POS", "DE"),
                           (4, 1, "2025-01-05 10:00:00", 10.0, "POS", "US"), (5, 1, "2025-01-06 10:00:00", 10.0, "POS", "US"), (6, 1, "2025-01-07 10:00:00", 10.0, "POS", "US")],
          "AccountProfiles": [(1, "LOW", 5.0, "US")], "RiskAlerts": []}
TIES = {"Accounts": [(3, "Zed Zed", "US", "2020-01-01", "ACTIVE"), (1, "Amy Amy", "US", "2020-01-01", "ACTIVE")],
        "Transactions": [(1, 3, "2025-01-05 10:00:00", 10.0, "POS", "US"), (2, 3, "2025-01-06 10:00:00", 20.0, "POS", "US"), (3, 3, "2025-01-07 10:00:00", 30.0, "POS", "US"),
                         (4, 1, "2025-01-05 10:00:00", 30.0, "POS", "US"), (5, 1, "2025-01-06 10:00:00", 20.0, "POS", "US"), (6, 1, "2025-01-07 10:00:00", 10.0, "POS", "US")],
        "AccountProfiles": [(1, "HIGH", 10.0, "US"), (3, "HIGH", 10.0, "US")],
        "RiskAlerts": [(1, 1, "GEO", "HIGH", "2025-01-05 10:00:00", 0), (2, 1, "AMOUNT", "HIGH", "2025-01-05 10:00:00", 0), (3, 1, "VELOCITY", "HIGH", "2025-01-05 10:00:00", 0)]}


Q3S = {"Accounts": [(1, "Amy Amy", "US", "2020-01-01", "ACTIVE"), (2, "Bo Bo", "US", "2020-01-01", "ACTIVE"), (3, "Cy Cy", "US", "2020-01-01", "ACTIVE")],
       "Transactions": [(1, 1, "2025-01-05 10:00:00", 1000.0, "POS", "US"), (2, 2, "2025-01-05 10:00:00", 1000.0, "POS", "US"), (3, 3, "2025-01-05 10:00:00", 301.0, "POS", "US"),
                        (4, 3, "2025-01-06 10:00:00", 299.0, "POS", "US"), (5, 3, "2025-01-07 10:00:00", 900.0, "POS", "US"), (6, 3, "2025-01-08 10:00:00", 5000.0, "POS", "US")],
       "AccountProfiles": [(1, "LOW", None, "US"), (3, "LOW", 100.0, "US")],
       "RiskAlerts": [(1, 1, "AMOUNT", "HIGH", "2025-01-05 10:00:00", 0), (2, 2, "AMOUNT", "HIGH", "2025-01-05 10:00:00", 0), (3, 3, "AMOUNT", "HIGH", "2025-01-05 10:00:00", 0),
                      (4, 4, "AMOUNT", "HIGH", "2025-01-06 10:00:00", 0), (5, 5, "AMOUNT", "HIGH", "2025-01-07 10:00:00", 1), (6, 6, "AMOUNT", "MEDIUM", "2025-01-08 10:00:00", 0),
                      (7, 6, "GEO", "HIGH", "2025-01-08 10:00:00", 0), (8, 6, "VELOCITY", "HIGH", "2025-01-08 10:00:00", 0)]}


def build():
    qs = []
    q1_sets = [("Sample data from the statement", A1), ("Second sample", A2), ("No qualifying account (empty result)", EMPTYQ),
               ("Equal totals -> tie broken by account_id", TIES), ("Randomised, boundary timestamps", gen(51, n_acc=10, n_txn=90)),
               ("Randomised, many refunds", gen(52, n_acc=12, n_txn=140))]
    ref1 = """SELECT a.account_id, a.customer_name,
       COUNT(*)                    AS txn_count,
       ROUND(SUM(t.amount), 2)     AS total_amount,
       MAX(t.amount)               AS largest_txn
FROM Accounts a
JOIN Transactions t ON t.account_id = a.account_id
WHERE a.status = 'ACTIVE'
  AND t.txn_time >= '2025-01-01 00:00:00' AND t.txn_time < '2025-02-01 00:00:00'
  AND t.amount > 0
GROUP BY a.account_id, a.customer_name
HAVING COUNT(*) >= 3
ORDER BY total_amount DESC, a.account_id ASC;"""
    qs.append(sql_question("oa02-sql-01", "select", 200, "January Spending of Active Accounts",
"""Compliance wants to review heavy January 2025 activity.

Join `Accounts` and `Transactions` and return, for every account whose `status = 'ACTIVE'`:

`account_id, customer_name, txn_count, total_amount, largest_txn`

Only count **purchases** (`amount > 0`; refunds are negative) made in January 2025, i.e. `txn_time` from `'2025-01-01 00:00:00'` up to but **excluding** `'2025-02-01 00:00:00'`. Return only accounts with **at least 3** such purchases. `total_amount` is `SUM(amount)` rounded to 2 decimals and `largest_txn` the maximum amount. Sort by `total_amount` descending, then `account_id` ascending.""",
        TABLES[:2], SCHEMA, q1_sets,
        "SELECT a.account_id, a.customer_name, COUNT(*) AS txn_count, 0.0 AS total_amount, 0.0 AS largest_txn\nFROM Accounts a\nJOIN Transactions t ON t.account_id = a.account_id\n-- TODO: filters, GROUP BY, HAVING, ORDER BY\n;",
        ref1, "Columns, in order: account_id, customer_name, txn_count, total_amount, largest_txn. Order: total_amount DESC, account_id ASC.",
        ["Date boundary tests: 2024-12-31 23:59:59, 2025-01-31 23:59:59, 2025-02-01 00:00:00.", "Refunds must be excluded before counting."],
        "Filter before grouping (status, half-open date range, amount > 0), group per account and apply HAVING COUNT(*) >= 3. A BETWEEN '2025-01-01' AND '2025-01-31' filter would miss late-January timestamps.",
        ["joins", "aggregation", "date ranges", "HAVING"], "medium"))
    q2_sets = [("Sample data from the statement", A1), ("Second sample", A2), ("Accounts without a profile and transactions without alerts only", EMPTYQ),
               ("Multiple alerts on one transaction must not inflate counts", TIES),
               ("Randomised", pick(guard_q2, 600, n_acc=10, n_txn=70)), ("Randomised larger", pick(guard_q2, 800, n_acc=12, n_txn=120, p_alert=0.5))]
    ref2 = """SELECT p.risk_tier,
       COUNT(DISTINCT t.txn_id) AS txn_count,
       COUNT(DISTINCT a.txn_id) AS flagged_count,
       ROUND(1.0 * COUNT(DISTINCT a.txn_id) / COUNT(DISTINCT t.txn_id), 4) AS flag_rate,
       MAX(t.amount) AS max_amount
FROM Transactions t
JOIN AccountProfiles p ON p.account_id = t.account_id
LEFT JOIN RiskAlerts a ON a.txn_id = t.txn_id
WHERE t.amount > 0
GROUP BY p.risk_tier
ORDER BY CASE p.risk_tier WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END;"""
    qs.append(sql_question("oa02-sql-02", "select", 150, "Alert Rate by Risk Tier",
"""Using `Transactions`, `AccountProfiles` and `RiskAlerts`, summarise purchases by the account's `risk_tier`.

Consider only transactions with `amount > 0` that belong to an account **having a profile**. A transaction is *flagged* if it has **at least one** row in `RiskAlerts` (any type, resolved or not). Note that a transaction can have several alerts.

Return one row per risk tier that has such transactions:

`risk_tier, txn_count, flagged_count, flag_rate, max_amount`

* `txn_count` – number of distinct qualifying transactions
* `flagged_count` – number of distinct qualifying transactions that are flagged
* `flag_rate` – `flagged_count / txn_count` rounded to 4 decimals
* `max_amount` – largest qualifying amount in the tier

Order tiers `HIGH`, `MEDIUM`, `LOW`.""",
        [TABLES[1], TABLES[2], TABLES[3]], SCHEMA, q2_sets,
        "SELECT p.risk_tier, COUNT(*) AS txn_count, 0 AS flagged_count, 0.0 AS flag_rate, MAX(t.amount) AS max_amount\nFROM Transactions t\nJOIN AccountProfiles p ON p.account_id = t.account_id\n-- TODO: LEFT JOIN alerts, avoid double counting\nGROUP BY p.risk_tier;",
        ref2, "Columns, in order: risk_tier, txn_count, flagged_count, flag_rate, max_amount. Order HIGH, MEDIUM, LOW.",
        ["Row multiplication by the alert join is the main trap: COUNT(*) fails the tests with several alerts per transaction.", "Custom tier ordering."],
        "LEFT JOIN alerts so un-alerted transactions stay in the denominator, and use COUNT(DISTINCT ...) because one transaction with 3 alerts produces 3 joined rows. CASE gives the required tier order.",
        ["joins", "COUNT DISTINCT", "LEFT JOIN", "CASE"], "medium"))
    q3_sets = [("Sample data from the statement", A1), ("Second sample", A2), ("Empty alerts table", EMPTYQ), ("NULL average, missing profile, just above/below 3x, resolved and non-HIGH alerts", Q3S),
               ("Randomised", pick(guard_q3, 1000, n_acc=10, n_txn=70, p_alert=0.5, avg_rng=(20, 300))), ("Randomised larger", pick(guard_q3, 1200, n_acc=12, n_txn=130, p_alert=0.5, avg_rng=(20, 400)))]
    ref3 = """UPDATE RiskAlerts
SET severity = 'CRITICAL'
WHERE resolved = 0
  AND severity = 'HIGH'
  AND (SELECT t.amount FROM Transactions t WHERE t.txn_id = RiskAlerts.txn_id)
      > 3 * (SELECT p.avg_monthly_spend
             FROM Transactions t JOIN AccountProfiles p ON p.account_id = t.account_id
             WHERE t.txn_id = RiskAlerts.txn_id);"""
    qs.append(sql_question("oa02-sql-03", "update", 100, "Escalate Alerts on Out-of-Pattern Spend",
"""Escalate high-severity open alerts whose transaction is unusually large for the customer.

Update `RiskAlerts` so that `severity` becomes `'CRITICAL'` for every alert that satisfies **all** of:

* `resolved = 0`;
* current `severity = 'HIGH'`;
* the alert's transaction amount is **strictly greater than 3 times** the `avg_monthly_spend` of the transaction's account (taken from `AccountProfiles`).

Alerts whose account has no profile, or whose `avg_monthly_spend` is NULL, must **not** be changed. No other row or table may change.""",
        TABLES, SCHEMA, q3_sets,
        "UPDATE RiskAlerts\nSET severity = 'CRITICAL'\nWHERE resolved = 0\n  AND severity = 'HIGH'\n  -- TODO: compare the transaction amount with 3 * avg_monthly_spend\n  AND 1 = 0;",
        ref3, "Final contents of RiskAlerts, Transactions and AccountProfiles are compared with the expected post-update state.",
        ["NULL/missing profile rows must be left untouched.", "Strict '>' is tested at values just above/below 3x."],
        "Correlated scalar subqueries fetch the amount and the profile's average spend for each alert. When a profile is missing or the average is NULL the comparison is NULL and the alert is not updated, which is exactly the required behaviour.",
        ["UPDATE", "correlated subquery", "NULL handling"], "medium",
        check_queries=[{"id": "alerts", "sql": "SELECT * FROM RiskAlerts ORDER BY alert_id"}, {"id": "txns", "sql": "SELECT * FROM Transactions ORDER BY txn_id"},
                       {"id": "profiles", "sql": "SELECT * FROM AccountProfiles ORDER BY account_id"}]))
    return qs
