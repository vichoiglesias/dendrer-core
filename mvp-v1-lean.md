# Dendrer MVP v1 - Lean Approach

> **Philosophy**: Ship the thinnest vertical slice that delivers value. Validate with real users before building more.

## Core Value Proposition

Enable developers to:
1. Sign up and get an API key
2. Make inference calls to open-source LLMs via OpenAI-compatible API
3. Get billed based on usage

**That's it.** Everything else is deferred.

---

## 4-Week Build Plan

### Week 1: Foundation (Nov 2024)

**Goal**: Working backend + database + local dev environment

**Deliverables**:
- [x] Project structure (monorepo)
- [ ] FastAPI application skeleton
- [ ] PostgreSQL schema with Alembic migrations
- [ ] Docker Compose dev environment (postgres, redis, local model)
- [ ] Basic auth: API key generation + validation
- [ ] Health check endpoint

**Schema (Minimal)**:
```sql
users (id, email, hashed_password, created_at)
api_keys (id, user_id, key_hash, name, created_at, last_used_at)
models (id, name, provider, config, status, created_at)
inference_requests (id, user_id, model_id, tokens_used, latency_ms, created_at)
subscriptions (id, user_id, plan, stripe_subscription_id, status)
```

**API Endpoints**:
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT
- `POST /api-keys` - Generate API key
- `GET /health` - Health check

---

### Week 2: Inference Pipeline

**Goal**: End-to-end inference with ONE model working

**Deliverables**:
- [ ] vLLM integration (Llama 2 7B or Mistral 7B)
- [ ] OpenAI-compatible endpoint: `POST /v1/chat/completions`
- [ ] Token counting and metering
- [ ] Redis for request queuing (simple queue, no fancy job scheduler)
- [ ] Basic rate limiting (per API key)
- [ ] Deploy to cloud (GKE or EKS) - single GPU node

**Performance Target**:
- p95 latency: <2.5 seconds (relax the 1.8s target for MVP)
- Support 10 concurrent requests

**Cost Estimate (AWS with Spot Instances)**:
- 1x GPU node (g4dn.xlarge T4, spot): ~$114/month
- RDS PostgreSQL (db.t3.micro): ~$15/month
- ElastiCache Redis (cache.t3.micro): ~$12/month
- S3 + Data Transfer: ~$20/month
- **Total**: ~$161/month (aggressive savings with spot instances)
- **On-Demand Fallback**: ~$407/month if spot unavailable

---

### Week 3: Multi-tenancy & Billing

**Goal**: Multiple users can use the service and get charged

**Deliverables**:
- [ ] Tenant isolation (user_id filtering in all queries)
- [ ] Usage tracking: token consumption per user
- [ ] Stripe integration:
  - Create customer on signup
  - Subscribe to plan (Free, Pro $49)
  - Usage-based billing (track tokens, bill monthly)
- [ ] Quota enforcement:
  - Free tier: 10k tokens/month
  - Pro: 1M tokens/month
- [ ] Simple admin queries (SQL for now)

**Plans**:
```
Free:   10k tokens/month,  $0
Pro:    1M tokens/month,   $49
```

(Defer Business/Enterprise until we have 10 Pro customers)

---

### Week 4: Developer Experience & Beta

**Goal**: Make it easy for first users to onboard

**Deliverables**:
- [ ] Python SDK (simple wrapper around requests)
- [ ] Quickstart documentation
- [ ] Example code (chat completion, streaming)
- [ ] Load testing with k6 (validate 100 req/min sustained)
- [ ] Error handling and logging (structured logs to stdout)
- [ ] Basic dashboard (usage, remaining quota) - can be simple HTML + FastAPI templates

**Beta Launch**:
- Onboard 5-10 friendly users
- Get feedback
- Measure: signup rate, API usage, errors

---

## Technical Stack (Locked In)

