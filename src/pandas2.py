import random
import numpy as np
import pandas as pd
from builder import pandas_question

NAN = float("nan")
TICK = ["AAPL", "MSFT", "NVDA", "JPM", "XOM"]


def tr(rows):
    return pd.DataFrame(rows, columns=["trade_id", "ticker", "side", "qty", "price"]).astype({"trade_id": "int64", "qty": "int64", "price": "float64"})


def rand_tr(seed, n=14, nan=False):
    r = random.Random(seed); rows = []
    for i in range(1, n + 1):
        rows.append((i, r.choice(TICK[:4]), r.choice(["BUY", "SELL"]), r.choice([10, 50, 100, 100, 200, 500]), round(r.uniform(20, 400), 2)))
    df = tr(rows)
    if nan:
        df["qty"] = df["qty"].astype("float64"); df["price"] = df["price"].astype("float64")
        for i in range(n):
            if r.random() < 0.2: df.loc[i, "price"] = NAN
            if r.random() < 0.15: df.loc[i, "qty"] = NAN
    return df


T1 = tr([(1, "AAPL", "BUY", 100, 180.5), (2, "MSFT", "SELL", 200, 410.0), (3, "AAPL", "BUY", 50, 181.0), (4, "NVDA", "BUY", 300, 875.25), (5, "MSFT", "BUY", 100, 409.5), (6, "AAPL", "SELL", 100, 179.9)])
T2 = tr([(10, "JPM", "BUY", 100, 195.0), (11, "JPM", "BUY", 500, 195.0), (12, "XOM", "BUY", 99, 110.0), (13, "XOM", "SELL", 1000, 111.0)])

# ------------------------------------------------------------------ OA1 easy
REF_E1 = '''import pandas as pd

def buy_blocks(trades):
    out = trades[(trades["side"] == "BUY") & (trades["qty"] >= 100)]
    out = out.sort_values(["price", "trade_id"], ascending=[False, True])
    return out[["trade_id", "ticker", "qty", "price"]].reset_index(drop=True)
'''
REF_E2 = '''import pandas as pd
import numpy as np

def add_notional(trades):
    out = trades.copy()
    out["notional"] = out["qty"] * out["price"]
    out["signed_qty"] = np.where(out["side"] == "BUY", out["qty"], -out["qty"])
    return out[["trade_id", "side", "qty", "price", "notional", "signed_qty"]]
'''
REF_E3 = '''import pandas as pd

def ticker_summary(trades):
    out = (trades.groupby("ticker", as_index=False)
                 .agg(n_trades=("trade_id", "count"), total_qty=("qty", "sum"), avg_price=("price", "mean")))
    return out.sort_values(["total_qty", "ticker"], ascending=[False, True]).reset_index(drop=True)
'''
REF_E4 = '''import pandas as pd

def fill_gaps(trades):
    out = trades.copy()
    out["price"] = out["price"].fillna(out.groupby("ticker")["price"].transform("mean"))
    out["qty"] = out["qty"].fillna(0).astype("int64")
    return out[["trade_id", "ticker", "side", "qty", "price"]]
'''
REF_E5 = '''import pandas as pd

def attach_names(trades, securities):
    out = trades.merge(securities, on="ticker", how="left")
    out["name"] = out["name"].fillna("UNKNOWN")
    out["sector"] = out["sector"].fillna("UNKNOWN")
    return out.sort_values("trade_id")[["trade_id", "ticker", "name", "sector", "qty"]].reset_index(drop=True)
'''
SEC = pd.DataFrame([("AAPL", "Apple Inc.", "Technology"), ("MSFT", "Microsoft Corp.", "Technology"), ("JPM", "JPMorgan Chase", "Financials"), ("XOM", "Exxon Mobil", "Energy")], columns=["ticker", "name", "sector"])

TRADE_COLS = [("trade_id", "int64", "Unique trade id"), ("ticker", "str", "Ticker symbol"), ("side", "str", "'BUY' or 'SELL'"), ("qty", "int64", "Shares"), ("price", "float64", "Execution price")]


