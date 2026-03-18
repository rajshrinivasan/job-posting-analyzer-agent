# Pattern 2: Concurrent — Job Posting Analyzer

## What it does
Broadcasts a job posting and candidate CV to three specialist agents
simultaneously. All agents run in parallel and produce independent analyses.

## Pipeline
```
job posting + CV (same prompt)
   ┌──────────────────────────────┐
   ↓              ↓               ↓
[skills_matcher] [culture_assessor] [salary_estimator]
   ↓              ↓               ↓
   └──────────────────────────────┘
         aggregated output
              ↓
      printed to console
```

## Key concept
Unlike sequential, agents here do not see each other's output. Each one
analyses the same input independently. The framework waits for all three to
finish, then bundles the results into a single aggregated response.

## Files
| File | Purpose |
|---|---|
| `job_posting_analyzer.py` | Main script |
| `job_posting_analyzer_instructions.txt` | Agent instructions (`[skills_matcher]`, `[culture_assessor]`, `[salary_estimator]`) |
| `agent_utils.py` | `load_instructions()` — parses the sectioned instructions file |

## Setup
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your key:
```
OPENAI_API_KEY="sk-..."
```

## Run
Pass the job posting (`.txt`) and candidate CV (`.docx`) as arguments:
```bash
python job_posting_analyzer.py path/to/job_posting.txt path/to/cv.docx
```

## Example inputs

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

## Example output
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
