Scope

Dendrer MVP focused on:
	•	Multi-tenant inference endpoints for OSS LLMs.
	•	Managed fine-tuning jobs.
	•	Versioned model registry and blue-green deploys.
	•	Metering, billing, and strict cost controls.

Target SLOs:
	•	Inference p95 latency ≤ 1.8 s at target QPS.
	•	Control-plane availability ≥ 99.9%.
	•	Job scheduler success rate ≥ 99% over 24 h.
	•	Budget alarms before crossing 8.5k USD monthly burn.

⸻

High-level Architecture

Control Plane
	•	API Gateway: FastAPI (Python) or NestJS (TypeScript).
	•	Auth: API keys + JWT (HS256/RS256), per-tenant RBAC.
	•	Billing: Stripe subscriptions, metered usage for tokens and training hours.
	•	Model Registry: Postgres-backed metadata + immutable blobs in object storage.
	•	Scheduler: queue-based (NATS JetStream or Redis Streams) for training and deploy ops.
	•	Analytics and Metering: event bus -> ClickHouse for usage events and cost analytics.

Data Plane
	•	Inference Workers: containerized backends (vLLM/TGI/text-generation-inference or custom runners), k8s autoscaled.
	•	Fine-tune Workers: containerized trainers (LoRA/QLoRA), run on GPU node pools with per-job resource quotas.
	•	Artifact Storage: S3-compatible (MinIO or cloud S3), versioned buckets.
	•	Feature Flags: ConfigMap + LaunchDarkly or open-source equivalent.

Queues and Streams
	•	NATS JetStream (preferred) or Redis:
	•	topics: deploy.create, deploy.promote, train.start, train.cancel, usage.emit.

Networking
	•	Public: HTTPS via Cloudflare or ALB -> API Gateway.
	•	Private: k8s services for workers; NetworkPolicies to isolate namespaces.
	•	Egress controls and quotas per namespace to prevent surprise bills.

⸻

Infra (IaC-first)

Terraform project layout
infra/
  modules/
    vpc/
    eks/ or gke/
    node_groups/
    rds_postgres/
    s3/
    redis_or_nats/
    observability/ (prometheus-operator, loki, tempo, grafana)
    budgets/
  envs/
    prod/
    staging/
    
    
Kubernetes
	•	Cluster: EKS or GKE. Two node pools:
	•	gpu-pool: L4/A10/A100 depending on region and price. Taints: gpu=true:NoSchedule.
	•	cpu-pool: general workloads.
	•	Autoscaling:
	•	HPA for inference workers keyed on custom metric tokens_per_second.
	•	KEDA scaler for queue depth on train.start.
	•	Requests/limits:
	•	Inference pod: 1 GPU (or MIG), 6–16 GB RAM, CPU 2–4 vCPU.
	•	Training pod: 1–4 GPUs, RAM 32–128 GB, CPU 8–32 vCPU.

Budgets and Alarms
	•	Terraform AWS Budgets or GCP Billing Budgets:
	•	6k and 8.5k actual spend alerts (email + Slack webhook).
	•	Forecasted overspend alert at 90% of monthly target.
	•	Daily cost report job publishes to Slack 08:00 CET.

Storage
	•	Postgres 15 (RDS/Cloud SQL), pg_partman for time-partitioned usage tables.
	•	S3 buckets:
	•	models/ (immutable): <org>/<model>/<version>/weights.*
	•	artifacts/ (training outputs, logs)
	•	datasets/ (optional, encrypted, access-scoped)

Secrets
	•	External Secrets Operator pulling from AWS Secrets Manager / GCP Secret Manager.
	•	Key rotation runbook monthly.

⸻

Data Model (Postgres)

