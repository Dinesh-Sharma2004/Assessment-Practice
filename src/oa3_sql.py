import random
from datetime import datetime, timedelta
from fractions import Fraction
from builder import sql_question
from oa1_sql import _half

SCHEMA = """CREATE TABLE NewsArticles (
  article_id   INTEGER PRIMARY KEY,
  headline     TEXT NOT NULL,
  source       TEXT NOT NULL,
  published_at TEXT NOT NULL,          -- 'YYYY-MM-DD HH:MM:SS'
  language     TEXT NOT NULL           -- ISO code, e.g. 'en'
);
CREATE TABLE Entities (
  entity_id   INTEGER PRIMARY KEY,
  entity_name TEXT NOT NULL UNIQUE,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('COMPANY','PERSON','SECTOR')),
  ticker      TEXT                      -- NULL for non-companies
);
CREATE TABLE SentimentScores (
  article_id INTEGER NOT NULL REFERENCES NewsArticles(article_id),
  entity_id  INTEGER NOT NULL REFERENCES Entities(entity_id),
  score      REAL NOT NULL CHECK (score BETWEEN -1 AND 1),
  confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  PRIMARY KEY (article_id, entity_id)
);
CREATE TABLE MarketEvents (
  event_id      INTEGER PRIMARY KEY,
  entity_id     INTEGER NOT NULL REFERENCES Entities(entity_id),
  event_time    TEXT NOT NULL,          -- 'YYYY-MM-DD HH:MM:SS'
  event_type    TEXT NOT NULL,
  magnitude_pct REAL NOT NULL           -- signed price move in percent
);"""
TABLES = [
 {"name": "NewsArticles", "description": "News items with publication timestamp.", "columns": [
   {"name": "article_id", "type": "INTEGER", "description": "Primary key"}, {"name": "headline", "type": "TEXT", "description": "Headline"},
   {"name": "source", "type": "TEXT", "description": "Publisher/source name"}, {"name": "published_at", "type": "TEXT", "description": "'YYYY-MM-DD HH:MM:SS'"},
   {"name": "language", "type": "TEXT", "description": "Language code"}]},
 {"name": "Entities", "description": "Companies, people and sectors recognised in text.", "columns": [
   {"name": "entity_id", "type": "INTEGER", "description": "Primary key"}, {"name": "entity_name", "type": "TEXT", "description": "Unique name"},
   {"name": "entity_type", "type": "TEXT", "description": "'COMPANY','PERSON' or 'SECTOR'"}, {"name": "ticker", "type": "TEXT", "description": "Ticker for companies, else NULL"}]},
 {"name": "SentimentScores", "description": "Sentiment of an article towards an entity (one row per article/entity pair).", "columns": [
   {"name": "article_id", "type": "INTEGER", "description": "FK to NewsArticles"}, {"name": "entity_id", "type": "INTEGER", "description": "FK to Entities"},
   {"name": "score", "type": "REAL", "description": "Sentiment in [-1, 1]"}, {"name": "confidence", "type": "REAL", "description": "Model confidence in [0, 1]"}]},
 {"name": "MarketEvents", "description": "Observed market events for entities.", "columns": [
   {"name": "event_id", "type": "INTEGER", "description": "Primary key"}, {"name": "entity_id", "type": "INTEGER", "description": "FK to Entities"},
   {"name": "event_time", "type": "TEXT", "description": "'YYYY-MM-DD HH:MM:SS'"}, {"name": "event_type", "type": "TEXT", "description": "'PRICE_MOVE','VOLUME_SPIKE','HALT'"},
   {"name": "magnitude_pct", "type": "REAL", "description": "Signed percent price move"}]},
]
ENT = [(1, "Acme Corp", "COMPANY", "ACME"), (2, "Borealis Bank", "COMPANY", "BORB"), (3, "Cirrus Software", "COMPANY", "CIRS"),
       (4, "Delta Energy", "COMPANY", "DLTE"), (5, "Dr. Elena Park", "PERSON", None), (6, "Semiconductors", "SECTOR", None)]
fmt = lambda d: d.strftime("%Y-%m-%d %H:%M:%S")


