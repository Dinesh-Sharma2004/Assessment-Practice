import random
import numpy as np
import pandas as pd
from builder import pandas_question, dsa_question

NAN = float("nan")

# ================================ PANDAS ================================
def hl(rows):
    return pd.DataFrame(rows, columns=["article_id", "headline", "source", "published_at"]).astype({"article_id": "int64"})

WORDS = ["Acme", "profit", "UP", "5%", "Q3", "Fed", "holds", "rates", "steady", "Borealis", "bank's", "outlook", "cut", "—", "!!", "merger", "talks"]

def rand_hl(seed, n=30):
    r = random.Random(seed); rows = []
    for i in range(1, n + 1):
        base = r.choice([["Acme", "profit", "UP", "5%"], ["Fed", "holds", "rates", "steady"], ["Borealis", "bank's", "outlook", "cut"], ["Q3", "merger", "talks"]])
        h = " ".join(base) if r.random() < 0.6 else " ".join(r.choice(WORDS) for _ in range(r.randrange(1, 5)))
        h = r.choice([h, h.upper(), "  " + h + "!!", h.replace(" ", "  ")])
        if r.random() < 0.05: h = None
        t = f"2025-03-0{r.randrange(1, 4)} {r.randrange(0, 24):02d}:{r.randrange(0, 60):02d}:00"
        if r.random() < 0.05: t = "not a date"
        rows.append((i, h, r.choice(["Wire", "Blog"]), t))
    return hl(rows)

REF_P1 = '''import pandas as pd

def normalize_headlines(articles):
    df = articles.copy()
    df["published_at"] = pd.to_datetime(df["published_at"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["headline", "published_at"])
    df["headline_norm"] = (df["headline"].str.lower()
                           .str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip())
    df = df[df["headline_norm"] != ""]
    df = df.sort_values(["headline_norm", "published_at", "article_id"], kind="mergesort")
    sizes = df.groupby("headline_norm")["article_id"].transform("size")
    df["n_duplicates"] = (sizes - 1).astype("int64")
    df = df.drop_duplicates(subset="headline_norm", keep="first")
    df = df.sort_values(["published_at", "article_id"], kind="mergesort")
    return df[["article_id", "headline_norm", "published_at", "n_duplicates"]].reset_index(drop=True)
'''

def mn(rows):
    return pd.DataFrame(rows, columns=["mention_id", "article_id", "text_span"]).astype({"mention_id": "int64", "article_id": "int64"})

def al(rows):
    return pd.DataFrame(rows, columns=["alias", "entity_id"]).astype({"entity_id": "int64"})

ALIASES = [("Acme Corp.", 1), ("acme", 1), ("Acme Corporation Ltd", 1), ("Borealis Bank PLC", 2), ("borealis", 3), ("Borealis", 2), ("Cirrus Software Inc", 4), ("Dr. Park", 5)]
SPANS = ["ACME", "Acme Corp", "Borealis Bank", "borealis", "Cirrus software, Inc.", "cirrus software", "Unknown Co", "Dr Park", "Dr. Park", "inc", "  Acme   Corporation  "]

def rand_mn(seed, n=25):
    r = random.Random(seed)
    return mn([(i, r.randrange(1, 6), r.choice(SPANS + [None] if False else SPANS)) for i in range(1, n + 1)])

REF_P2 = '''import pandas as pd

SUFFIX = r"(?:\\s+(?:inc|corp|corporation|ltd|plc|co))+$"

def _norm(s):
    s = s.str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
    return s.str.replace(SUFFIX, "", regex=True)

def match_entities(mentions, aliases):
    m = mentions.copy()
    a = aliases.copy()
    m["key"] = _norm(m["text_span"])
    a["key"] = _norm(a["alias"])
    a = a.sort_values(["key", "entity_id"]).drop_duplicates("key", keep="first")[["key", "entity_id"]]
    out = m.merge(a, on="key", how="left")
    out["entity_id"] = out["entity_id"].astype("Int64")
    out["matched"] = out["entity_id"].notna()
    return out.sort_values("mention_id")[["mention_id", "article_id", "entity_id", "matched"]].reset_index(drop=True)
'''

