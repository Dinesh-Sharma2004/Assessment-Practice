from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import bank, clock, db, engine
from .config import DIST, TEST_MODE


@asynccontextmanager
async def lifespan(app):
    db.init()
    for doc in bank.banks().values():
        for p in bank.shape_problems(doc):
            print("WARNING (bank mismatch, not modified):", p)
    yield


app = FastAPI(title="Mock OA Platform", lifespan=lifespan)


@app.exception_handler(engine.ApiError)
async def api_error(_: Request, e: engine.ApiError):
    return JSONResponse({"error": e.code, "message": e.message}, status_code=e.status)


class NewAttempt(BaseModel):
    assessmentId: str
    profile: str


class AnswerBody(BaseModel):
    value: str | None = None
    review: bool | None = None
    visited: bool | None = None
    clear: bool = False


class CodeBody(BaseModel):
    code: str


@app.get("/api/assessments")
def assessments():
    return engine.dashboard()


@app.post("/api/attempts")
def new_attempt(b: NewAttempt):
    return {"attemptId": engine.create_attempt(b.assessmentId, b.profile)}


@app.get("/api/attempts/{aid}")
def attempt(aid: str):
    return engine.state(aid)


@app.put("/api/attempts/{aid}/answers/{qid}")
def answer(aid: str, qid: str, b: AnswerBody):
    kw = {}
    if b.clear:
        kw["value"] = None
    elif "value" in b.model_fields_set:
        kw["value"] = b.value
    return engine.save_answer(aid, qid, review=b.review, visited=b.visited, **kw)


@app.post("/api/attempts/{aid}/questions/{qid}/run")
def run(aid: str, qid: str, b: CodeBody):
    return engine.run_public(aid, qid, b.code)


@app.post("/api/attempts/{aid}/questions/{qid}/submit")
def submit(aid: str, qid: str, b: CodeBody):
    return engine.submit(aid, qid, b.code)


@app.post("/api/attempts/{aid}/finish-section")
def finish_section(aid: str):
    return engine.finish_section(aid)


@app.get("/api/attempts/{aid}/results")
def results(aid: str):
    return engine.results(aid)


if TEST_MODE:
    class Adv(BaseModel):
        seconds: float = 0
        reset: bool = False

    @app.post("/api/test/clock")
    def fake_clock(b: Adv):
        clock.reset() if b.reset else clock.advance(b.seconds)
        return {"now": clock.now()}


if (DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/"):
            return JSONResponse({"error": "not_found"}, status_code=404)
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