def gen(seed, n_art=24, n_ent=6, p_pair=0.35, n_ev=25, langs=("en", "en", "en", "fr", "de"), conf_step=100):
    r = random.Random(seed)
    base = datetime(2025, 3, 3, 6, 0, 0)
    arts = []
    for i in range(1, n_art + 1):
        t = base + timedelta(hours=r.randrange(0, 96), minutes=r.randrange(0, 60), seconds=r.randrange(0, 60))
        arts.append((i, f"Headline {i}", r.choice(["Wire", "Blog", "Press"]), fmt(t), r.choice(langs)))
    ents = ENT[:n_ent]
    sc = []
    for a in arts:
        for e in ents:
            if r.random() < p_pair:
                sc.append((a[0], e[0], round(r.choice([-1, 1]) * r.randrange(0, 100) / 100, 2), round(r.randrange(20, 100) / 100, 2)))
    ev = []
    for k in range(1, n_ev + 1):
        a = r.choice(arts); t = datetime.strptime(a[3], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=r.randrange(-300, 1700), seconds=r.randrange(0, 59))
        ev.append((k, r.choice(ents)[0], fmt(t), r.choice(["PRICE_MOVE", "VOLUME_SPIKE", "HALT"]), round(r.choice([-1, 1]) * r.uniform(0.1, 6), 2)))
    return {"NewsArticles": arts, "Entities": ents, "SentimentScores": sc, "MarketEvents": ev}


def F(x): return Fraction(str(x))

def guard_q1(d):
    typ = {e[0]: e for e in d["Entities"]}
    by = {}
    for s in d["SentimentScores"]:
        if typ[s[1]][2] == "COMPANY" and s[3] >= 0.5:
            by.setdefault(s[1], []).append(s)
    for v in by.values():
        if len(v) >= 2 and _half(sum(F(x[2]) * F(x[3]) for x in v) / sum(F(x[3]) for x in v), 3): return False
    return True

def guard_q2(d):
    art = {a[0]: a for a in d["NewsArticles"]}
    by = {}
    for s in d["SentimentScores"]:
        a = art[s[0]]
        if a[4] == "en": by.setdefault((s[1], a[3][:10]), []).append(F(s[2]))
    return not any(_half(sum(v) / len(v), 3) for v in by.values())

def pick(guard, seed0, **kw):
    for s in range(seed0, seed0 + 800):
        d = gen(s, **kw)
        if guard(d): return d
    raise RuntimeError

S1 = {"NewsArticles": [(1, "Acme beats estimates", "Wire", "2025-03-03 09:00:00", "en"), (2, "Acme faces lawsuit", "Blog", "2025-03-03 15:30:00", "en"),
                       (3, "Borealis raises guidance", "Wire", "2025-03-04 08:15:00", "en"), (4, "Acme unveils chip", "Press", "2025-03-04 10:00:00", "en"),
                       (5, "Acme recule en bourse", "Wire", "2025-03-04 11:00:00", "fr"), (6, "Cirrus launches product", "Wire", "2025-03-05 12:00:00", "en"),
                       (7, "Park comments on Cirrus", "Press", "2025-03-05 13:00:00", "en"), (8, "Acme outlook cut", "Wire", "2025-03-06 09:30:00", "en")],
      "Entities": ENT,
      "SentimentScores": [(1, 1, 0.80, 0.90), (2, 1, -0.60, 0.70), (3, 2, 0.50, 0.60), (4, 1, 0.40, 0.80), (5, 1, -0.90, 0.95), (6, 3, 0.30, 0.40),
                          (6, 6, 0.20, 0.80), (7, 5, -0.10, 0.60), (7, 3, 0.50, 0.50), (8, 1, -0.70, 0.85), (3, 3, 0.10, 0.55)],
      "MarketEvents": [(1, 1, "2025-03-03 10:00:00", "PRICE_MOVE", 2.5), (2, 1, "2025-03-03 16:00:00", "PRICE_MOVE", 1.2), (3, 2, "2025-03-05 08:15:00", "PRICE_MOVE", 1.0),
                       (4, 3, "2025-03-05 12:30:00", "VOLUME_SPIKE", 0.0), (5, 1, "2025-03-06 20:00:00", "PRICE_MOVE", -3.1), (6, 3, "2025-03-06 12:00:01", "PRICE_MOVE", 2.0),
                       (7, 1, "2025-03-04 11:30:00", "HALT", -0.5), (8, 5, "2025-03-05 14:00:00", "PRICE_MOVE", -1.0), (9, 3, "2025-03-05 20:00:00", "PRICE_MOVE", 1.1)]}