def build_oa1():
    qs = []
    qs.append(pandas_question("e1", 60, "Large Buy Orders", """From a trades table keep only the **BUY** trades with `qty >= 100`.

Return the columns `trade_id, ticker, qty, price`, sorted by `price` from highest to lowest (ties: smaller `trade_id` first), with a fresh 0..n-1 index.""",
        "buy_blocks", "def buy_blocks(trades: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef buy_blocks(trades: pd.DataFrame) -> pd.DataFrame:\n    # TODO: filter, sort, select columns\n    return trades\n",
        {"trades": TRADE_COLS},
        [("Sample data from the statement", {"trades": T1}, {}), ("Second sample (qty exactly 100, equal prices)", {"trades": T2}, {}), ("No row qualifies (empty result)", {"trades": tr([(1, "AAPL", "SELL", 500, 10.0), (2, "AAPL", "BUY", 5, 10.0)])}, {}),
         ("Randomised", {"trades": rand_tr(1)}, {}), ("Randomised larger", {"trades": rand_tr(2, 40)}, {}), ("Randomised small", {"trades": rand_tr(3, 6)}, {})],
        REF_E1, "Columns [trade_id int64, ticker str, qty int64, price float64]; sorted by price DESC, trade_id ASC.",
        ["Both filter conditions are needed (side and quantity).", "Tie-break on trade_id is tested."],
        "Combine the two conditions with &, sort by price descending and trade_id ascending, then pick the columns and reset the index.",
        ["filtering", "sorting"], "easy"))
    qs.append(pandas_question("e2", 60, "Notional and Signed Quantity", """Add two new columns to the trades table **without loops**:

* `notional = qty * price`
* `signed_qty = qty` for BUY trades and `-qty` for SELL trades

Return the columns `trade_id, side, qty, price, notional, signed_qty` in the original row order.""",
        "add_notional", "def add_notional(trades: pd.DataFrame) -> pd.DataFrame",
        "import numpy as np\nimport pandas as pd\n\ndef add_notional(trades: pd.DataFrame) -> pd.DataFrame:\n    out = trades.copy()\n    # TODO\n    return out\n",
        {"trades": TRADE_COLS},
        [("Sample data from the statement", {"trades": T1}, {}), ("Second sample", {"trades": T2}, {}), ("Single SELL row", {"trades": tr([(7, "XOM", "SELL", 3, 2.5)])}, {}),
         ("Randomised", {"trades": rand_tr(4)}, {}), ("Randomised larger", {"trades": rand_tr(5, 35)}, {}), ("Empty table", {"trades": tr([])}, {})],
        REF_E2, "Columns [trade_id, side, qty, price, notional float64, signed_qty int64]; original row order.",
        ["Vectorised column arithmetic (no row loops).", "SELL rows get a negative signed quantity."],
        "Column arithmetic is vectorised: qty * price multiplies row by row. np.where(condition, a, b) chooses between two arrays element-wise, so BUY keeps qty and SELL gets -qty.",
        ["vectorised", "np.where"], "easy"))
    qs.append(pandas_question("e3", 60, "Summary per Ticker", """Summarise the trades per `ticker`.

Return one row per ticker with `ticker, n_trades` (number of trades), `total_qty` (sum of `qty`) and `avg_price` (mean `price`, not rounded).

Sort by `total_qty` descending, then `ticker` ascending, with a fresh index.""",
        "ticker_summary", "def ticker_summary(trades: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef ticker_summary(trades: pd.DataFrame) -> pd.DataFrame:\n    # TODO: groupby + agg + sort\n    return trades\n",
        {"trades": TRADE_COLS},
        [("Sample data from the statement", {"trades": T1}, {}), ("Second sample (equal totals)", {"trades": tr([(1, "B", "BUY", 100, 1.0), (2, "A", "BUY", 100, 3.0), (3, "C", "SELL", 5, 2.0)])}, {}), ("Single ticker", {"trades": tr([(1, "Z", "BUY", 1, 9.0), (2, "Z", "SELL", 2, 10.0)])}, {}),
         ("Randomised", {"trades": rand_tr(6)}, {}), ("Randomised larger", {"trades": rand_tr(7, 50)}, {}), ("Empty table", {"trades": tr([])}, {})],
        REF_E3, "Columns [ticker str, n_trades int64, total_qty int64, avg_price float64].",
        ["Named aggregation or equivalent.", "Sorting by two keys with different directions."],
        "groupby('ticker') with named aggregation (count, sum, mean) builds the summary; sort_values accepts a list of columns and a list of ascending flags.",
        ["groupby", "aggregation"], "easy"))
    qs.append(pandas_question("e4", 60, "Fill Missing Values", """Some rows have missing data. Clean the table:

* a missing `price` is replaced by the **mean price of the same ticker** (computed from that ticker's non-missing prices; if the ticker has no price at all it stays NaN);
* a missing `qty` is replaced by `0`, and `qty` becomes an integer column.

Return `trade_id, ticker, side, qty, price` in the original row order.""",
        "fill_gaps", "def fill_gaps(trades: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef fill_gaps(trades: pd.DataFrame) -> pd.DataFrame:\n    out = trades.copy()\n    # TODO\n    return out\n",
        {"trades": [("trade_id", "int64", "Unique trade id"), ("ticker", "str", "Ticker"), ("side", "str", "'BUY' or 'SELL'"), ("qty", "float64", "Shares; may be NaN"), ("price", "float64", "Price; may be NaN")]},
        [("Sample data from the statement", {"trades": pd.DataFrame([(1, "AAPL", "BUY", 100.0, 180.0), (2, "AAPL", "SELL", NAN, NAN), (3, "AAPL", "BUY", 50.0, 182.0), (4, "MSFT", "BUY", 10.0, NAN), (5, "MSFT", "SELL", 20.0, 400.0)], columns=["trade_id", "ticker", "side", "qty", "price"])}, {}),
         ("A ticker with no known price keeps NaN", {"trades": pd.DataFrame([(1, "ZZZ", "BUY", NAN, NAN), (2, "ZZZ", "BUY", 5.0, NAN), (3, "AAA", "SELL", 7.0, 9.0)], columns=["trade_id", "ticker", "side", "qty", "price"])}, {}),
         ("Nothing missing", {"trades": rand_tr(8, 6).astype({"qty": "float64"})}, {}), ("Randomised", {"trades": rand_tr(9, 20, nan=True)}, {}), ("Randomised larger", {"trades": rand_tr(10, 50, nan=True)}, {}), ("Randomised small", {"trades": rand_tr(11, 8, nan=True)}, {})],
        REF_E4, "Columns [trade_id int64, ticker str, side str, qty int64, price float64]; original row order.",
        ["The ticker-wise mean must come from groupby + transform (not the global mean).", "qty must be integer after filling."],
        "groupby('ticker')['price'].transform('mean') returns a Series aligned with the original rows holding each ticker's mean, which fillna can use directly. Fill qty with 0 and cast to int64.",
        ["missing values", "transform"], "easy"))
    qs.append(pandas_question("e5", 60, "Add Security Names", """Enrich trades with security information.

Left-join `securities` (unique `ticker`) onto `trades`. Trades whose ticker is not in `securities` must be kept and get `'UNKNOWN'` in both `name` and `sector`.

Return `trade_id, ticker, name, sector, qty` sorted by `trade_id`, with a fresh index.""",
        "attach_names", "def attach_names(trades: pd.DataFrame, securities: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef attach_names(trades: pd.DataFrame, securities: pd.DataFrame) -> pd.DataFrame:\n    # TODO: merge, fill, sort\n    return trades\n",
        {"trades": TRADE_COLS, "securities": [("ticker", "str", "Unique ticker"), ("name", "str", "Company name"), ("sector", "str", "Sector")]},
        [("Sample data from the statement", {"trades": T1, "securities": SEC}, {}), ("Unknown tickers present", {"trades": tr([(1, "ZZZ", "BUY", 5, 1.0), (2, "JPM", "BUY", 5, 1.0), (3, "QQQ", "SELL", 9, 3.0)]), "securities": SEC}, {}),
         ("Unsorted trade ids", {"trades": tr([(9, "XOM", "BUY", 1, 1.0), (2, "AAPL", "BUY", 1, 1.0), (5, "MSFT", "SELL", 1, 1.0)]), "securities": SEC}, {}), ("Randomised", {"trades": rand_tr(12, 15), "securities": SEC}, {}),
         ("Randomised larger", {"trades": rand_tr(13, 40), "securities": SEC.iloc[:2]}, {}), ("Empty trades", {"trades": tr([]), "securities": SEC}, {})],
        REF_E5, "Columns [trade_id int64, ticker str, name str, sector str, qty int64].",
        ["Left join (not inner) keeps unknown tickers.", "fillna must be applied to both new columns."],
        "merge(..., how='left') keeps every trade; unmatched rows get NaN in name/sector which fillna('UNKNOWN') replaces. Finally sort by trade_id and reset the index.",
        ["merge", "fillna"], "easy"))
    return qs


