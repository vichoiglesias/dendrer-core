# Dendrer

> Open-source LLM inference platform - democratizing access to large language models.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Dendrer is a Model-as-a-Service (MaaS) platform that provides:

- **Fast Deployment**: Multi-tenant inference endpoints for open-source LLMs
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API calls
- **Cost-Effective**: Leveraging AWS spot instances and open-source models
- **Developer-Friendly**: Simple API, comprehensive SDK, extensive documentation

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 with async SQLAlchemy
- **Cache/Queue**: Redis 7
- **Inference**: vLLM with Mistral 7B v0.3
- **Infrastructure**: Kubernetes (EKS), Terraform
- **Cloud**: AWS (spot instances for cost optimization)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/dendrer-core.git
   cd dendrer-core
   ```

2. **Set up environment variables**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your local settings
   ```

3. **Start services with Docker Compose**
   ```bash
   # From project root
   docker-compose up -d postgres redis
   ```

4. **Install Python dependencies**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   # Make sure you're in the backend directory
   alembic upgrade head
   ```

6. **Start the FastAPI server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Using Docker Compose (Full Stack)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

### Optional: pgAdmin (Database UI)

```bash
# Start pgAdmin
docker-compose --profile tools up -d pgadmin

# Access pgAdmin at http://localhost:5050
# Login: admin@dendrer.com / admin
```

## Project Structure

```
dendrer-core/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── config.py       # Configuration management
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test suite
│   ├── Dockerfile          # Backend container
│   └── requirements.txt    # Python dependencies
├── infra/                  # Terraform infrastructure
│   ├── modules/            # Reusable Terraform modules
│   └── envs/               # Environment configs
├── sdk/                    # Python SDK (future)
├── docs/                   # Documentation
├── docker-compose.yml      # Local development
├── mvp-v1-lean.md         # MVP specification
└── README.md              # This file
```

## Database Schema

### Core Tables

- **users**: User accounts and authentication
- **api_keys**: API key management
- **subscriptions**: Billing and plan management
- **models**: LLM model registry
- **inference_requests**: Usage tracking and billing

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Get JWT token

### API Keys
- `POST /api/v1/api-keys` - Generate API key
- `GET /api/v1/api-keys` - List API keys
- `DELETE /api/v1/api-keys/{id}` - Revoke API key

### Inference (OpenAI-compatible)
- `POST /v1/chat/completions` - Chat completion
- `POST /v1/completions` - Text completion (future)

### Admin
- `GET /api/v1/admin/stats` - Usage statistics
- `GET /api/v1/admin/users` - User management

## Development

### Creating Database Migrations

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Running Tests

```bash
cd backend
pytest

# With coverage
pytest --cov=app tests/

# Watch mode
pytest-watch
```

### Code Quality

```bash
# Format code
black app tests

# Lint code
ruff check app tests

# Type checking
mypy app
```

## Configuration

Key environment variables (see `backend/.env.example`):

```bash
# Application
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dendrer

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production

# Stripe (optional)
STRIPE_SECRET_KEY=sk_test_...

# Quotas
FREE_TIER_QUOTA=10000        # tokens/month
PRO_TIER_QUOTA=1000000       # tokens/month
```

## Deployment

See [mvp-v1-lean.md](./mvp-v1-lean.md) for detailed deployment instructions.

### AWS Infrastructure

```bash
cd infra/envs/prod

# Initialize Terraform
terraform init

# Plan changes
terraform plan

# Apply infrastructure
terraform apply
```

## Roadmap

### Phase 1: MVP (Weeks 1-4) ✅ In Progress
- [x] Project structure
- [x] FastAPI backend
- [x] Database models
- [x] Docker Compose setup
- [ ] Authentication & API keys
- [ ] Inference endpoints
- [ ] Stripe billing integration
- [ ] Python SDK
- [ ] Cloud deployment

### Phase 2: Beta (Weeks 5-8)
- [ ] Multiple model support
- [ ] Usage dashboard
- [ ] Rate limiting
- [ ] Monitoring & alerts
- [ ] Load testing
- [ ] Beta user onboarding

### Phase 3: Production (Weeks 9-12)
- [ ] Fine-tuning support
- [ ] Advanced RBAC
- [ ] Multi-region deployment
- [ ] SLA guarantees
- [ ] Enterprise features

## Contributing

We're not accepting external contributions yet as we validate the MVP. Check back soon!

## License

[MIT License](LICENSE)

## Support

- Documentation: [docs/](./docs/)
- Issues: GitHub Issues
- Email: support@dendrer.com

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [vLLM](https://docs.vllm.ai/)
- Using [Mistral 7B](https://huggingface.co/mistralai/Mistral-7B-v0.3)

---

**Status**: 🚧 MVP Development

**Version**: 0.1.0

**Last Updated**: 2024-10-21