def sc(rows):
    return pd.DataFrame(rows, columns=["article_id", "entity_id", "published_at", "score"]).astype({"article_id": "int64", "entity_id": "int64", "score": "float64"})

def rand_sc(seed, n=60, n_ent=3):
    r = random.Random(seed); rows = []
    for i in range(n):
        t = f"2025-03-0{r.randrange(1, 3)} {r.randrange(0, 24):02d}:{r.randrange(0, 60):02d}:{r.randrange(0, 60):02d}"
        if r.random() < 0.04: t = "bad"
        rows.append((r.randrange(1, 25), r.randrange(1, n_ent + 1), t, NAN if r.random() < 0.08 else round(r.uniform(-1, 1), 2)))
    return sc(rows)

REF_P3 = '''import pandas as pd

def six_hour_sentiment(scores):
    df = scores.copy()
    df["published_at"] = pd.to_datetime(df["published_at"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["published_at", "score"])
    df = df.drop_duplicates(subset=["article_id", "entity_id"], keep="last")
    df["bin_start"] = df["published_at"].dt.floor("6h")
    out = (df.groupby(["entity_id", "bin_start"], as_index=False)
             .agg(mean_score=("score", "mean"), n_articles=("article_id", "nunique"), max_abs_score=("score", lambda s: s.abs().max())))
    return out.sort_values(["entity_id", "bin_start"]).reset_index(drop=True)
'''

