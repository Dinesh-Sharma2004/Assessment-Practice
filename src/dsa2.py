import random
from builder import dsa_question

# -------------------------------------------------------------------- D-a: best pair under a budget (easy)
REF_A = '''from typing import List

def best_pair_under_budget(prices: List[int], budget: int) -> int:
    a = sorted(prices)
    lo, hi, best = 0, len(a) - 1, -1
    while lo < hi:
        s = a[lo] + a[hi]
        if s <= budget:
            best = max(best, s)
            lo += 1
        else:
            hi -= 1
    return best
'''
BR_A = '''def best_pair_under_budget(prices, budget):
    best = -1
    for i in range(len(prices)):
        for j in range(i + 1, len(prices)):
            if prices[i] + prices[j] <= budget:
                best = max(best, prices[i] + prices[j])
    return best
'''
def gen_a(r):
    return {"prices": [r.randrange(1, 30) for _ in range(r.randrange(0, 9))], "budget": r.randrange(1, 50)}

# -------------------------------------------------------------------- D-b: first unique character (easy)
REF_B = '''def first_unique_index(s: str) -> int:
    count = {}
    for ch in s:
        count[ch] = count.get(ch, 0) + 1
    for i, ch in enumerate(s):
        if count[ch] == 1:
            return i
    return -1
'''
BR_B = '''def first_unique_index(s):
    for i, ch in enumerate(s):
        if s.count(ch) == 1:
            return i
    return -1
'''
def gen_b(r):
    return {"s": "".join(r.choice("abcde") for _ in range(r.randrange(0, 10)))}

# -------------------------------------------------------------------- D-c: merge windows (easy-medium)
REF_C = '''from typing import List

def merge_windows(windows: List[List[int]]) -> List[List[int]]:
    merged = []
    for s, e in sorted(windows):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged
'''
BR_C = '''def merge_windows(windows):
    pts = set()
    for s, e in windows:
        for x in range(2 * s, 2 * e + 1):
            pts.add(x)
    out = []; x = min(pts) if pts else None
    for p in sorted(pts):
        if out and p == out[-1][1] + 1:
            out[-1][1] = p
        else:
            out.append([p, p])
    return [[a // 2, b // 2] for a, b in out]
'''
def gen_c(r):
    w = []
    for _ in range(r.randrange(0, 7)):
        s = r.randrange(0, 12); w.append([s, s + r.randrange(0, 5)])
    return {"windows": w}