# ------------------------------------------------------------------ OA2 easy-medium
def tx(rows):
    return pd.DataFrame(rows, columns=["txn_id", "txn_time"]).astype({"txn_id": "int64"})


def rand_tx(seed, n=14):
    r = random.Random(seed); rows = []
    for i in range(1, n + 1):
        t = f"2025-0{r.randrange(1, 4)}-{r.randrange(1, 28):02d} {r.randrange(0, 24):02d}:{r.randrange(0, 60):02d}:00"
        if r.random() < 0.1: t = r.choice(["", "n/a", "2025-02-30 10:00:00"])
        rows.append((i, t))
    return tx(rows)


REF_M1 = '''import pandas as pd

def calendar_features(txns):
    df = txns.copy()
    df["txn_time"] = pd.to_datetime(df["txn_time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["txn_time"])
    df["date"] = df["txn_time"].dt.normalize()
    df["weekday"] = df["txn_time"].dt.day_name()
    df["is_weekend"] = df["txn_time"].dt.dayofweek >= 5
    df["month"] = df["txn_time"].dt.strftime("%Y-%m")
    df["hour"] = df["txn_time"].dt.hour.astype("int64")
    return df.sort_values(["txn_time", "txn_id"])[["txn_id", "txn_time", "date", "weekday", "is_weekend", "month", "hour"]].reset_index(drop=True)
'''