def build_pandas():
    qs = []
    h1 = hl([(1, "Acme's Q3 profit — UP 5%!", "Wire", "2025-03-01 09:00:00"), (2, "ACME S Q3 PROFIT UP 5", "Blog", "2025-03-01 08:00:00"),
             (3, "acme  s q3 profit up 5 !!", "Blog", "2025-03-01 08:00:00"), (4, "Fed holds rates steady", "Wire", "2025-03-01 07:30:00"),
             (5, None, "Wire", "2025-03-01 10:00:00"), (6, "???", "Wire", "2025-03-01 10:00:00"), (7, "Fed holds rates", "Wire", "not a time"), (8, "Fed holds rates steady.", "Press", "2025-03-02 07:30:00")])
    h2 = hl([(10, "Single headline", "Wire", "2025-03-05 00:00:00")])
    d1 = [("Sample: punctuation, case, duplicates with ties, missing values", {"articles": h1}, {}), ("One article", {"articles": h2}, {}),
          ("Nothing valid (empty result)", {"articles": hl([(1, "!!!", "x", "2025-03-01 00:00:00"), (2, "ok", "x", "bad")])}, {}),
          ("Randomised", {"articles": rand_hl(31)}, {}), ("Randomised larger", {"articles": rand_hl(32, 80)}, {}), ("Randomised small", {"articles": rand_hl(33, 12)}, {})]
    qs.append(pandas_question("oa03-pd-01", 150, "Normalise and Deduplicate Headlines",
"""Implement `normalize_headlines(articles)` to prepare headlines for NLP.

1. Parse `published_at` with format `%Y-%m-%d %H:%M:%S` (invalid → NaT). Drop rows with a missing `headline` or an invalid `published_at`.
2. Create `headline_norm`: lower-case the headline, replace every run of characters other than `a-z` and `0-9` with a single space, and strip leading/trailing spaces. Drop rows whose `headline_norm` is empty.
3. Rows with the same `headline_norm` are duplicates. Keep the one with the **earliest** `published_at` (tie → smallest `article_id`) and record `n_duplicates` = number of *other* rows collapsed into it (int64).
4. Return `article_id, headline_norm, published_at, n_duplicates`, sorted by `published_at` then `article_id`, with default index.""",
        "normalize_headlines", "def normalize_headlines(articles: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef normalize_headlines(articles: pd.DataFrame) -> pd.DataFrame:\n    df = articles.copy()\n    # TODO\n    return df\n",
        {"articles": [("article_id", "int64", "Unique id"), ("headline", "str", "Raw headline, may be missing"), ("source", "str", "Publisher"), ("published_at", "str", "Timestamp text")]},
        d1, REF_P1, "Columns [article_id int64, headline_norm str, published_at datetime64, n_duplicates int64].",
        ["Apostrophes/dashes become spaces (\"acme s q3...\").", "The tie rule on equal timestamps is tested in the sample."],
        "Vectorised string cleaning with str.lower + regex replace; sort so the desired survivor comes first, compute group sizes via transform('size'), then drop_duplicates(keep='first').",
        ["string methods", "deduplication", "datetime"], "medium"))
    m1 = mn([(1, 10, "ACME"), (2, 10, "Acme Corp"), (3, 11, "Borealis Bank"), (4, 11, "borealis"), (5, 12, "Cirrus software, Inc."), (6, 12, "Unknown Co"), (7, 13, "Dr Park"), (8, 13, "inc"), (9, 14, "  Acme   Corporation  ")])
    d2 = [("Sample: suffix stripping, ambiguous alias, unmatched", {"mentions": m1, "aliases": al(ALIASES)}, {}),
          ("Aliases that normalise to the same key keep the smallest entity_id", {"mentions": mn([(1, 1, "Borealis")]), "aliases": al([("borealis", 9), ("BOREALIS Inc", 3), ("Borealis Corp", 7)])}, {}),
          ("No mentions", {"mentions": mn([]), "aliases": al(ALIASES)}, {}), ("Randomised", {"mentions": rand_mn(41), "aliases": al(ALIASES)}, {}),
          ("Randomised larger", {"mentions": rand_mn(42, 80), "aliases": al(ALIASES[::-1])}, {}), ("Empty aliases", {"mentions": rand_mn(43, 8), "aliases": al([])}, {})]
    qs.append(pandas_question("oa03-pd-02", 150, "Entity Linking by Normalised Aliases",
"""Implement `match_entities(mentions, aliases)` to link text spans to entity ids.

Define a *key* for any text: lower-case; replace each run of non-`[a-z0-9]` characters by one space; strip; then **repeatedly remove a trailing company suffix word** from `{inc, corp, corporation, ltd, plc, co}` (only when it is preceded by another word – a text that is just `inc` keeps its key `inc`).

1. Compute keys for `mentions.text_span` and for `aliases.alias`.
2. If several aliases share a key, keep only the one with the **smallest `entity_id`**.
3. Left-join mentions to the alias table on the key.
4. `entity_id` is a nullable integer (`Int64`) – `<NA>` for unmatched mentions; `matched` is a bool.

Return `mention_id, article_id, entity_id, matched` sorted by `mention_id`, default index.""",
        "match_entities", "def match_entities(mentions: pd.DataFrame, aliases: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef match_entities(mentions: pd.DataFrame, aliases: pd.DataFrame) -> pd.DataFrame:\n    m = mentions.copy()\n    # TODO\n    return m\n",
        {"mentions": [("mention_id", "int64", "Unique id"), ("article_id", "int64", "Article"), ("text_span", "str", "Text found in the article")],
         "aliases": [("alias", "str", "Known alias"), ("entity_id", "int64", "Entity the alias refers to")]},
        d2, REF_P2, "Columns [mention_id int64, article_id int64, entity_id Int64 (nullable), matched bool].",
        ["Left join must not drop or duplicate mentions (dedupe aliases first).", "Nullable integer output is checked with null-aware comparison."],
        "Normalise both sides with the same vectorised function, deduplicate aliases on the key (smallest entity_id), merge with how='left' and cast entity_id to the nullable Int64 type so missing links stay missing rather than becoming floats.",
        ["merge", "string normalisation", "nullable dtypes"], "hard"))
    s1 = sc([(1, 1, "2025-03-01 00:00:00", 0.5), (2, 1, "2025-03-01 05:59:59", -0.5), (3, 1, "2025-03-01 06:00:00", 0.25), (3, 1, "2025-03-01 06:00:00", 0.75),
             (4, 2, "2025-03-01 13:00:00", NAN), (5, 2, "2025-03-01 13:30:00", -0.8), (5, 2, "bad", 0.9), (6, 2, "2025-03-02 18:00:00", 0.1)])
    d3 = [("Sample: bins at 6-hour boundaries, duplicate pair, NaN and bad timestamp", {"scores": s1}, {}), ("Single row", {"scores": sc([(1, 7, "2025-03-04 23:59:59", -0.3)])}, {}),
          ("All invalid (empty result)", {"scores": sc([(1, 1, "x", 0.1), (2, 1, "2025-03-01 00:00:00", NAN)])}, {}), ("Randomised", {"scores": rand_sc(51)}, {}),
          ("Randomised larger", {"scores": rand_sc(52, 200, 4)}, {}), ("Randomised sparse", {"scores": rand_sc(53, 15, 5)}, {})]
    qs.append(pandas_question("oa03-pd-03", 100, "Six-Hour Sentiment Bins",
"""Implement `six_hour_sentiment(scores)`.

1. Parse `published_at` (`%Y-%m-%d %H:%M:%S`, invalid → NaT) and drop rows with an invalid timestamp or a missing `score`.
2. If a `(article_id, entity_id)` pair repeats, keep the **last** occurrence in input order.
3. Assign each row to a 6-hour bin: `bin_start = published_at.floor('6h')`.
4. For each `(entity_id, bin_start)` compute `mean_score`, `n_articles` (distinct `article_id`) and `max_abs_score` (largest absolute score).
5. Return `entity_id, bin_start, mean_score, n_articles, max_abs_score` sorted by `entity_id`, `bin_start`; only bins that contain data appear.""",
        "six_hour_sentiment", "def six_hour_sentiment(scores: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef six_hour_sentiment(scores: pd.DataFrame) -> pd.DataFrame:\n    df = scores.copy()\n    # TODO\n    return df\n",
        {"scores": [("article_id", "int64", "Article"), ("entity_id", "int64", "Entity"), ("published_at", "str", "Timestamp text"), ("score", "float64", "Sentiment; may be NaN")]},
        d3, REF_P3, "Columns [entity_id int64, bin_start datetime64, mean_score float64, n_articles int64, max_abs_score float64].",
        ["Bin edges (05:59:59 vs 06:00:00) are tested.", "Duplicates are removed before aggregation."],
        "Coerce timestamps, drop invalid rows, dedupe with keep='last', floor to 6h and use groupby with named aggregation; nunique counts distinct articles.",
        ["datetime floor", "groupby", "time bins"], "medium"))
    return qs