def build():
    r = random.Random(808)
    big = [r.randrange(1, 10**6) for _ in range(100000)]
    qa = dsa_question("da", 100, "Best Pair Under Budget",
"""A portfolio manager wants to buy exactly **two different items** (two different positions in the list, even if their prices are equal) without spending more than `budget`.

Return the **largest total price** of any two items that does not exceed `budget`. If no pair fits, return `-1`.""",
        ["0 <= len(prices) <= 10^5", "1 <= prices[i] <= 10^6", "1 <= budget <= 2 * 10^6"], [("Pairs: 10+40=50, 10+25=35, 25+40=65 (too much), ... the best that fits is 50", {"prices": [10, 40, 25], "budget": 60}), ("Nothing fits", {"prices": [30, 40], "budget": 50})],
        "best_pair_under_budget", "def best_pair_under_budget(prices: List[int], budget: int) -> int",
        "from typing import List\n\ndef best_pair_under_budget(prices: List[int], budget: int) -> int:\n    # TODO\n    pass\n",
        [("Example 1", {"prices": [10, 40, 25], "budget": 60}), ("Example 2: nothing fits", {"prices": [30, 40], "budget": 50}), ("Empty list", {"prices": [], "budget": 10}), ("Single item", {"prices": [5], "budget": 10}),
         ("Equal prices form a valid pair", {"prices": [5, 5, 100], "budget": 10}), ("Exact budget", {"prices": [1, 2, 3, 4, 5], "budget": 9}), ("Large random n=100000", {"prices": big, "budget": 1_000_000}), ("Large, nothing fits", {"prices": [10**6] * 100000, "budget": 5})],
        REF_A, BR_A, gen_a, "O(n log n) time: sort once, then two pointers", ["Brute force over all pairs is O(n^2) and fails the n = 100000 test."],
        "Sort the prices. Put one pointer at the cheapest item and one at the most expensive. If their sum fits, record it and move the left pointer up (try a bigger partner); if it is too large, move the right pointer down. Each step discards one item, so the loop is linear after sorting.",
        ["arrays", "two pointers", "sorting"], "easy")
    qb = dsa_question("db", 160, "First Unique Symbol",
"""A stream of single-character event codes is given as a string `s`. Return the **index of the first character that appears exactly once** in `s`, or `-1` if every character repeats (or `s` is empty).""",
        ["0 <= len(s) <= 10^5", "s consists of lowercase English letters"], [("'a' repeats; 'b' is the first character that occurs once (index 1)", {"s": "aabbc" if False else "abacc"}), ("Every character repeats", {"s": "aabb"})],
        "first_unique_index", "def first_unique_index(s: str) -> int", "def first_unique_index(s: str) -> int:\n    # TODO\n    pass\n",
        [("Example 1", {"s": "abacc"}), ("Example 2", {"s": "aabb"}), ("Empty string", {"s": ""}), ("Single character", {"s": "z"}), ("Unique character at the end", {"s": "aabbccd"}), ("Unique character first", {"s": "xaabb"}),
         ("Long all-repeating", {"s": "ab" * 50000}), ("Long, unique at the very end", {"s": "ab" * 49999 + "abc"[2:] + "ab" * 0})],
        REF_B, BR_B, gen_b, "O(n) time using a frequency map", ["Calling s.count for each character is O(n^2) and times out on the long tests."],
        "Count every character once with a dictionary (or Counter). Then scan the string from the left and return the first index whose count is 1. Two linear passes give O(n).",
        ["strings", "hash map"], "easy")
    qc = dsa_question("dc", 100, "Merge Overlapping Maintenance Windows",
"""Maintenance windows are given as `[start, end]` pairs of integers (inclusive). Two windows that **overlap or touch** (the next start is `<=` the current end) must be merged into one.

Return the merged windows as a list of `[start, end]`, sorted by `start`. The input may be unsorted and may contain duplicates.""",
        ["0 <= len(windows) <= 10^5", "0 <= start <= end <= 10^9"], [("[1,3] and [2,6] overlap; [8,10] and [15,18] stand alone", {"windows": [[1, 3], [2, 6], [8, 10], [15, 18]]}), ("[1,4] and [4,5] touch at 4, so they merge", {"windows": [[4, 5], [1, 4]]})],
        "merge_windows", "def merge_windows(windows: List[List[int]]) -> List[List[int]]", "from typing import List\n\ndef merge_windows(windows: List[List[int]]) -> List[List[int]]:\n    # TODO\n    pass\n",
        [("Example 1", {"windows": [[1, 3], [2, 6], [8, 10], [15, 18]]}), ("Example 2: touching windows", {"windows": [[4, 5], [1, 4]]}), ("Empty", {"windows": []}), ("One window contains the others", {"windows": [[0, 100], [5, 6], [50, 60]]}),
         ("Adjacent but not touching", {"windows": [[1, 2], [3, 4]]}), ("Duplicates", {"windows": [[2, 2], [2, 2], [2, 3]]}), ("Large random", {"windows": [[(s := r.randrange(0, 10**6)), s + r.randrange(0, 50)] for _ in range(60000)]}),
         ("Large chain", {"windows": [[i * 2, i * 2 + 2] for i in range(50000)]})],
        REF_C, BR_C, gen_c, "O(n log n) time (sorting), O(n) space", ["Comparing every pair of windows is O(n^2) and times out."],
        "Sort the windows by start. Walk through them keeping the last merged window: if the next start is not beyond its end, extend that end (take the maximum); otherwise start a new merged window.",
        ["intervals", "sorting"], "easy")
    return qa, qb, qc