def acc(rows):
    return pd.DataFrame(rows, columns=["account_id", "updated_at", "balance"]).astype({"account_id": "int64", "balance": "float64"})


def rand_acc(seed, n=16):
    r = random.Random(seed)
    return acc([(r.randrange(1, 6), f"2025-03-0{r.randrange(1, 4)} {r.randrange(8, 12):02d}:{r.choice(['00', '30'])}:00", round(r.uniform(0, 1000), 2)) for _ in range(n)])


REF_M2 = '''import pandas as pd

def latest_per_account(rows):
    df = rows.copy()
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    df = df.sort_values("updated_at", kind="mergesort")           # stable: equal timestamps keep input order
    df = df.drop_duplicates("account_id", keep="last")
    return df.sort_values("account_id")[["account_id", "updated_at", "balance"]].reset_index(drop=True)
'''


def vol(rows):
    return pd.DataFrame(rows, columns=["symbol", "date", "volume"]).astype({"volume": "int64"})


def rand_vol(seed, n=18):
    r = random.Random(seed); rows = []
    for s in ("AA", "BB", "CC"):
        for d in range(1, 7):
            if r.random() < 0.85: rows.append((s, f"2025-04-{d:02d}", r.randrange(100, 1000, 10)))
    r.shuffle(rows)
    return vol(rows)


REF_M3 = '''import pandas as pd

def running_stats(daily):
    df = daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["symbol", "date"], kind="mergesort").reset_index(drop=True)
    g = df.groupby("symbol")["volume"]
    df["vol_ma3"] = g.transform(lambda s: s.rolling(3, min_periods=1).mean())
    df["cum_volume"] = g.cumsum()
    df["volume_rank"] = g.rank(method="min", ascending=False).astype("int64")
    return df[["symbol", "date", "volume", "vol_ma3", "cum_volume", "volume_rank"]]
'''


