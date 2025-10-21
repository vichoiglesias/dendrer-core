roject

Dendrer MVP: conservative growth, pricing, infra, and first paying users.

Context

Dendrer is a Model-as-a-Service platform focused on fast deployment, fine-tuning, and EU-friendly privacy. Goal: reach sustainable revenue while keeping infra under control.

Objectives
	1.	Ship a usable MVP with stable deploys and a simple paywall.
	2.	Prove demand with real users and measured willingness to pay.
	3.	Reach a credible path to break-even with conservative assumptions.

Success Criteria
	•	50 signups, 10 paying customers, 1 design partner within 60 days.
	•	p95 latency under 1.8 s for standard inference payloads.
	•	Monthly infra under 9k USD with autoscaling on.
	•	Churn under 10 percent monthly for Pro tier.

Deliverables
	•	Finance model spreadsheet (12 months, base and range scenarios).
	•	Pricing page and checkout live.
	•	Autoscaling GPU infra with cost caps and alerts.
	•	Analytics dashboards for funnel and unit economics.
	•	One public case study and one technical blog post.

Guardrails and Constraints
	•	Privacy first. No customer data is used for training without explicit opt-in.
	•	Prefer EU regions for hosting when customers are in EU.
	•	Keep burn predictable. Hard cost cap alarm at 8.5k USD per month.
	•	Avoid vendor lock-in where possible. Abstract providers via a simple interface.
	•	In proposals or quotes, show values without VAT, with VAT added separately.

⸻

Operating Assumptions (initial, update as we learn)
	•	Conversion free to paid 10 percent to 20 percent.
	•	Tier mix: Pro 70 percent, Business 25 percent, Enterprise 5 percent.
	•	Average Enterprise logo value 800 to 1,500 USD per month to start.
	•	Salary for founder operator 10k USD per month.
	•	Infra 8k to 10k USD per month at launch scale.

⸻

Team of Agents

1) FinanceAgent
	•	Output: finance_model.xlsx, pricing_recommendation.md
	•	Tasks:
	•	Build month-by-month model with inputs:
	•	users_acquired, free_to_paid_rate, tier_mix, ARPU by tier
	•	gpu_hours, avg cost per gpu_hour, egress per GB, storage per TB, fixed SaaS
	•	salary, contingency 10 percent
	•	Produce Base, Conservative, Stretch scenarios.
	•	Compute CAC payback at CAC bands 0, 200, 400 USD.
	•	Alerts: warn if runway under 9 months.
	•	Acceptance:
	•	Single sheet with input cells colored, three scenario tabs, clean charts.

2) InfraAgent
	•	Output: infra_plan.md, tf/ or pulumi/ stack, runbooks/
	•	Tasks:
	•	Choose cloud and region set with spot-to-on-demand fallback.
	•	Define instance classes for training vs inference.
	•	Implement autoscaling based on queue depth and token-per-second.
	•	Set hard cost guards: budget alerts, daily spend webhook, GPU cap.
	•	Observability: logs, metrics, traces. p95 latency SLO and error budget.
	•	Blue-green deploy for model endpoints. One-click rollback.
	•	Acceptance:
	•	Load test shows p95 < 1.8 s at target QPS, cost guard alarms verified.

3) ProductAgent
	•	Output: pricing_page.mdx, onboarding_flows.md, paywall_flow.json
	•	Tasks:
	•	Pricing and plan limits (tokens, jobs, seats). Clear free tier boundary.
	•	Checkout via Stripe. Dunning emails enabled.
	•	In-product “Deploy in one command” quickstart and copy-paste SDK snippets.
	•	Track key events: signup, first inference, first fine-tune, paywall view, checkout start, checkout success.
	•	Acceptance:
	•	Median time to first successful inference under 10 minutes from signup.

4) GrowthAgent
	•	Output: gtm_experiments.md, content_calendar.md
	•	Tasks:
	•	3 channels to test: GitHub templates, “How we fine-tuned X” posts, targeted outreach to agencies handling privacy-sensitive use cases.
	•	Define 6 two-week experiments with hypotheses and success metrics.
	•	Build a short case study with one pilot customer.
	•	Acceptance:
	•	At least 2 experiments hit minimum effect size on signups or activations.

5) DXAgent (Developer Experience)
	•	Output: docs site skeleton, examples/, CLI polish
	•	Tasks:
	•	Ship “hello-dendrer” example in Node and Python.
	•	CLI: clear errors, progress bars, deploy logs, copyable curl examples.
	•	Templates for common tasks: FAQ bot, RAG starter, fine-tune from JSONL.
	•	Acceptance:
	•	External dev completes quickstart without guidance in under 15 minutes.