# ================================ DSA ================================
REF_D1 = '''import heapq
from typing import List
from collections import defaultdict

def top_k_entities(events: List[List], k: int) -> List[str]:
    total = defaultdict(int)
    for name, weight in events:
        total[name] += weight
    best = heapq.nsmallest(k, total.items(), key=lambda kv: (-kv[1], kv[0]))
    return [name for name, _ in best]
'''
BR_D1 = '''def top_k_entities(events, k):
    total = {}
    for name, w in events:
        total[name] = total.get(name, 0) + w
    order = sorted(total, key=lambda n: (-total[n], n))
    return order[:k]
'''
def gen_d1(r):
    names = ["ab", "b", "a", "zed", "Q", "q", "m"]
    ev = [[r.choice(names), r.randrange(-3, 6)] for _ in range(r.randrange(1, 12))]
    return {"events": ev, "k": r.randrange(1, len({e[0] for e in ev}) + 1)}

REF_D2 = '''from typing import List
from collections import deque

def count_shortest_routes(n: int, edges: List[List[int]], src: int, dst: int, min_conf: int) -> List[int]:
    MOD = 10**9 + 7
    adj = [[] for _ in range(n)]
    for u, v, c in edges:
        if c >= min_conf:
            adj[u].append(v)
            adj[v].append(u)
    dist = [-1] * n
    ways = [0] * n
    dist[src], ways[src] = 0, 1
    q = deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            break
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                q.append(v)
            if dist[v] == dist[u] + 1:
                ways[v] = (ways[v] + ways[u]) % MOD
    return [dist[dst], ways[dst] % MOD] if dist[dst] != -1 else [-1, 0]
'''
BR_D2 = '''def count_shortest_routes(n, edges, src, dst, min_conf):
    MOD = 10**9 + 7
    cur = [0] * n; cur[src] = 1
    for L in range(0, n + 1):
        if cur[dst] > 0:
            return [L, cur[dst] % MOD]
        nxt = [0] * n
        for u, v, c in edges:
            if c >= min_conf:
                nxt[v] += cur[u]; nxt[u] += cur[v]
        cur = nxt
    return [-1, 0]
'''
def gen_d2(r):
    n = r.randrange(1, 8)
    edges = [[r.randrange(0, n), r.randrange(0, n), r.randrange(1, 6)] for _ in range(r.randrange(0, 12))]
    edges = [e for e in edges if e[0] != e[1]]
    return {"n": n, "edges": edges, "src": r.randrange(0, n), "dst": r.randrange(0, n), "min_conf": r.randrange(1, 5)}

