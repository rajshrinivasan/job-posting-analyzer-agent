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

## Run
```bash
# From the repo root
.venv\Scripts\activate
python 02_job_posting_analyzer/job_posting_analyzer.py
```

## To customise
Replace the `job_posting` and `candidate_cv` strings in the script with a
real posting and your own CV summary to get a personalised analysis.