⸻

Milestones and Timeline (Day 0 is today)
	•	Week 1: Finance model v1, infra decision, pricing draft, event schema, CLI quickstart.
	•	Week 2: Autoscaling MVP, checkout live, analytics piped, first content piece.
	•	Week 3: Load test, blue-green deploys, pilot customer onboarded.
	•	Week 4: Post-mortems, case study v1, revise pricing and infra based on data.

⸻

Architecture Sketch
	•	Control plane: API, auth, billing, model registry, job scheduler.
	•	Data plane: inference workers, fine-tune workers, queue, object storage.
	•	Observability: metrics (Prometheus-compatible), tracing, structured logs.
	•	Safety: per-tenant encryption at rest, network policies, secrets manager.

⸻

Pricing v1 (subject to A/B)
	•	Free: 10k tokens per month, 1 fine-tune job, community support.
	•	Pro 49 USD per month: 1M tokens, 3 fine-tune jobs, versioning, rollback.
	•	Business 199 USD per month: 5M tokens, team roles, priority GPUs, analytics.
	•	Enterprise custom: SSO, on-prem or dedicated VPC, SLA, support.

K-factor: move limits not by model names but by token and job quotas to simplify the cost curve.

⸻

Cost Controls
	•	Budget alerts at 6k, 8.5k, 10k USD monthly.
	•	Daily spend Slack webhook 08:00 CET with 7-day trend.
	•	GPU scaler minimums during off-hours.
	•	Block long-running fine-tunes by default over N hours without override.

⸻

Analytics and KPIs
	•	Activation: first successful inference, first fine-tune.
	•	Time to first value: signup to first inference.
	•	Conversion: paywall view to checkout start to paid success.
	•	LTV, Gross Margin, ARPU by tier.
	•	Infra unit cost: USD per 1M tokens served, per fine-tune hour.

Event names
	•	user_signed_up, project_created, cli_install, first_inference_ok, fine_tune_started, fine_tune_completed, paywall_view, checkout_started, checkout_success, cancel_requested.

⸻

Runbooks (create under runbooks/)
	•	Incident 500s on inference: steps, rollback, on-call.
	•	Cost overrun: immediate cap, customer comms template.
	•	Model rollback: registry pointer switch, blast radius, verification.
	•	Security incident: isolation, key rotation, audit log export.

⸻

Risk Log (start a risks.md)
	•	GPU supply or price spikes. Mitigation: multi-cloud, L4/RTX fallbacks.
	•	Latency regression under load. Mitigation: autoscaler tuned to queue depth.
	•	Unexpected egress bills. Mitigation: caching, spec limits, alerts.
	•	Slow conversion. Mitigation: better onboarding, templates, targeted outreach.

⸻

Decision Log (start a decisions.md)

Keep ADR-style notes for infra choices, pricing changes, SDK design, auth model.

⸻

Prompts for Sub-Agents

FinanceAgent Prompt
You are FinanceAgent. Build a 12-month model for Dendrer with three scenarios. Inputs are clearly labeled cells. Output charts for revenue, infra, salary, and net. Include a sensitivity table for conversion and tier mix.

InfraAgent Prompt
You are InfraAgent. Design and provision an autoscaling GPU stack with budget alarms. Produce Terraform or Pulumi code and a load test plan. Deliver a runbook for rollbacks and cost incidents.

ProductAgent Prompt
You are ProductAgent. Ship a clear pricing page and checkout. Instrument the funnel events listed in agent.md. Ensure time to first inference is under 10 minutes with your onboarding flow.

GrowthAgent Prompt
You are GrowthAgent. Define 6 two-week GTM experiments. For each, specify channel, hypothesis, steps, tracking, and kill or scale criteria.

DXAgent Prompt
You are DXAgent. Ship hello-world examples in Node and Python plus a minimal docs site. Ensure the CLI error messages and progress UX are excellent.

⸻

Daily Execution Checklist
	•	Review spend dashboard and error budget.
	•	Review activation funnel numbers.
	•	Triage top 3 user complaints or friction points.
	•	Ship at least one improvement or piece of content per day.

Weekly Cadence
	•	Monday: plan, set experiment goals and infra targets.
	•	Wednesday: midpoint review, unblockers.
	•	Friday: metrics review, write one public update or thread.

⸻

Communication
	•	Single owner: Vicente. Decisions are documented in decisions.md.
	•	Public updates: monthly recap with metrics and a short roadmap.
	•	Customer comms: no surprises. Notify before breaking changes.

⸻