| Component | Choice | Why |
|-----------|--------|-----|
| **Backend** | FastAPI (Python 3.11+) | Fast iteration, async, great ML ecosystem |
| **Database** | PostgreSQL 15 (Cloud SQL/RDS) | Managed, reliable, ACID |
| **Cache/Queue** | Redis 7 (Managed) | Simple, proven, low ops |
| **Inference** | vLLM | Best OSS inference engine |
| **Container Orchestration** | Kubernetes (EKS) | Industry standard, spot instance integration |
| **IaC** | Terraform | Declarative, widely used |
| **Observability** | Prometheus + Grafana (Helm) | Standard K8s stack |
| **Auth** | JWT + API Keys | Simple, secure |
| **Billing** | Stripe | De facto standard |
| **Cloud** | AWS | 70% cost savings with spot instances, better GPU availability |

---

## What's OUT of Scope for MVP

Deferred to v2+ (after validating product-market fit):

- ❌ Fine-tuning infrastructure
- ❌ Blue-green deployments
- ❌ Multi-region support
- ❌ Custom domains
- ❌ Advanced RBAC (teams, roles)
- ❌ Model versioning UI
- ❌ Node.js SDK
- ❌ SSO / OAuth providers
- ❌ Custom model uploads
- ❌ Embeddings endpoints
- ❌ Function calling
- ❌ Image generation

**Just inference. Just chat completions. That's the MVP.**

---

## Success Criteria (60 Days Post-Launch)

| Metric | Target | Stretch |
|--------|--------|---------|
| **Signups** | 50 | 100 |
| **Paying Customers** | 10 | 25 |
| **MRR** | $490 | $1,000+ |
| **API Uptime** | 99% | 99.5% |
| **p95 Latency** | <2.5s | <2s |
| **Churn** | <20% | <10% |

**Leading Indicators** (Week 1-2):
- 5+ GitHub stars (if open-sourcing)
- 10+ waitlist signups
- 3+ beta testers actively using API

---

## Architecture Diagram (Simplified)

```
┌─────────────┐
│   Client    │
│  (SDK/cURL) │
└──────┬──────┘
       │
       │ HTTPS
       ▼
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│   FastAPI Backend    │
│  - Auth/API Keys     │
│  - Usage Metering    │
│  - Stripe Webhooks   │
└────┬────────────┬────┘
     │            │
     ▼            ▼
┌─────────┐  ┌──────────┐
│ Postgres│  │  Redis   │
│   RDS   │  │ (Queue)  │
└─────────┘  └────┬─────┘
                  │
                  ▼
           ┌──────────────┐
           │ vLLM Worker  │
           │ (GPU Pod)    │
           └──────────────┘
```

**Deployment**:
- 1x EKS cluster (2-3 nodes: 1 GPU spot, 2 CPU on-demand)
- 1x RDS PostgreSQL instance (db.t3.micro)
- 1x ElastiCache Redis instance (cache.t3.micro)
- S3 for model artifacts
- Application Load Balancer with ACM SSL cert

**Estimated Monthly Cost**: $161 (spot) to $407 (on-demand)

---

## Development Phases

### Phase 0: Local Setup (Days 1-2)
```bash
# Project structure
dendrer-core/
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── models/    # SQLAlchemy models
│   │   ├── routes/    # API endpoints
│   │   ├── services/  # Business logic
│   │   └── config.py
│   ├── alembic/       # DB migrations
│   ├── tests/
│   └── requirements.txt
├── infra/             # Terraform
│   ├── modules/
│   └── envs/
├── sdk/               # Python client
│   └── dendrer/
├── docs/              # Documentation
├── docker-compose.yml
└── README.md
```

### Phase 1: Backend Core (Days 3-7)
- FastAPI app with CRUD for users, api_keys
- Alembic migrations
- Pytest test suite (>70% coverage)
- Docker compose with postgres + redis

### Phase 2: Inference (Days 8-14)
- vLLM container integration
- `/v1/chat/completions` endpoint
- Token counting (tiktoken or model-specific)
- Request/response logging

