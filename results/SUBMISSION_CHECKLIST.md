# Submission checklist (matches `docs/STUDENT_GUIDE.md` § Submission Format)

Use this list before you `git add` / push to **GitHub Classroom**.

## Required tree

```
results/
├── assignment-1-endpoints.txt
├── scenario-a-zip.txt
├── scenario-a-container.txt
├── scenario-b-*.txt
├── scenario-c-*.txt
├── cloudwatch-zip-reports.txt
├── cloudwatch-container-reports.txt
└── figures/
    ├── latency-decomposition.*
    ├── cost-vs-rps.*
    └── pricing-screenshots/
results/report.md
```

## Assignments 1–4 (lab measurements) — status

| File / pattern | Assignment | Present in repo |
|----------------|------------|-----------------|
| `assignment-1-endpoints.txt` | 1 | Yes |
| `scenario-a-zip.txt`, `scenario-a-container.txt` | 2 | Yes |
| `scenario-b-*.txt` (8 files: lambda zip/c5,c10, container c5,c10, fargate c10,c50, ec2 c10,c50) | 3 | Yes |
| `scenario-c-*.txt` (4 files) | 4 | Yes |
| `cloudwatch-zip-reports.txt`, `cloudwatch-container-reports.txt` | 2 (evidence) | Yes |
| `figures/latency-decomposition.png` | 2 | Yes (`figures/gen_latency_decomposition.py` regenerates it) |
| `figures/cost-vs-rps.png` | 6 | Yes (optional for “A1–4 only” hand-in; required for full course) |
| `figures/pricing-screenshots/` | 5 | Add **dated** PNGs from AWS pricing pages before final submission |
| `report.md` | All | Yes — keep within ~4 pages equivalent |

## Git notes

- **`loadtest/endpoints.sh`** is listed in `.gitignore` — do **not** commit it (URLs expire / are account-specific).
- Do **not** commit `.aws/` credentials or `*.pem`.

## Full course submission

Complete **Assignments 5–6** in `report.md`, add **pricing screenshots**, then run **`deploy/99-cleanup.sh`** after you have copied everything you need.
