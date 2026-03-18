"""
Concurrent Orchestration: Job Posting Analyzer
-----------------------------------------------
Broadcasts the same job posting (and candidate CV) to three specialist
agents simultaneously. All agents run in parallel and their results are
collected independently.

Agents:
  - skills_matcher   : compares the JD requirements against the candidate CV
  - culture_assessor : identifies green and red flags in the company culture
  - salary_estimator : infers a realistic salary band from role and location signals

Instructions are loaded from job_posting_analyzer_instructions.txt.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import cast
from dotenv import load_dotenv
from docx import Document
from agent_framework import Message
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework.openai import OpenAIResponsesClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_utils import load_instructions


def read_job_posting(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_candidate_cv(path: Path) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

HERE = Path(__file__).parent


async def main(job_posting_path: Path, candidate_cv_path: Path):
    load_dotenv(HERE / ".env")

    # ── Load agent instructions from file ───────────────────────────────────
    instructions = load_instructions(HERE / "job_posting_analyzer_instructions.txt")
    skills_matcher_instructions = instructions["skills_matcher"]
    culture_assessor_instructions = instructions["culture_assessor"]
    salary_estimator_instructions = instructions["salary_estimator"]

    # ── Client + agents ─────────────────────────────────────────────────────
    client = OpenAIResponsesClient(model_id="gpt-4o")

    skills_matcher = client.as_agent(
        name="skills_matcher",
        instructions=skills_matcher_instructions,
    )
    culture_assessor = client.as_agent(
        name="culture_assessor",
        instructions=culture_assessor_instructions,
    )
    salary_estimator = client.as_agent(
        name="salary_estimator",
        instructions=salary_estimator_instructions,
    )

    # ── Job posting + candidate CV ───────────────────────────────────────
    job_posting = read_job_posting(job_posting_path)
    candidate_cv = read_candidate_cv(candidate_cv_path)

    prompt = f"Job posting:\n{job_posting}\n\nCandidate CV:\n{candidate_cv}"

    # ── Build concurrent workflow ────────────────────────────────────────
    # All three agents receive the same prompt simultaneously.
    workflow = ConcurrentBuilder(
        participants=[skills_matcher, culture_assessor, salary_estimator]
    ).build()

    # ── Run and collect the final aggregated output ──────────────────────
    outputs: list[list[Message]] = []
    async for event in workflow.run(prompt, stream=True):
        if event.type == "output":
            outputs.append(cast(list[Message], event.data))

    # ── Display results ──────────────────────────────────────────────────
    if outputs:
        print("=" * 60)
        print("JOB POSTING ANALYSIS")
        print("=" * 60)
        for msg in outputs[-1]:
            if msg.role == "assistant":
                name = msg.author_name or "agent"
                print(f"\n[{name.upper()}]\n{msg.text}")
                print("-" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse a job posting against a candidate CV.")
    parser.add_argument("job_posting", type=Path, help="Path to the job posting .txt file")
    parser.add_argument("candidate_cv", type=Path, help="Path to the candidate CV .docx file")
    args = parser.parse_args()
    asyncio.run(main(args.job_posting, args.candidate_cv))