def build_dsa():
    r = random.Random(303)
    names = [f"E{i:04d}" for i in range(5000)]
    ev = [[r.choice(names), r.randrange(1, 100)] for _ in range(50000)]
    ties = [["b", 5], ["a", 5], ["c", 5], ["d", 1]]
    d1 = [("Example 1", {"events": [["ACME", 3], ["BANK", 5], ["ACME", 4], ["CIRRUS", 7]], "k": 2}), ("Example 2: tie broken by name", {"events": ties, "k": 3}),
          ("k equals number of entities", {"events": [["x", 1], ["y", -2]], "k": 2}), ("Negative totals", {"events": [["x", -1], ["y", -2], ["z", -3]], "k": 1}),
          ("Case-sensitive names", {"events": [["a", 2], ["A", 2], ["b", 1]], "k": 2}), ("Single event", {"events": [["only", 9]], "k": 1}),
          ("50000 events / 5000 names / k=10", {"events": ev, "k": 10}), ("50000 events / k=2000", {"events": ev, "k": 2000}),
          ("All equal totals", {"events": [[n, 1] for n in names], "k": 7})]
    q1 = dsa_question("oa03-dsa-01", 200, "Top-K Most Influential Entities",
"""A news-analytics service receives a list of `[entity_name, weight]` events (a weight is an integer influence score and can be negative). The total influence of an entity is the sum of its weights.

Return the names of the **k entities with the largest total influence**, ordered from largest to smallest total. If two entities have the same total, the one whose name is **lexicographically smaller** (plain string comparison, case-sensitive) comes first.""",
        ["1 <= len(events) <= 2 * 10^5", "1 <= len(name) <= 20", "-10^6 <= weight <= 10^6", "1 <= k <= number of distinct entities"],
        [("ACME has total 7, CIRRUS 7, BANK 5: tie on 7 broken alphabetically", {"events": [["ACME", 3], ["BANK", 5], ["ACME", 4], ["CIRRUS", 7]], "k": 2}),
         ("All three tie on 5; names a, b, c come first alphabetically", {"events": ties, "k": 3})],
        "top_k_entities", "def top_k_entities(events: List[List], k: int) -> List[str]",
        "from typing import List\n\ndef top_k_entities(events: List[List], k: int) -> List[str]:\n    # TODO\n    pass\n",
        d1, REF_D1, BR_D1, gen_d1, "O(n + m log k) with a heap (m = distinct entities); sorting everything is O(n + m log m) and also acceptable",
        ["A solution that sorts raw events instead of aggregating first fails every multi-event test.", "Tie-breaking on names is tested separately."],
        "Aggregate totals in a hash map, then select the k best with a heap (heapq.nsmallest with key (-total, name)). The key encodes both the ordering and the tie-break.",
        ["heap", "hash map", "sorting"], "medium")
    # chain of diamonds: 0 -> {a,b} -> 1 ...
    def diamonds(k):
        edges = []; n = 1
        cur = 0
        for _ in range(k):
            a, b, nxt = n, n + 1, n + 2; n += 3
            edges += [[cur, a, 5], [cur, b, 5], [a, nxt, 5], [b, nxt, 5]]
            cur = nxt
        return n, edges, cur
    n_d, e_d, last = diamonds(5000)
    rnd_n = 30000
    rnd_e = [[r.randrange(rnd_n), r.randrange(rnd_n), r.randrange(1, 10)] for _ in range(60000)]
    rnd_e = [e for e in rnd_e if e[0] != e[1]]
    d2 = [("Example 1", {"n": 5, "edges": [[0, 1, 9], [0, 2, 9], [1, 3, 9], [2, 3, 9], [3, 4, 2]], "src": 0, "dst": 3, "min_conf": 5}),
          ("Example 2: weak link blocks route", {"n": 5, "edges": [[0, 1, 9], [0, 2, 9], [1, 3, 9], [2, 3, 9], [3, 4, 2]], "src": 0, "dst": 4, "min_conf": 5}),
          ("src == dst", {"n": 3, "edges": [], "src": 1, "dst": 1, "min_conf": 1}), ("Parallel edges count as distinct routes", {"n": 3, "edges": [[0, 1, 3], [0, 1, 3], [1, 2, 3], [1, 2, 4]], "src": 0, "dst": 2, "min_conf": 3}),
          ("Disconnected", {"n": 4, "edges": [[0, 1, 9], [2, 3, 9]], "src": 0, "dst": 3, "min_conf": 1}), ("Longer alternative ignored", {"n": 5, "edges": [[0, 1, 1], [1, 2, 1], [2, 4, 1], [0, 3, 1], [3, 4, 1]], "src": 0, "dst": 4, "min_conf": 1}),
          ("Diamond chain: 5000 diamonds (2^5000 routes mod p)", {"n": n_d, "edges": e_d, "src": 0, "dst": last, "min_conf": 5}),
          ("Random graph n=30000, m=60000", {"n": rnd_n, "edges": rnd_e, "src": 0, "dst": 29999, "min_conf": 3}), ("Random graph strict threshold", {"n": rnd_n, "edges": rnd_e, "src": 5, "dst": 17777, "min_conf": 1}),
          ("Self-contained triangle", {"n": 3, "edges": [[0, 1, 5], [1, 2, 5], [0, 2, 5]], "src": 0, "dst": 2, "min_conf": 5})]
    q2 = dsa_question("oa03-dsa-02", 250, "Reliable Relay Routes",
"""A knowledge graph links `n` entities (numbered `0..n-1`). Each undirected link `[u, v, conf]` has a confidence value. Only links with `conf >= min_conf` may be used.

Return `[hops, routes]` where `hops` is the minimum number of links needed to travel from `src` to `dst` and `routes` is the **number of distinct shortest routes** modulo `1_000_000_007`. A route is a sequence of links, so parallel links between the same pair of entities give distinct routes. If `dst` cannot be reached return `[-1, 0]`; if `src == dst` return `[0, 1]`.""",
        ["1 <= n <= 10^5", "0 <= len(edges) <= 2 * 10^5", "0 <= u, v < n, u != v; parallel links are allowed", "1 <= conf, min_conf <= 10^9"],
        [("Two shortest routes 0-1-3 and 0-2-3 (2 hops)", d2[0][1]), ("Link 3-4 has confidence 2 < 5, so node 4 is unreachable", d2[1][1])],
        "count_shortest_routes", "def count_shortest_routes(n: int, edges: List[List[int]], src: int, dst: int, min_conf: int) -> List[int]",
        "from typing import List\n\ndef count_shortest_routes(n: int, edges: List[List[int]], src: int, dst: int, min_conf: int) -> List[int]:\n    # TODO\n    pass\n",
        d2, REF_D2, BR_D2, gen_d2, "O(n + m) breadth-first search",
        ["DFS enumeration of all paths is exponential and fails the diamond-chain test.", "Forgetting the modulus overflows nothing in Python but is exercised by the diamond chain (huge counts)."],
        "BFS layers: when node v is first discovered at distance d+1 record it; every edge from a node at distance d to a node at distance d+1 adds ways[u] to ways[v]. Because BFS processes nodes in nondecreasing distance order, ways[u] is final when u is dequeued. Counting is done modulo 1e9+7.",
        ["graph", "BFS", "counting"], "hard")
    return [q1, q2]