### Phase 3: Cloud Deploy (Days 15-21)
- Terraform for GKE cluster
- Deploy FastAPI + vLLM to K8s
- Set up Cloud SQL + Redis
- SSL cert + domain

### Phase 4: Billing & Polish (Days 22-28)
- Stripe integration
- Usage-based metering
- Python SDK
- Quickstart docs
- Load testing

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **GPU costs exceed budget** | High | Start with smallest GPU (T4), use spot instances, implement aggressive autoscaling |
| **vLLM reliability issues** | Medium | Have fallback to HuggingFace TGI, thorough testing |
| **Stripe integration complexity** | Low | Use Stripe test mode, follow official guides, start simple |
| **Slow model loading (cold starts)** | Medium | Keep 1 warm instance, pre-load model, consider model quantization |
| **Token metering inaccuracy** | High | Cross-validate with multiple methods, extensive testing, err on side of user |
| **No signups after launch** | High | Build waitlist pre-launch, engage ML/AI communities, offer generous free tier |

---

## Go-to-Market (Lightweight)

**Pre-launch** (During development):
- Create landing page (simple HTML + Tailwind)
- Start Twitter/X account, share build progress
- Post in r/MachineLearning, r/LocalLLaMA
- Email 10 friends in tech for early feedback

**Launch** (Week 4):
- Product Hunt launch
- Show HN post
- LinkedIn announcement
- Direct outreach to 20 potential users

**Post-launch**:
- Weekly updates on usage/learnings
- User interviews (5+ conversations)
- Iterate based on feedback

**No paid ads.** Organic only for MVP.

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-10-21 | Use FastAPI over NestJS | Python ML ecosystem, async support, rapid iteration |
| 2024-10-21 | AWS over GCP | 70% cost savings with spot instances ($114 vs $317/mo), better GPU availability |
| 2024-10-21 | Mistral 7B v0.3 over Llama | Apache 2.0 license (truly open), no commercial restrictions, good performance |
| 2024-10-21 | Defer fine-tuning | Validate inference demand first, reduce scope |
| 2024-10-21 | Use managed DB/Redis | Focus on core value, not ops (RDS, ElastiCache) |
| 2024-10-21 | Keep closed source for MVP | Validate business model before open sourcing |
| 2024-10-21 | Target indie devs & startups | Will pay $49/mo, need OpenAI alternatives, give good feedback |
| 2024-10-21 | Use dendrer.com domain | Already owned, professional .com TLD |

---

## Next Steps

**Right Now**:
1. [ ] Review and approve this MVP plan
2. [ ] Initialize project structure
3. [ ] Set up docker-compose dev environment
4. [ ] Start Week 1 tasks

**Tomorrow**:
- First FastAPI endpoint working
- Database migrations running
- Local model inference test

**This Week**:
- Complete Phase 0 + Phase 1

---

## Questions to Answer Before Building

- [x] Which cloud provider? **AWS** - Better spot instance pricing (70% off), more reliable GPU availability
- [x] Which model for MVP? **Mistral 7B v0.3** - Apache 2.0 license, fast, good quality
- [x] Open source the project? **No** - Keep closed during MVP validation, reconsider after PMF
- [x] Domain name? **dendrer.com** - Already owned
- [x] Target beta user persona? **Indie developers & small startups** - Building AI apps, will pay for convenience, need cost-effective alternatives to OpenAI API

---

## Resources

- **vLLM Docs**: https://docs.vllm.ai/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Stripe API**: https://stripe.com/docs/api
- **Terraform EKS**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_cluster
- **AWS Spot Instances**: https://aws.amazon.com/ec2/spot/
- **Mistral 7B**: https://huggingface.co/mistralai/Mistral-7B-v0.3

---

**Last Updated**: 2024-10-21
**Status**: Ready to build
**Estimated Completion**: 4 weeks from start
