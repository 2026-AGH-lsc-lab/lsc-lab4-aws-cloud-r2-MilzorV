# AWS Cloud Lab Report

Measurements were taken in **us-east-1** (AWS Academy). Load-test output is under `results/`; charts under `results/figures/`.

---

## Assignment 1: Deploy all environments

Four targets run the same k-NN workload (Lambda zip, Lambda container, Fargate + ALB, EC2 `t3.small`). Endpoint checks are saved in `assignment-1-endpoints.txt`.

For the fixed query in `loadtest/query.json`, all four endpoints returned the same top-5 neighbours:

| Rank | Index | Distance |
|------|-------|----------|
| 1 | 35859 | 12.001459121704102 |
| 2 | 24682 | 12.059946060180664 |
| 3 | 35397 | 12.487079620361328 |
| 4 | 20160 | 12.489519119262695 |
| 5 | 30454 | 12.499402046203613 |

---

## Assignment 2: Scenario A — cold start

**Method:** After at least 20 minutes without Lambda traffic, `oha` sent 30 sequential POSTs (1/s) per variant with SigV4 authentication (`scenario-a.sh`). CloudWatch `REPORT` lines were exported to `cloudwatch-zip-reports.txt` and `cloudwatch-container-reports.txt`. All requests returned HTTP **200**.

**Client (`oha`):** zip slowest **1655 ms**, p50 **229 ms**; container slowest **1674 ms**, p50 **224 ms** (`scenario-a-zip.txt`, `scenario-a-container.txt`).

**Server (first cold REPORT):**

| Variant | Init duration | Handler duration |
|---------|---------------|------------------|
| Zip | 615.32 ms | 77.11 ms |
| Container | 685.43 ms | 82.00 ms |

Warm invocations omit `Init Duration`; handler durations in the exports are mostly ~65–115 ms.

**Decomposition:** cold network RTT ≈ \(t_{\text{client}} - \text{Init} - \text{Duration}\); warm p50 ≈ \(t_{\text{p50}} - \text{Duration}\) (handler from REPORT ~75 ms for the warm bar).

**Zip vs container:** init is **lower for zip (615 ms) than container (685 ms)**, consistent with zip + layer vs container image startup.

**Figure:** `figures/latency-decomposition.png` (stacked bars: network vs init vs handler).

---

## Assignment 3: Scenario B — warm steady-state

**Method:** `scenario-b.sh` runs a warm-up phase, then 500 requests per configuration. Outputs: `scenario-b-*.txt`. All runs returned HTTP **200**.

**Client-side percentiles (ms)** from `oha`:

| Environment | Concurrency | p50 | p95 | p99 |
|-------------|-------------|-----|-----|-----|
| Lambda (zip) | 5 | 222.0 | 271.7 | 536.7 |
| Lambda (zip) | 10 | 221.4 | 253.8 | 546.6 |
| Lambda (container) | 5 | 220.9 | 329.4 | 605.0 |
| Lambda (container) | 10 | 218.3 | 283.2 | 601.3 |
| Fargate | 10 | 802.4 | 1063.2 | 1214.8 |
| Fargate | 50 | 3990.1 | 4295.9 | 4393.0 |
| EC2 | 10 | 324.3 | 455.8 | 1312.1 |
| EC2 | 50 | 927.0 | 1130.5 | 1899.5 |

**Server-side `query_time_ms`:** sampled from JSON for Fargate/EC2 (`curl`); for Lambda, CloudWatch `Duration` on `REPORT` lines (warm handlers roughly **~70–110 ms**). Client p50 (~**220 ms**) is higher because of TLS, Function URL, and RTT.

**Tail behaviour:** several rows have **p99 ≫ 2× p95** (e.g. Lambda zip at c5, Fargate at c50), indicating long tails and queueing.

**Lambda c5 vs c10:** p50 changes little because concurrent requests use **separate execution environments** (within the account limit).

**Fargate/EC2 c10 vs c50:** p50 rises sharply — **one task / one instance**; higher concurrency queues behind the same CPU.

**Client p50 vs `query_time_ms`:** the client timer includes **RTT + TLS + ALB** (Fargate) and **Function URL** overhead (Lambda).

---

## Assignment 4: Scenario C — burst from zero

**Method:** After idle long enough for Lambda to release execution environments, `scenario-c.sh` issued **200 requests** to all four targets concurrently: Lambda zip and container at **concurrency 10**; Fargate and EC2 at **concurrency 50**. Outputs: `scenario-c-lambda-zip.txt`, `scenario-c-lambda-container.txt`, `scenario-c-fargate.txt`, `scenario-c-ec2.txt`. All runs: HTTP **200** (200 responses each).

**Client percentiles (ms)** — values taken from `oha` (seconds converted to ms where needed):

