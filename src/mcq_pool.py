"""Builds the 25 conceptual MCQs for each OA from the legacy pool (+ new items) following the difficulty ladder."""
import importlib
from builder import MCQ

# quotas per OA per topic: (easy, medium, hard)
QUOTA = {
    "ML":   {1: (6, 1, 0), 2: (3, 4, 0), 3: (0, 6, 1), 4: (0, 3, 4), 5: (0, 1, 6)},
    "STAT": {1: (5, 1, 0), 2: (2, 4, 0), 3: (0, 5, 1), 4: (0, 3, 3), 5: (0, 1, 5)},
    "AI":   {1: (4, 1, 0), 2: (2, 3, 0), 3: (0, 5, 0), 4: (0, 2, 3), 5: (0, 1, 4)},
    "CS":   {1: (4, 0, 0), 2: (2, 2, 0), 3: (0, 4, 0), 4: (0, 2, 2), 5: (0, 0, 4)},
    "TEST": {1: (3, 0, 0), 2: (1, 2, 0), 3: (0, 3, 0), 4: (0, 1, 2), 5: (0, 0, 3)},
}
TOPIC_ORDER = ["ML", "STAT", "AI", "CS", "TEST"]
MAP = {"CS": "CS", "ML": "ML", "STAT": "STAT", "AI": "AI", "SQL": "CS", "JAVA": "CS", "OOP": "CS", "TEST": "TEST"}


def pool():
    out = []
    for n in range(1, 6):
        for m in importlib.import_module(f"oa{n}_mcq").M:
            if m.topic in MAP:
                m.topic = MAP[m.topic]
                out.append(m)
    from mcq_new import M as NEW
    return out + NEW


def _tokens(m):
    import re
    return set(re.findall(r"[a-z]{4,}", m.stmt.lower()))


def build_mcq(oa: int):
    """Quota selection with a non-overlap rule inside the OA: no shared concept tag (first two tags) and no near-duplicate wording."""
    p = pool()
    taken = globals().setdefault("_TAKEN", set())
    res, used_tags = [], set()
    for t in TOPIC_ORDER:
        for diff, k in zip(("easy", "medium", "hard"), QUOTA[t][oa]):
            got = 0
            for strict in (2, 1, 0):
                for m in p:
                    if got == k:
                        break
                    if m.topic != t or m.diff != diff or id(m) in taken:
                        continue
                    if strict and set(m.tags[:strict]) & used_tags:
                        continue
                    if any(len(_tokens(m) & _tokens(x)) / max(1, len(_tokens(m) | _tokens(x))) > 0.5 for x in res):
                        continue
                    taken.add(id(m)); res.append(m); used_tags |= set(m.tags[:2]); got += 1
            assert got == k, (oa, t, diff, got, k)
    assert len(res) == 25
    return res


if __name__ == "__main__":
    import collections
    for oa in range(1, 6):
        r = build_mcq(oa)
        print(oa, len(r), dict(collections.Counter(m.diff for m in r)), dict(collections.Counter(m.topic for m in r)))