def build_oa2():
    qs = []
    t1 = tx([(3, "2025-03-08 10:15:00"), (1, "2025-03-07 23:59:59"), (2, "2025-03-09 00:00:00"), (4, "not a time"), (5, "2025-03-10 08:30:00")])
    qs.append(pandas_question("m1", 60, "Calendar Features from Timestamps", """Create calendar features from transaction timestamps.

1. Parse `txn_time` with format `%Y-%m-%d %H:%M:%S`; drop rows that cannot be parsed.
2. Add `date` (the timestamp at midnight, datetime), `weekday` (English day name such as `Saturday`), `is_weekend` (Saturday or Sunday), `month` (text like `2025-03`) and `hour` (0–23, int64).
3. Sort by `txn_time`, then `txn_id`; return `txn_id, txn_time, date, weekday, is_weekend, month, hour` with a fresh index.""",
        "calendar_features", "def calendar_features(txns: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef calendar_features(txns: pd.DataFrame) -> pd.DataFrame:\n    df = txns.copy()\n    # TODO\n    return df\n",
        {"txns": [("txn_id", "int64", "Unique id"), ("txn_time", "str", "Timestamp text, may be invalid")]},
        [("Sample data from the statement", {"txns": t1}, {}), ("Month boundary and midnight", {"txns": tx([(1, "2025-01-31 23:59:59"), (2, "2025-02-01 00:00:00"), (3, "2024-02-29 12:00:00")])}, {}), ("All invalid (empty result)", {"txns": tx([(1, ""), (2, "x")])}, {}),
         ("Randomised", {"txns": rand_tx(1)}, {}), ("Randomised larger", {"txns": rand_tx(2, 40)}, {}), ("Single row", {"txns": tx([(9, "2025-06-15 06:07:08")])}, {})],
        REF_M1, "Columns [txn_id int64, txn_time datetime64, date datetime64, weekday str, is_weekend bool, month str, hour int64].",
        ["Invalid timestamps must be dropped (errors='coerce' then dropna).", "Midnight timestamps belong to the new day."],
        "pd.to_datetime(..., errors='coerce') turns bad text into NaT; the .dt accessor then gives day_name(), dayofweek (5 and 6 are the weekend), normalize() for the date, and strftime('%Y-%m') for the month.",
        ["datetime", ".dt accessor"], "easy"))
    a1 = acc([(1, "2025-03-01 09:00:00", 100.0), (2, "2025-03-01 09:30:00", 50.0), (1, "2025-03-01 10:00:00", 120.0), (2, "2025-03-01 09:00:00", 40.0), (3, "2025-03-02 08:00:00", 5.0), (3, "2025-03-02 08:00:00", 7.0)])
    qs.append(pandas_question("m2", 60, "Latest Balance per Account", """Each account can appear several times with different `updated_at` timestamps. Keep only the **latest** row of each account.

If two rows of an account have exactly the same latest timestamp, keep the one that appears **later in the input**. Return `account_id, updated_at (datetime), balance` sorted by `account_id` with a fresh index.""",
        "latest_per_account", "def latest_per_account(rows: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef latest_per_account(rows: pd.DataFrame) -> pd.DataFrame:\n    df = rows.copy()\n    # TODO\n    return df\n",
        {"rows": [("account_id", "int64", "Account"), ("updated_at", "str", "Timestamp text"), ("balance", "float64", "Balance at that time")]},
        [("Sample data from the statement", {"rows": a1}, {}), ("One row per account", {"rows": acc([(5, "2025-03-01 09:00:00", 1.0), (4, "2025-03-01 09:00:00", 2.0)])}, {}), ("Empty input", {"rows": acc([])}, {}),
         ("Randomised", {"rows": rand_acc(3)}, {}), ("Randomised larger", {"rows": rand_acc(4, 60)}, {}), ("All timestamps equal", {"rows": acc([(1, "2025-03-01 09:00:00", 1.0), (1, "2025-03-01 09:00:00", 2.0), (1, "2025-03-01 09:00:00", 3.0)])}, {})],
        REF_M2, "Columns [account_id int64, updated_at datetime64, balance float64], sorted by account_id.",
        ["The tie rule needs a stable sort before drop_duplicates(keep='last').", "Timestamps must be parsed (string order is not enough if formats vary)."],
        "Parse the timestamps, sort them with a stable algorithm so equal timestamps keep their input order, then drop_duplicates('account_id', keep='last') leaves the final row of every account.",
        ["sorting", "drop_duplicates"], "easy"))
    d1 = vol([("AA", "2025-04-02", 300), ("AA", "2025-04-01", 100), ("AA", "2025-04-03", 200), ("AA", "2025-04-04", 600), ("BB", "2025-04-01", 50), ("BB", "2025-04-02", 50)])
    qs.append(pandas_question("m3", 60, "Running Volume Statistics", """For each `symbol` (rows may be unsorted), sort by `date` and add:

* `vol_ma3` – mean of the current and previous two `volume` values (fewer rows at the start: use what is available, i.e. `min_periods=1`);
* `cum_volume` – running (cumulative) sum of `volume`;
* `volume_rank` – rank of the day's volume within the symbol, `1` = highest, equal volumes share the lower rank number (`method='min'`), as int64.

Return `symbol, date (datetime), volume, vol_ma3, cum_volume, volume_rank` sorted by symbol then date, with a fresh index.""",
        "running_stats", "def running_stats(daily: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef running_stats(daily: pd.DataFrame) -> pd.DataFrame:\n    df = daily.copy()\n    # TODO\n    return df\n",
        {"daily": [("symbol", "str", "Ticker"), ("date", "str", "'YYYY-MM-DD'"), ("volume", "int64", "Shares traded")]},
        [("Sample data from the statement", {"daily": d1}, {}), ("Ties in volume share a rank", {"daily": vol([("Z", "2025-04-01", 10), ("Z", "2025-04-02", 10), ("Z", "2025-04-03", 5)])}, {}), ("Single row", {"daily": vol([("Q", "2025-04-09", 7)])}, {}),
         ("Randomised", {"daily": rand_vol(5)}, {}), ("Randomised larger", {"daily": rand_vol(6)}, {}), ("Empty", {"daily": vol([])}, {})],
        REF_M3, "Columns [symbol str, date datetime64, volume int64, vol_ma3 float64, cum_volume int64, volume_rank int64].",
        ["Sorting by date inside each symbol before rolling/cumsum.", "Rank method='min' for ties."],
        "Sort first, then use groupby on the symbol: transform with rolling(3, min_periods=1).mean(), cumsum() and rank(method='min', ascending=False) all stay aligned with the sorted rows.",
        ["groupby", "rolling", "rank"], "medium"))
    return qs


