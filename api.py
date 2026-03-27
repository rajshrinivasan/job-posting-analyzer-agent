"""
FastAPI web interface for the Job Posting Analyzer.

Serves a single-page UI (static/index.html) and exposes a POST /analyse
endpoint that streams results via Server-Sent Events (SSE). All three agents
run concurrently inside a single ConcurrentBuilder workflow; the SSE generator
yields one result event per assistant message as they surface from the workflow.

Run:
    uvicorn api:app --reload
"""

import io
import json
import sys
from pathlib import Path
from typing import AsyncGenerator, cast

from docx import Document
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse

from agent_framework import Message
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework.openai import OpenAIResponsesClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_utils import load_instructions

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

app = FastAPI(title="Job Posting Analyzer")

# ── Shared client + agents (created once at startup) ─────────────────────────
_instructions = load_instructions(HERE / "job_posting_analyzer_instructions.txt")
_client = OpenAIResponsesClient(model_id="gpt-4o")

AGENTS = [
    _client.as_agent(name="skills_matcher",   instructions=_instructions["skills_matcher"]),
    _client.as_agent(name="culture_assessor", instructions=_instructions["culture_assessor"]),
    _client.as_agent(name="salary_estimator", instructions=_instructions["salary_estimator"]),
]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (HERE / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/analyse")
async def analyse(
    job_posting: str = Form(...),
    cv_file: UploadFile = File(...),
) -> StreamingResponse:
    cv_bytes = await cv_file.read()
    return StreamingResponse(
        _sse_stream(job_posting, cv_bytes),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if proxied
        },
    )


# ── SSE generator ─────────────────────────────────────────────────────────────

async def _sse_stream(
    job_posting: str, cv_bytes: bytes
) -> AsyncGenerator[str, None]:
    def _event(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    try:
        # Parse CV from uploaded bytes
        doc = Document(io.BytesIO(cv_bytes))
        candidate_cv = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        prompt = f"Job posting:\n{job_posting}\n\nCandidate CV:\n{candidate_cv}"

        # Run all three agents concurrently via a single ConcurrentBuilder workflow
        workflow = ConcurrentBuilder(participants=AGENTS).build()

        yield _event({"type": "start"})

        async for event in workflow.run(prompt, stream=True):
            if event.type == "output":
                for msg in cast(list[Message], event.data):
                    if msg.role == "assistant":
                        name = msg.author_name or "agent"
                        yield _event({"type": "result", "agent": name, "content": msg.text})

        yield _event({"type": "done"})

    except Exception as exc:
        yield _event({"type": "fatal", "message": str(exc)})
