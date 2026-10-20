"""Runs candidate code in a separate, resource-limited subprocess (never inside the web process)."""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from .config import ROOT

RUNNER = Path(__file__).with_name("runner.py")


class RuntimeFailure(Exception):
    """The sandbox itself failed (not the candidate's wrong answer). Must be shown, never counted as success."""


def execute(doc: dict, q: dict, code: str, mode: str, timeout: int = 120) -> list[dict]:
    work = tempfile.mkdtemp(prefix="oa-run-")
    try:
        proc = subprocess.Popen(
            [sys.executable, "-I", str(RUNNER), doc["_file"], q["id"], mode, str(ROOT)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work, text=True,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0", "HOME": work, "TMPDIR": work},
            start_new_session=True)
        try:
            out, err = proc.communicate(code, timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise RuntimeFailure(f"Execution exceeded the {timeout}s overall limit and was terminated.")
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)   # make sure no child outlives the run
            except ProcessLookupError:
                pass
        if "@@RESULT@@" not in out:
            raise RuntimeFailure("Runner crashed: " + (err.strip().splitlines() or ["no output"])[-1][:300])
        return json.loads(out.split("@@RESULT@@", 1)[1])
    finally:
        shutil.rmtree(work, ignore_errors=True)


def score(q: dict, tests: list[dict]) -> float:
    """Same formula as oa_lib.grade_question: marks * (sum of passed weights) / (sum of all weights)."""
    total = sum(t["weight"] for t in tests)
    got = sum(t["weight"] for t in tests if t["passed"])
    return round(q["marks"] * got / total, 2) if total else 0.0


def present(tests: list[dict], reveal_hidden_details: bool) -> list[dict]:
    """Candidate-safe view: hidden tests only expose pass/fail and the failure category."""
    out = []
    for t in tests:
        d = {"id": t["id"], "visibility": t["visibility"], "passed": t["passed"], "kind": t["kind"], "seconds": t["seconds"]}
        if t["visibility"] == "public" or reveal_hidden_details:
            d.update(message=t["message"], stdout=t["stdout"])
        out.append(d)
    return out