# ------------------------------------------------------------------ OA4 / OA5 new
def ev(rows):
    return pd.DataFrame(rows, columns=["user_id", "event_date"]).astype({"user_id": "int64"})


def rand_ev(seed, users=12, months=6):
    r = random.Random(seed); rows = []
    for u in range(1, users + 1):
        start = r.randrange(0, 3)
        for m in range(start, months):
            if r.random() < 0.6 or m == start:
                rows.append((u, f"2025-{m+1:02d}-{r.randrange(1, 28):02d}"))
                if r.random() < 0.3: rows.append((u, f"2025-{m+1:02d}-{r.randrange(1, 28):02d}"))
    r.shuffle(rows)
    return ev(rows)


REF_H1 = '''import pandas as pd

def cohort_retention(events):
    df = events.copy()
    df["event_date"] = pd.to_datetime(df["event_date"])
    df["ym"] = df["event_date"].dt.year * 12 + df["event_date"].dt.month
    first = df.groupby("user_id")["ym"].transform("min")
    df["idx"] = df["ym"] - first
    df["cohort"] = [f"{(v - 1) // 12:04d}-{(v - 1) % 12 + 1:02d}" for v in first]
    active = df.drop_duplicates(["user_id", "idx"])
    size = df.drop_duplicates("user_id").groupby("cohort")["user_id"].size().rename("cohort_size")
    counts = active[active["idx"] <= 3].groupby(["cohort", "idx"])["user_id"].size().unstack("idx").reindex(columns=[0, 1, 2, 3]).fillna(0)
    out = size.to_frame().join(counts)
    for m in range(4):
        out[f"m{m}"] = out[m] / out["cohort_size"]
    out = out[["cohort_size", "m0", "m1", "m2", "m3"]].reset_index().sort_values("cohort").reset_index(drop=True)
    out["cohort_size"] = out["cohort_size"].astype("int64")
    return out
'''


