"""Loads the existing question banks (assessment-0N.json) and builds candidate-safe views."""
import json
from functools import lru_cache

from .config import PROFILES, ROOT, SECTIONS

TOTAL_MARKS = {"mcq": 400, "apt": 240, "da": 300, "sql": 300, "pandas": 300, "dsa": 260}
COUNTS = {"mcq": 25, "apt": 15, "da": 12, "pandas": 5, "dsa": 2}      # SQL has 2 questions in OA1/OA2 and 3 afterwards


@lru_cache(maxsize=1)
def banks() -> dict:
    out = {}
    for p in sorted(ROOT.glob("assessment-0?.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        d["_file"] = str(p)
        out[d["assessmentId"]] = d
    return out


def get(aid: str) -> dict | None:
    return banks().get(aid)


def sections(doc):
    return {s["type"]: s for s in doc["sections"]}


def section_questions(doc, key):
    return sections(doc)[key]["questions"]


def find_question(doc, qid):
    for i, key in enumerate(SECTIONS):
        for q in section_questions(doc, key):
            if q["id"] == qid:
                return i, q
    return None, None


def durations(doc, profile="standard") -> dict:
    return doc["timing"][PROFILES[profile]]["sectionSeconds"]


def shape_problems(doc) -> list[str]:
    """Reports (never rewrites) differences between a bank and the documented layout."""
    bad = []
    secs = sections(doc)
    if list(secs) != SECTIONS:
        bad.append(f"{doc['assessmentId']}: sections {list(secs)}")
        return bad
    for k in SECTIONS:
        qs = secs[k]["questions"]
        if k in COUNTS and len(qs) != COUNTS[k]:
            bad.append(f"{doc['assessmentId']}: {k} has {len(qs)} questions, expected {COUNTS[k]}")
        if sum(q["marks"] for q in qs) != TOTAL_MARKS[k]:
            bad.append(f"{doc['assessmentId']}: {k} marks {sum(q['marks'] for q in qs)}, expected {TOTAL_MARKS[k]}")
    if doc["totalMarks"] != 1800:
        bad.append(f"{doc['assessmentId']}: totalMarks {doc['totalMarks']}")
    return bad


def difficulty_label(doc) -> str:
    return doc.get("level", "Mixed")


def public_question(q: dict) -> dict:
    """Whitelist of fields a candidate may see while the attempt is running (no solutions, no hidden tests, no rubric)."""
    base = {k: q[k] for k in ("id", "type", "tags", "difficulty", "marks", "statement", "hints", "walkthrough") if k in q}
    if q["type"] == "mcq":
        base.update(topic=q["topic"], kind=q["kind"], options=q["options"])
        if "charts" in q:
            base["charts"] = q["charts"]
        return base
    base["title"] = q["title"]
    if q["type"] == "sql":
        base.update(subtype=q["subtype"], tables=q["tables"], schemaSql=q["schemaSql"], sampleDataSql=q["sampleDataSql"],
                    starterQuery=q["starterQuery"], outputSpec=q["outputSpec"], checkQueries=q["checkQueries"], sampleTables=q["sampleTables"], tableCount=q["tableCount"],
                    publicTests=[{"id": t["id"], "description": t["description"]} for t in q["publicTests"]],
                    sampleExpected=q["publicTests"][0]["expected"])
    elif q["type"] == "pandas":
        base.update(functionName=q["functionName"], functionSignature=q["functionSignature"], starterCode=q["starterCode"],
                    inputs=q["inputs"], parameters=q["parameters"], outputSpec=q["outputSpec"], comparison=q["comparison"],
                    publicTests=[{"id": t["id"], "description": t["description"], "inputs": t["inputs"], "params": t["params"],
                                  "expected": t["expected"]} for t in q["publicTests"]])
    else:
        base.update(functionName=q["functionName"], functionSignature=q["functionSignature"], starterCode=q["starterCode"],
                    constraints=q["constraints"], examples=q["examples"], expectedComplexity=q["expectedComplexity"],
                    timeLimitSecondsPerTest=q["timeLimitSecondsPerTest"],
                    publicTests=[{"id": t["id"], "description": t["description"], "input": t["input"], "expected": t["expected"]}
                                 for t in q["publicTests"]])
    return base


def starter(q) -> str:
    return q.get("starterQuery") or q.get("starterCode") or ""