S2 = {"NewsArticles": [(1, "Delta oil surge", "Wire", "2025-04-01 07:00:00", "en"), (2, "Delta pipeline leak", "Wire", "2025-04-01 18:00:00", "en"),
                       (3, "Delta recovers", "Blog", "2025-04-03 09:00:00", "en"), (4, "Delta beats", "Wire", "2025-04-03 09:30:00", "en"), (5, "Borealis merger rumor", "Press", "2025-04-02 11:00:00", "en")],
      "Entities": ENT[:4] + [ENT[5]],
      "SentimentScores": [(1, 4, 0.90, 0.99), (2, 4, -0.80, 0.90), (3, 4, 0.20, 0.50), (4, 4, 0.60, 0.50), (5, 2, 0.70, 0.75), (1, 2, 0.10, 0.20), (3, 6, 0.50, 0.95), (4, 6, 0.40, 0.95)],
      "MarketEvents": [(1, 4, "2025-04-01 07:10:00", "PRICE_MOVE", 1.5), (2, 4, "2025-04-02 18:00:00", "PRICE_MOVE", -2.0), (3, 4, "2025-04-02 18:00:01", "PRICE_MOVE", -2.0),
                       (4, 4, "2025-04-03 12:00:00", "PRICE_MOVE", -1.0), (5, 6, "2025-04-04 08:00:00", "PRICE_MOVE", 0.7), (6, 2, "2025-04-01 12:00:00", "PRICE_MOVE", 0.9)]}
EDGE_EMPTY = {"NewsArticles": [(1, "x", "Wire", "2025-05-01 00:00:00", "fr")], "Entities": ENT[:3], "SentimentScores": [(1, 1, 0.5, 0.4), (1, 2, -0.5, 0.49)], "MarketEvents": []}
EDGE_CAP = {"NewsArticles": [(1, "a", "Wire", "2025-05-01 00:00:00", "en"), (2, "b", "Wire", "2025-05-02 00:00:00", "en"), (3, "c", "Wire", "2025-05-02 23:59:59", "en")],
            "Entities": ENT[:2],
            "SentimentScores": [(1, 1, 0.50, 0.95), (2, 1, -0.50, 1.00), (3, 1, 0.01, 0.50), (1, 2, 0.00, 0.50), (2, 2, 0.30, 0.50)],
            "MarketEvents": [(1, 1, "2025-05-01 10:00:00", "PRICE_MOVE", 1.0), (2, 1, "2025-05-01 11:00:00", "PRICE_MOVE", 2.0), (3, 1, "2025-05-02 01:00:00", "PRICE_MOVE", -1.0),
                             (4, 1, "2025-05-03 00:00:01", "PRICE_MOVE", 1.0), (5, 2, "2025-05-01 05:00:00", "PRICE_MOVE", 1.0), (6, 2, "2025-04-30 23:59:59", "PRICE_MOVE", 1.0), (7, 1, "2025-05-03 00:00:00", "PRICE_MOVE", 3.0)]}
EDGE_CAP["MarketEvents"] = [e for e in EDGE_CAP["MarketEvents"] if e[0] != 7]