def qt(rows):
    return pd.DataFrame(rows, columns=["ticker", "ts", "mid"]).astype({"mid": "float64"})


def td(rows):
    return pd.DataFrame(rows, columns=["trade_id", "ticker", "ts", "side", "price"]).astype({"trade_id": "int64", "price": "float64"})


def rand_qt_td(seed, n_t=12):
    r = random.Random(seed); quotes, trades = [], []
    for tk in ("AAA", "BBB"):
        px = 100.0
        for k in range(0, 60, 5):
            px += r.uniform(-0.5, 0.5)
            if r.random() < 0.85: quotes.append((tk, f"2025-05-01 10:{k:02d}:00", round(px, 2)))
    for i in range(1, n_t + 1):
        trades.append((i, r.choice(["AAA", "BBB", "CCC"]), f"2025-05-01 10:{r.randrange(0, 60):02d}:{r.randrange(0, 60):02d}", r.choice(["BUY", "SELL"]), round(100 + r.uniform(-1, 1), 2)))
    r.shuffle(quotes); r.shuffle(trades)
    return qt(quotes), td(trades)


REF_H2 = '''import numpy as np
import pandas as pd

def attach_quotes(trades, quotes):
    t = trades.copy(); q = quotes.copy()
    t["ts"] = pd.to_datetime(t["ts"]).astype("datetime64[ns]"); q["ts"] = pd.to_datetime(q["ts"]).astype("datetime64[ns]")
    t = t.sort_values("ts", kind="mergesort"); q = q.sort_values("ts", kind="mergesort")
    q = q.rename(columns={"ts": "quote_ts"}); q["quote_ts_copy"] = q["quote_ts"]
    m = pd.merge_asof(t, q, left_on="ts", right_on="quote_ts", by="ticker", direction="backward", tolerance=pd.Timedelta("5min"), allow_exact_matches=True)
    m["quote_ts"] = m["quote_ts_copy"]
    m["slippage"] = np.where(m["side"] == "BUY", m["price"] - m["mid"], m["mid"] - m["price"])
    return m.sort_values("trade_id")[["trade_id", "ticker", "quote_ts", "mid", "slippage"]].reset_index(drop=True)
'''


def build_oa4_h1():
    e1 = ev([(1, "2025-01-05"), (1, "2025-02-10"), (1, "2025-02-11"), (2, "2025-01-20"), (3, "2025-01-31"), (3, "2025-04-02"), (4, "2025-02-03"), (4, "2025-03-01"), (4, "2025-05-06"), (5, "2025-02-28")])
    return pandas_question("h1", 60, "Cohort Retention Table", """Build a monthly **cohort retention** table from raw activity events.

1. Parse `event_date`. A user's **cohort** is the calendar month (text `YYYY-MM`) of their first event.
2. For each event compute `idx` = number of calendar months since the user's cohort month (the cohort month itself is `0`). Several events of one user in the same month count once.
3. For each cohort return `cohort_size` (number of users, int64) and `m0, m1, m2, m3` – the **fraction of the cohort's users who have at least one event** `0, 1, 2, 3` months after the cohort month (`m0` is always 1.0; months with no activity give `0.0`). Activity beyond month 3 is ignored.

Return `cohort, cohort_size, m0, m1, m2, m3` sorted by `cohort`, with a fresh index.""",
        "cohort_retention", "def cohort_retention(events: pd.DataFrame) -> pd.DataFrame",
        "import pandas as pd\n\ndef cohort_retention(events: pd.DataFrame) -> pd.DataFrame:\n    df = events.copy()\n    # TODO\n    return df\n",
        {"events": [("user_id", "int64", "User"), ("event_date", "str", "'YYYY-MM-DD'")]},
        [("Sample data from the statement", {"events": e1}, {}), ("Single user, activity only in month 0 and month 5", {"events": ev([(1, "2025-03-04"), (1, "2025-08-04")])}, {}), ("Year boundary", {"events": ev([(1, "2024-11-30"), (1, "2025-01-02"), (2, "2024-12-15"), (2, "2025-03-15"), (3, "2025-01-01")])}, {}),
         ("Randomised", {"events": rand_ev(1)}, {}), ("Randomised larger", {"events": rand_ev(2, 40, 8)}, {}), ("Randomised small", {"events": rand_ev(3, 5, 4)}, {})],
        REF_H1, "Columns [cohort str, cohort_size int64, m0 float64, m1 float64, m2 float64, m3 float64].",
        ["Month arithmetic across a year boundary (Dec -> Jan).", "Duplicate events in a month count once per user.", "Missing months give 0.0, not NaN."],
        "Convert each date to a month number (year*12+month), take the minimum per user as the cohort, subtract it to get the month index, de-duplicate (user, index) pairs, count users per (cohort, index) with unstack, and divide by the cohort size.",
        ["cohort analysis", "groupby", "unstack"], "hard")