| Target | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) |
|--------|----------|----------|----------|----------|
| Lambda (zip) | 224.4 | 1515.4 | 1574.7 | 1581.8 |
| Lambda (container) | 223.9 | 1293.3 | 1377.0 | 1397.1 |
| Fargate | 4000.7 | 4297.2 | 4506.3 | 4681.1 |
| EC2 | 864.3 | 1471.5 | 1860.7 | 1877.2 |

**Bimodal Lambda:** histograms show a dense band near **~220 ms** (warm) and a tail near **~1.3–1.6 s** (cold starts and/or new environments under burst). Both zip and container show this.

**Comparison:** Under this burst, Fargate’s median latencies are dominated by **queueing** on a single task at c=50 (p50 ≈ **4 s**). Lambda’s tail mixes **init and routing**; the warm band stays near **~220 ms**, but cold paths pull **p99** up.

**SLO (p99 \< 500 ms):** **not met** here — Lambda p99 ≈ **1.4–1.6 s**, EC2 ≈ **1.9 s**, Fargate ≈ **4.5 s**. Mitigations: **Lambda** — provisioned concurrency / concurrency limits; **Fargate/EC2** — more tasks or instances, auto-scaling.

**CloudWatch:** `Init Duration` lines in `/aws/lambda/lsc-knn-zip` and `/aws/lambda/lsc-knn-container` were reviewed for the burst interval (`REPORT` / `Init Duration` filters).

---

## Assignment 5: Cost at zero load

Dated pricing screenshots for Lambda, Fargate, and EC2 on-demand belong in `figures/pricing-screenshots/` (see course instructions).

**Idle behaviour:** **Lambda** bills **$0** with zero invocations. **Fargate** and **EC2** bill for **running capacity** even at RPS = 0 if the task/instance stays up.

**18 h vs 6 h split:** with no traffic, Lambda still has **no idle charge**. Fargate/EC2 accrue **full uptime cost** while resources stay provisioned (this lab keeps a single task/instance running).

---

## Assignment 6: Cost model, break-even, recommendation

### Traffic model (lab brief)

- Peak: **100 RPS** × **30 min/day**
- Normal: **5 RPS** × **5.5 h/day**
- Remaining time: **0 RPS**

**Requests per day:** \(100 \times 30 \times 60 + 5 \times 5.5 \times 3600 = 279\,000\).

**Requests per month (30 days):** \(279\,000 \times 30 = 8.37 \times 10^6\).

### Lambda (brief’s formula)

Memory **512 MB** (0.5 GB); handler duration **~0.075 s** from warm CloudWatch `Duration`.

\[
\text{GB-seconds/month} = N \times 0.075 \times 0.5
\]

\[
\text{Monthly} \approx N \cdot \frac{0.20}{10^6} + \text{GB-s} \cdot 0.0000166667
\]

For \(N = 8.37 \times 10^6\): request component **~\$1.67**, compute **~\$5.23**, total **~\$6.90** (list prices from the brief; align to current console pricing).

### Always-on (flat)

- **Fargate:** \((0.5 \times \text{vCPU\$} + 1 \times \text{GiB\$}) \times 720\) h/month (per-region table).
- **EC2 `t3.small`:** \(\text{hourly} \times 720\) h/month.

### Break-even (uniform average RPS, simplified)

Per-request cost \(k = 0.20/10^6 + 0.075 \times 0.5 \times 0.0000166667 \approx 8.25\times 10^{-7}\) USD/request. Monthly requests \(N = R \cdot 2\,592\,000\). Setting \(kN = C_{\text{fargate}}\) with \(C_{\text{fargate}} \approx \$17.8\)/month (illustrative Fargate 0.5 vCPU / 1 GiB) gives \(R \approx 8.3\) **average RPS** in this steady model; plug in **your** Fargate rate from pricing.

**Figure:** `figures/cost-vs-rps.png`.

### Recommendation

- **Scenario B:** Lambda zip p99 **~537–547 ms** at c5/c10 — **above 500 ms**; other targets are higher under single-replica setup.
- **Scenario C:** all measured **p99** values **exceed 500 ms**; Lambda shows **bimodal** latency after idle.
- **Cost:** at this traffic model, **Lambda** (~**\$6.9**/month with the above assumptions) is **below** typical **24/7** Fargate/EC2 for the same period; illustrative break-even vs Fargate is **~8 RPS** average in the simplified model.
- **Trade-off:** **Lambda** is attractive at **low average** load with **spiky** traffic, but **does not meet p99 \< 500 ms** in these runs without changes. **Fargate/EC2** need **scale-out**; **Lambda** benefits from **provisioned concurrency** and tuning.
- **When to revisit:** much **higher** sustained load (always-on wins on **$/request**), **relaxed** SLO, or **different** architecture (ASG, multiple tasks, reserved capacity).

---

Lab resources should be torn down when finished: `bash deploy/99-cleanup.sh`.
