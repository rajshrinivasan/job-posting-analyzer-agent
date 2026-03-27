# Job Posting Analyzer — Concurrent Multi-Agent System

A portfolio project demonstrating the **concurrent orchestration** pattern for multi-agent AI systems.

Three specialist agents analyse the same job posting simultaneously — no agent waits for another, and none sees the others' output. Results are collected and displayed together once all three finish.

```
         job posting + CV
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
[skills_  [culture_  [salary_
 matcher]  assessor]  estimator]
    │          │          │
    └──────────┼──────────┘
               ▼
      aggregated output
        (printed to console)
```

---

## Agents

| Agent | What it does |
|---|---|
| `skills_matcher` | Compares required/preferred skills from the JD against the candidate's CV. Reports matched skills, gaps, and a match verdict. |
| `culture_assessor` | Reads the job posting language for culture signals. Reports green flags, red flags, and an overall culture verdict. |
| `salary_estimator` | Infers a realistic salary band from role, seniority, skills, and location. Includes a negotiation note. |

---

## Tech stack

- **Python 3.10+**
- [`agent-framework-core`](https://pypi.org/project/agent-framework-core/) + [`agent-framework-orchestrations`](https://pypi.org/project/agent-framework-orchestrations/) — lightweight agent abstractions and the `ConcurrentBuilder` orchestration pattern
- **OpenAI `gpt-4o`** via `agent-framework-openai`
- `python-docx` — reads `.docx` CV files
- `python-dotenv` — loads the API key from `.env`

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone <repo-url>
cd job-posting-analyzer-agent
python -m venv venv
```

**2. Activate the virtual environment**

```bash
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your OpenAI API key**

Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
```

```
OPENAI_API_KEY="sk-..."
```

---

## Usage

```bash
python job_posting_analyzer.py <path/to/job_posting.txt> <path/to/cv.docx>
```

- `job_posting.txt` — plain text file containing the job description
- `cv.docx` — candidate CV as a Word document

---

## Example

**job_posting.txt**

```
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
```

**cv.docx** (content)

```
4 years experience as a Data Engineer at a mid-size consultancy.
Skills: Python, SQL, Azure (Data Factory, Blob Storage, Synapse), REST APIs,
Pandas, dbt, Git. Worked in Agile squads delivering BI and pipeline projects.
No formal experience with Kubernetes, Terraform, or CI/CD tooling.
Based in London.
```

**Output**

```
============================================================
JOB POSTING ANALYSIS
============================================================

[SKILLS_MATCHER]
Matched: Python, SQL, Azure Data Factory, Blob Storage, Synapse, REST APIs, Agile, dbt, Git
Gaps: Kubernetes, Terraform, CI/CD pipelines
Verdict: Partial Match — strong on the core data stack but missing all DevOps/IaC tooling.
------------------------------------------------------------

[CULTURE_ASSESSOR]
Green flags: Flexible working hours, hybrid arrangement (2 days), collaborative culture.
Red flags: "Wear many hats" (scope creep risk), no salary range disclosed, vague team size.
Verdict: Mixed — flexibility is genuine but the opacity around pay and role boundaries warrants probing.
------------------------------------------------------------

[SALARY_ESTIMATOR]
Estimated band: £55,000 – £70,000 per annum
Factors: Mid-level seniority, London location, Azure cloud skills premium, FinTech sector.
Negotiation note: Candidate has leverage on the core stack; Kubernetes/Terraform gap limits the ceiling.
------------------------------------------------------------
```

---

## Project structure

```
├── job_posting_analyzer.py              # Entry point — builds and runs the concurrent workflow
├── job_posting_analyzer_instructions.txt # Agent prompts, one [section] per agent
├── agent_utils.py                       # load_instructions() — parses the sectioned prompt file
├── requirements.txt
└── .env.example
```

---

## Key design notes

**Why concurrent?** Each agent's analysis is independent — skills matching doesn't need the culture assessment and vice versa. Running them in parallel cuts wall-clock time to roughly that of the slowest single agent rather than the sum of all three.

**Why separate instruction files?** Keeping agent prompts in `job_posting_analyzer_instructions.txt` (one `[section]` per agent) makes them easy to read, edit, and version without touching the orchestration code.

**Extending this:** Adding a fourth agent (e.g. a `growth_assessor` that evaluates career progression signals) is a single `client.as_agent(...)` call and a new `[section]` in the instructions file.