def build_oa5_h2():
    q1 = qt([("AAA", "2025-05-01 10:00:00", 100.0), ("AAA", "2025-05-01 10:05:00", 100.4), ("BBB", "2025-05-01 10:00:00", 50.0)])
    t1 = td([(2, "AAA", "2025-05-01 10:04:59", "BUY", 100.5), (1, "AAA", "2025-05-01 10:05:00", "SELL", 100.1), (3, "BBB", "2025-05-01 10:06:00", "BUY", 50.2), (4, "BBB", "2025-05-01 10:05:00", "BUY", 50.2), (5, "CCC", "2025-05-01 10:05:00", "BUY", 9.0)])
    qa, ta = rand_qt_td(1); qb, tb = rand_qt_td(2, 30); qc, tc = rand_qt_td(3, 8)
    return pandas_question("h2", 60, "Match Trades to the Latest Quote", """For execution analysis attach to every trade the **most recent quote of the same ticker at or before the trade time**, but only if that quote is **at most 5 minutes old** (a quote exactly 5 minutes old is acceptable).

1. Parse both `ts` columns. Trades and quotes are not sorted.
2. For each trade find the latest quote with the same `ticker` and `quote_ts <= trade ts` within 5 minutes; if none exists, `quote_ts`, `mid` and `slippage` are missing.
3. `slippage = price - mid` for BUY trades and `mid - price` for SELL trades (positive = worse for the trader).

Return `trade_id, ticker, quote_ts (datetime, the matched quote's time), mid, slippage` sorted by `trade_id`, with a fresh index.""",
        "attach_quotes", "def attach_quotes(trades: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame",
        "import numpy as np\nimport pandas as pd\n\ndef attach_quotes(trades: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:\n    # hint: pd.merge_asof needs both frames sorted by their time keys\n    return trades\n",
        {"trades": [("trade_id", "int64", "Unique id"), ("ticker", "str", "Ticker"), ("ts", "str", "Trade time"), ("side", "str", "'BUY' or 'SELL'"), ("price", "float64", "Execution price")],
         "quotes": [("ticker", "str", "Ticker"), ("ts", "str", "Quote time"), ("mid", "float64", "Mid price")]},
        [("Sample data from the statement", {"trades": t1, "quotes": q1}, {}), ("Same data with quotes shuffled", {"trades": t1.iloc[::-1], "quotes": q1.iloc[::-1]}, {}), ("Quotes exist only for other tickers", {"trades": t1, "quotes": qt([("ZZZ", "2025-05-01 10:00:00", 1.0)])}, {}),
         ("Randomised", {"trades": ta, "quotes": qa}, {}), ("Randomised larger", {"trades": tb, "quotes": qb}, {}), ("Randomised small", {"trades": tc, "quotes": qc}, {})],
        REF_H2, "Columns [trade_id int64, ticker str, quote_ts datetime64, mid float64, slippage float64]; float tolerance rel 1e-6.",
        ["pd.merge_asof with by='ticker', direction='backward' and a tolerance of 5 minutes.", "An exact timestamp match is allowed; both inputs must be sorted by time."],
        "merge_asof joins each trade to the nearest earlier quote of the same ticker; tolerance=Timedelta('5min') removes stale quotes. Keep a copy of the quote timestamp because the right key column is dropped from the result. np.where chooses the BUY/SELL sign.",
        ["merge_asof", "time series join"], "hard")
