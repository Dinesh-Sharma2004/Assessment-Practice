"""Isolated grader process:  python -I runner.py <bank.json> <qid> <public|full>   (candidate code on stdin).
Prints one JSON line.  Executed only by execution.py inside a temp directory with resource limits."""
import contextlib, io, json, resource, signal, sys, time

ROOT = sys.argv[4]
sys.path.insert(0, ROOT)
import oa_lib as L  # noqa: E402


class Timeout(BaseException):
    pass


def _alarm(signum, frame):
    raise Timeout()


def with_timeout(seconds, fn):
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return fn()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def main():
    bank_file, qid, mode = sys.argv[1:4]
    code = sys.stdin.read()
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (150, 150))
    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024**2, 10 * 1024**2))
    doc = json.load(open(bank_file, encoding="utf-8"))
    q = next(x for s in doc["sections"] for x in s["questions"] if x["id"] == qid)
    tests = q["publicTests"] + (q["hiddenTests"] if mode == "full" else [])
    out = []
    for t in tests:
        buf = io.StringIO()
        t0 = time.time()
        kind, msg = "ok", ""
        try:
            with contextlib.redirect_stdout(buf):
                if q["type"] == "sql":
                    ok, msg = with_timeout(8, lambda: L.grade_sql_test(q, t, code))
                elif q["type"] == "pandas":
                    def go():
                        res = L.run_pandas(code, q["functionName"], t["inputs"], t.get("params", {}))
                        return L.compare_df(res, t["expected"])
                    ok, msg = with_timeout(15, go)
                else:
                    got = L.run_dsa(code, q["functionName"], t["input"], q.get("timeLimitSecondsPerTest", 2) * 3)
                    ok, msg = L.values_equal(got, t["expected"]), f"returned {str(got)[:120]}"
            if not ok:
                kind = "error" if str(msg).startswith("error:") else "wrong"
        except (Timeout, L._Timeout):
            ok, kind, msg = False, "timeout", "time limit exceeded"
        except MemoryError:
            ok, kind, msg = False, "error", "MemoryError: memory limit exceeded"
        except BaseException as e:
            ok, kind, msg = False, "error", f"{type(e).__name__}: {e}"
        out.append({"id": t["id"], "visibility": t["visibility"], "weight": t["weight"], "passed": bool(ok), "kind": "ok" if ok else kind,
                    "message": str(msg)[:400], "stdout": buf.getvalue()[:1500], "seconds": round(time.time() - t0, 3)})
    print("\n@@RESULT@@" + json.dumps(out))


main()
