"""
FastAPI web interface for the Job Posting Analyzer.

Serves a single-page UI (static/index.html) and exposes a POST /analyse
endpoint that streams results via Server-Sent Events (SSE) as each of the
three specialist agents finishes — skills_matcher, culture_assessor, and
salary_estimator all run concurrently.

Run:
    uvicorn api:app --reload
"""

import asyncio
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

AGENTS = {
    "skills_matcher": _client.as_agent(
        name="skills_matcher",
        instructions=_instructions["skills_matcher"],
    ),
    "culture_assessor": _client.as_agent(
        name="culture_assessor",
        instructions=_instructions["culture_assessor"],
    ),
    "salary_estimator": _client.as_agent(
        name="salary_estimator",
        instructions=_instructions["salary_estimator"],
    ),
}


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

        # Queue collects results as each agent finishes
        queue: asyncio.Queue[dict] = asyncio.Queue()

        async def _run_one(name: str, agent) -> None:
            """Run a single-participant workflow and push the result to the queue."""
            try:
                workflow = ConcurrentBuilder(participants=[agent]).build()
                async for event in workflow.run(prompt, stream=True):
                    if event.type == "output":
                        for msg in cast(list[Message], event.data):
                            if msg.role == "assistant":
                                await queue.put({"type": "result", "agent": name, "content": msg.text})
                                return
                # Agent produced no output
                await queue.put({"type": "error", "agent": name, "message": "No response received."})
            except Exception as exc:
                await queue.put({"type": "error", "agent": name, "message": str(exc)})

        # Fire all three agents concurrently
        tasks = [
            asyncio.create_task(_run_one(name, agent))
            for name, agent in AGENTS.items()
        ]

        yield _event({"type": "start"})

        # Stream results to the client as each agent completes
        for _ in range(len(AGENTS)):
            result = await queue.get()
            yield _event(result)

        await asyncio.gather(*tasks)
        yield _event({"type": "done"})

    except Exception as exc:
        yield _event({"type": "fatal", "message": str(exc)})