def build():
    qs = []
    q1_sets = [("Sample data from the statement", S1), ("Second sample", S2), ("Everything filtered out (empty result)", EDGE_EMPTY),
               ("Cap / boundary sample", EDGE_CAP), ("Randomised", pick(guard_q1, 100, n_art=30)), ("Randomised larger", pick(guard_q1, 300, n_art=60, p_pair=0.5))]
    ref1 = """SELECT e.entity_name, e.ticker,
       COUNT(*) AS n_mentions,
       ROUND(SUM(s.score * s.confidence) / SUM(s.confidence), 3) AS weighted_score,
       MIN(s.score) AS min_score
FROM SentimentScores s
JOIN Entities e ON e.entity_id = s.entity_id
WHERE e.entity_type = 'COMPANY' AND s.confidence >= 0.5
GROUP BY e.entity_id, e.entity_name, e.ticker
HAVING COUNT(*) >= 2
ORDER BY weighted_score DESC, e.entity_name ASC;"""
    qs.append(sql_question("oa03-sql-01", "select", 200, "Confidence-Weighted Company Sentiment",
"""An NLP pipeline stores one sentiment score per (article, entity). Using `SentimentScores` and `Entities`, build a leaderboard of **companies** (`entity_type = 'COMPANY'`).

Only use scores with `confidence >= 0.5`. For each company return:

`entity_name, ticker, n_mentions, weighted_score, min_score`

* `n_mentions` – number of qualifying scores
* `weighted_score` – confidence-weighted mean `SUM(score * confidence) / SUM(confidence)` rounded to 3 decimals
* `min_score` – the lowest qualifying `score`

Keep companies with **at least 2** qualifying scores. Sort by `weighted_score` descending, then `entity_name` ascending.""",
        TABLES[1:3], SCHEMA, q1_sets,
        "SELECT e.entity_name, e.ticker, COUNT(*) AS n_mentions, 0.0 AS weighted_score, MIN(s.score) AS min_score\nFROM SentimentScores s\nJOIN Entities e ON e.entity_id = s.entity_id\n-- TODO: filters, HAVING, ORDER BY\nGROUP BY e.entity_id, e.entity_name, e.ticker;",
        ref1, "Columns, in order: entity_name, ticker, n_mentions, weighted_score, min_score. Order: weighted_score DESC, entity_name ASC.",
        ["Low-confidence rows must be filtered before aggregation (WHERE, not HAVING).", "Non-company entities must be excluded.", "Weighted (not simple) average."],
        "WHERE removes low-confidence scores and non-companies before grouping; the weighted mean divides the confidence-weighted sum by total confidence; HAVING keeps companies with >= 2 qualifying rows.",
        ["joins", "weighted average", "HAVING"], "medium"))
    q2_sets = [("Sample data from the statement", S1), ("Second sample", S2), ("No English articles (empty result)", EDGE_EMPTY),
               ("Cap / boundary sample", EDGE_CAP), ("Randomised", pick(guard_q2, 500, n_art=30)), ("Randomised larger", pick(guard_q2, 700, n_art=70, p_pair=0.5))]
    ref2 = """WITH daily AS (
  SELECT e.entity_name, DATE(a.published_at) AS day,
         COUNT(*) AS n_scores, ROUND(AVG(s.score), 3) AS avg_score
  FROM NewsArticles a
  JOIN SentimentScores s ON s.article_id = a.article_id
  JOIN Entities e        ON e.entity_id  = s.entity_id
  WHERE a.language = 'en'
  GROUP BY e.entity_id, e.entity_name, DATE(a.published_at)
)
SELECT entity_name, day, n_scores, avg_score,
       ROUND(avg_score - LAG(avg_score) OVER (PARTITION BY entity_name ORDER BY day), 3) AS change_from_prev
FROM daily
ORDER BY entity_name, day;"""
    qs.append(sql_question("oa03-sql-02", "select", 150, "Daily Sentiment Momentum",
"""Using `NewsArticles`, `SentimentScores` and `Entities`, compute day-over-day sentiment momentum for **English** articles only (`language = 'en'`).

For each entity and calendar day (`DATE(published_at)`) that has at least one English score, return:

`entity_name, day, n_scores, avg_score, change_from_prev`

* `n_scores` – number of scores that day
* `avg_score` – average `score`, rounded to 3 decimals
* `change_from_prev` – `avg_score` minus the entity's `avg_score` on its **previous day that has data**, rounded to 3 decimals; `NULL` for the entity's first day

Sort by `entity_name`, then `day`.""",
        TABLES[:3], SCHEMA, q2_sets,
        "SELECT e.entity_name, DATE(a.published_at) AS day, COUNT(*) AS n_scores, 0.0 AS avg_score, NULL AS change_from_prev\nFROM NewsArticles a\nJOIN SentimentScores s ON s.article_id = a.article_id\nJOIN Entities e ON e.entity_id = s.entity_id\nGROUP BY e.entity_name, DATE(a.published_at);",
        ref2, "Columns, in order: entity_name, day (YYYY-MM-DD text), n_scores, avg_score, change_from_prev. Order: entity_name, day.",
        ["LAG must be computed per entity (PARTITION BY) after daily aggregation.", "Gaps in days: the previous *available* day is used."],
        "Aggregate to entity-day first in a CTE, then apply LAG over the aggregated rows partitioned by entity and ordered by day. Applying LAG before grouping would compare individual articles instead of daily averages.",
        ["CTE", "LAG", "joins", "date functions"], "medium"))
    q3_sets = [("Sample data from the statement", S1), ("Second sample", S2), ("Empty MarketEvents", EDGE_EMPTY), ("Cap at 1.0 and 24-hour window boundaries", EDGE_CAP),
               ("Randomised", gen(900, n_art=30, n_ev=40)), ("Randomised larger", gen(901, n_art=60, p_pair=0.5, n_ev=120))]
    ref3 = """UPDATE SentimentScores
SET confidence = ROUND(MIN(1.0, confidence + 0.1), 2)
WHERE EXISTS (
  SELECT 1
  FROM NewsArticles a
  JOIN MarketEvents m ON m.entity_id = SentimentScores.entity_id
  WHERE a.article_id = SentimentScores.article_id
    AND m.event_time >= a.published_at
    AND m.event_time <= DATETIME(a.published_at, '+1 day')
    AND ((SentimentScores.score > 0 AND m.magnitude_pct > 0) OR (SentimentScores.score < 0 AND m.magnitude_pct < 0))
);"""
    qs.append(sql_question("oa03-sql-03", "update", 100, "Boost Sentiment Confidence When Markets Agree",
"""A feedback loop raises confidence in sentiment scores that were *confirmed by the market*.

Update `SentimentScores` so that `confidence` increases by `0.1`, capped at `1.0`, for every row for which **at least one** `MarketEvents` row exists such that:

* it has the same `entity_id`;
* `event_time` is at or after the article's `published_at` and no later than 24 hours after it (inclusive);
* the direction agrees: `score > 0` with `magnitude_pct > 0`, or `score < 0` with `magnitude_pct < 0` (a zero score or zero move never agrees).

Each score row is increased **at most once**, no matter how many events confirm it. Round the new confidence to 2 decimals. No other rows or tables may change.""",
        TABLES, SCHEMA, q3_sets,
        "UPDATE SentimentScores\nSET confidence = confidence + 0.1\nWHERE 1 = 0;  -- TODO: EXISTS (confirming event within 24h); cap at 1.0",
        ref3, "Final contents of SentimentScores, NewsArticles and MarketEvents are compared with the expected post-update state (confidence tolerance 1e-6).",
        ["Use EXISTS (or DISTINCT) so that several confirming events do not boost more than once.", "Cap at 1.0 is tested.", "Window boundaries use event_time >= published_at and <= +24 hours."],
        "A correlated EXISTS subquery joins the article (for published_at) to market events of the same entity. Because EXISTS yields a boolean, multiple confirming events cannot double-boost. MIN(1.0, x) inside ROUND caps the value; DATETIME(published_at, '+1 day') computes the window end.",
        ["UPDATE", "EXISTS", "date arithmetic"], "hard",
        check_queries=[{"id": "scores", "sql": "SELECT * FROM SentimentScores ORDER BY article_id, entity_id"}, {"id": "events", "sql": "SELECT * FROM MarketEvents ORDER BY event_id"},
                       {"id": "articles", "sql": "SELECT * FROM NewsArticles ORDER BY article_id"}]))
    return qs
