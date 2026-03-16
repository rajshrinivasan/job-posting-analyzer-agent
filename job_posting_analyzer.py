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

import asyncio
import sys
from pathlib import Path
from typing import cast
from dotenv import load_dotenv
from agent_framework import Message, WorkflowEvent
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework.openai import OpenAIResponsesClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_utils import load_instructions

HERE = Path(__file__).parent


async def main():
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
    job_posting = """
    Role: Mid-Level Data Engineer
    Company: FinTech startup, London (hybrid, 2 days in office)

    We are looking for a data engineer to join our growing platform team.
    You will design and maintain data pipelines, work closely with analysts,
    and help shape our cloud data architecture on Azure.

    Requirements:
    - 3+ years experience in data engineering
    - Strong Python skills
    - Experience with Azure Data Factory or similar ETL tools
    - SQL proficiency
    - Familiarity with REST APIs
    - Experience working in Agile teams

    Nice to have:
    - Kubernetes or containerisation experience
    - Terraform or infrastructure-as-code
    - CI/CD pipeline knowledge

    We offer a collaborative, fast-paced environment where you'll wear many hats.
    Flexible working hours. Competitive salary — we do not disclose a range upfront.
    """

    candidate_cv = """
    4 years experience as a Data Engineer at a mid-size consultancy.
    Skills: Python, SQL, Azure (Data Factory, Blob Storage, Synapse), REST APIs,
    Pandas, dbt, Git. Worked in Agile squads delivering BI and pipeline projects.
    No formal experience with Kubernetes, Terraform, or CI/CD tooling.
    Based in London.
    """

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
    asyncio.run(main())