-- Tenancy
CREATE TABLE orgs (
  id UUID PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES orgs(id),
  email CITEXT UNIQUE NOT NULL,
  role TEXT CHECK (role IN ('owner','admin','dev','viewer')),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE api_keys (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES orgs(id),
  name TEXT NOT NULL,
  hashed_key TEXT NOT NULL,
  scopes TEXT[] NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  revoked_at TIMESTAMPTZ
);

-- Models and versions
CREATE TABLE models (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES orgs(id),
  slug TEXT NOT NULL,             -- e.g. "mistral-7b"
  kind TEXT CHECK (kind IN ('llm','embedding')),
  visibility TEXT CHECK (visibility IN ('public','private')) DEFAULT 'private',
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(org_id, slug)
);

CREATE TABLE model_versions (
  id UUID PRIMARY KEY,
  model_id UUID REFERENCES models(id),
  version TEXT NOT NULL,          -- semver or git sha
  storage_uri TEXT NOT NULL,      -- s3://models/...
  params JSONB,                   -- tokenizer, dtype, quantization, lora refs
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(model_id, version)
);

-- Deployments
CREATE TABLE deployments (
  id UUID PRIMARY KEY,
  model_version_id UUID REFERENCES model_versions(id),
  env TEXT CHECK (env IN ('staging','prod')) DEFAULT 'prod',
  status TEXT CHECK (status IN ('creating','ready','failed','decommissioned')),
  router_url TEXT,                -- public inference endpoint
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Fine-tuning jobs
CREATE TABLE fine_tunes (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES orgs(id),
  base_model_version UUID REFERENCES model_versions(id),
  status TEXT CHECK (status IN ('queued','running','succeeded','failed','canceled')) DEFAULT 'queued',
  dataset_uri TEXT NOT NULL,      -- s3://datasets/...
  config JSONB,                   -- lora rank, lr, epochs, max_steps
  output_model_version UUID REFERENCES model_versions(id),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Usage events (metering)
CREATE TABLE usage_events (
  id BIGSERIAL PRIMARY KEY,
  org_id UUID REFERENCES orgs(id),
  ts TIMESTAMPTZ NOT NULL,
  kind TEXT CHECK (kind IN ('inference','training_hour')),
  tokens INT,                     -- for inference
  hours NUMERIC(6,2),             -- for training
  model_version_id UUID,
  deployment_id UUID,
  request_id UUID,
  cost_usd NUMERIC(10,4)          -- filled by billing job
);

-- Audit log
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  org_id UUID,
  user_id UUID,
  ts TIMESTAMPTZ DEFAULT now(),
  action TEXT,
  target_type TEXT,
  target_id UUID,
  meta JSONB
);

Indexes:
	•	usage_events(org_id, ts) BRIN.
	•	model_versions(model_id, version) BTree.
	•	deployments(model_version_id, status).

⸻

API Surface (OpenAPI sketch)

POST /v1/auth/api-keys
GET /v1/models
POST /v1/models/{model_id}/versions
POST /v1/deployments
POST /v1/fine-tunes
GET /v1/fine-tunes/{id}
POST /v1/inference/{deployment_id}
GET /v1/usage
POST /v1/webhooks/stripe

Inference request

POST /v1/inference/{deployment_id}
{
  "input": "User prompt...",
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}

Inference response

{
  "id": "req_...uuid",
  "model_version": "mistral-7b@1.0.3",
  "usage": { "prompt_tokens": 123, "completion_tokens": 256, "total_tokens": 379 },
  "output": "text..."
}

Training request
POST /v1/fine-tunes
{
  "base_model_version": "uuid",
  "dataset_uri": "s3://datasets/orgX/my.jsonl",
  "config": { "method":"lora", "rank": 16, "lr": 1e-4, "epochs": 3 }
}

SDK and CLI

Node SDK
const dendrer = new Dendrer({ apiKey: process.env.DENDRER_KEY });

const out = await dendrer.inference.complete({
  deploymentId: "dep_uuid",
  input: "Hello",
  temperature: 0.3,
  maxTokens: 128
});
console.log(out.output);

Python SDK
from dendrer import Client
cli = Client(api_key=os.getenv("DENDRER_KEY"))
resp = cli.inference.complete(deployment_id="dep_uuid", input="Hello")
print(resp.output)

CLI
dendrer login
dendrer models ls
dendrer fine-tune start --base mistral-7b@1.0.0 --dataset s3://... --lora-rank 16
dendrer deploy create --model-version <uuid>
dendrer deploy promote --deployment <uuid> --env prod
dendrer logs tail --deployment <uuid>
  
Inference Stack Details
	•	Runner: vLLM with tensor parallel where applicable.
	•	Tokenizers cached on local NVMe; node-level cache daemonset.
	•	Quantization: bitsandbytes 4/8-bit optional; perf vs quality toggle per deploy.
	•	Router:
	•	Sticky routing by deployment_id.
	•	Backpressure when queue_len > QMAX returns 429 with Retry-After.
	•	Streaming: SSE or chunked JSON lines; rate-limit to 1 stream per API key by default.

Metrics to export
	•	inference_requests_total{deployment_id}
	•	tokens_generated_total{deployment_id}
	•	inference_latency_seconds{quantile=0.95}
	•	router_queue_depth
	•	gpu_utilization_percent
	•	gpu_memory_used_bytes

⸻

Training Stack Details
	•	Trainer images ship PyTorch + PEFT + deepspeed where needed.
	•	Checkpoint cadence every N steps to artifacts/.
	•	Hard runtime cap default 6 h; override with approval flag.
	•	Spot instances allowed with checkpoint resume; fall back to on-demand.

Metrics
	•	training_jobs_running
	•	training_job_duration_seconds
	•	training_restart_count
	•	Cost attribution: label pods with org_id, job_id, export to cost tool.

⸻

Observability

Metrics: Prometheus Operator.
Logs: Loki, JSON logs only; include org_id, request_id, deployment_id.
Tracing: OpenTelemetry SDK, Tempo backend.
Dashboards (Grafana):
	•	Inference Overview: QPS, p95, error rate, tokens/sec.
	•	Training Overview: jobs by status, avg duration, restarts.
	•	Cost: infra cost by label, tokens served per dollar, forecast.

Alerts (Alertmanager):
	•	p95 latency > 1.8 s for 10 min.
	•	5xx rate > 1% for 5 min.
	•	GPU util < 20% for 30 min during peak (inefficiency).
	•	Billing: forecasted spend > 8.5k.

⸻

Security
	•	OAuth for console; API keys for service usage. Keys hashed with argon2.
	•	JWT contains org_id, scopes, kid; rotate keys quarterly.
	•	Namespace per org (enterprise) or shared with per-request isolation guards (MVP).
	•	NetworkPolicies: deny-all then allowlist between control-plane and workers.
	•	S3 bucket policies scoped per org prefix.
	•	Audit log for all admin actions and model promotions.
	•	Datasets optional encryption with KMS; at-rest encryption everywhere.
	•	DDoS: WAF basic rules, rate limit per IP and per API key.

⸻

Billing and Metering
	•	Stripe products:
	•	Pro 49 USD monthly, Business 199 USD monthly.
	•	Usage add-ons:
	•	Inference: price per 1M tokens.
	•	Training: price per GPU-hour.
	•	usage_events aggregated hourly by worker to org_usage_hourly.
	•	Billing job (cron) calculates cost_usd and pushes to Stripe metered usage.
	•	Dunning emails configured. Webhook: invoice.paid, invoice.payment_failed.

⸻

Cost Controls
	•	Per-org hard limits:
	•	max_tokens_per_day, max_training_hours_per_day.
	•	429 with informative error and link to upgrade or request raise.
	•	Autoscaler min replicas drop to 0 off-peak for staging.
	•	Prevent idle GPUs: idle reaper watches gpu_utilization and scales to 0.

⸻

Tests and Load

Load test (k6)
	•	Target QPS: start 2 req/s, ramp to 20 req/s.
	•	Payload: 256 prompt tokens, 256 completion tokens.
	•	Pass if p95 ≤ 1.8 s and error rate < 1%.

Soak test
	•	4 h continuous with variable QPS; check memory leaks and GC pauses.

Training test
	•	Synthetic dataset fine-tune runs < 30 min, checkpoints and resumes at least once.

Security tests
	•	JWT tamper, key rotation, rate-limit bypass attempts, SSRF in dataset URIs.

⸻

Runbooks

RB-001: Inference 5xx spike
	1.	Check Grafana panel “Inference Errors”.
	2.	If router queue depth high, scale via HPA override; otherwise rollback latest deploy.
	3.	Capture 50 failing request logs with request_id.
	4.	Postmortem within 24 h.

RB-002: Cost overrun
	1.	Hit infra throttle script: set max_replicas=1 across inference.
	2.	Pause new training jobs by toggling allow_train=false.
	3.	Notify paying orgs with template; offer credit if user impact.

RB-003: Model rollback
	1.	deploy.promote --previous
	2.	Verify p95 and error rates normalize.
	3.	Annotate audit log and send internal alert.

RB-004: Secret leak
	1.	Rotate KMS keys and affected API keys.
	2.	Invalidate active sessions.
	3.	Notify impacted orgs with timeline and actions.

⸻

Delivery Milestones

Week 1
	•	Terraform baseline, k8s cluster, Postgres, NATS/Redis.
	•	API skeleton with auth and healthz.
	•	Model registry tables and S3 wiring.
	•	CLI login, models ls.

Week 2
	•	vLLM inference worker, first deploy, router, metrics.
	•	Stripe basic subscriptions, metering tables.
	•	HPA/KEDA, budget alarms live.

Week 3
	•	Fine-tune worker with LoRA, checkpointing and resume.
	•	Blue-green promotion flow and rollback runbook.
	•	k6 load + soak tests; SLO dashboards.

Week 4
	•	Usage billing cron to Stripe metered usage.
	•	Docs for SDKs, example apps.
	•	Security hardening and incident drills.

⸻

Config Reference (sample)
# config/app.yaml
env: prod
region: eu-central-1
token_limits:
  free_daily_tokens: 10000
  pro_daily_tokens: 1000000
training_limits:
  default_daily_gpu_hours: 6
autoscaling:
  inference:
    min: 0
    max: 20
    target_tokens_per_second: 300
billing:
  stripe_price_ids:
    pro: price_...
    business: price_...
observability:
  alerts:
    latency_p95_seconds: 1.8
    error_rate_percent: 1.0
    
ADRs to Decide Early
	•	NATS JetStream vs Redis Streams for at-least-once semantics.
	•	vLLM vs TGI for runners (token throughput vs features).
	•	Single-tenant vs multi-tenant namespaces at MVP.
	•	GPU class choice and MIG strategy.
	•	Cost exporter and label taxonomy for unit economics.

⸻

Minimum Docs To Ship
	•	Quickstart: deploy a public OSS model and hit it from curl, Node, Python.
	•	Fine-tune tutorial with JSONL, LoRA config, and promotion to prod.
	•	Billing and limits page with concrete examples and HTTP error mapping.
	•	Security and data handling policy (EU-first, opt-in training).
