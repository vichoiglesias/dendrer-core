# Testing the Dendrer API

Quick guide to test the complete authentication and inference flow.

## Prerequisites

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed default model
python scripts/seed_models.py

# Start the API server
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Test Flow

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### 2. Login to Get JWT Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Save the `access_token` from the response.

### 3. Create an API Key

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -d '{
    "name": "My First API Key"
  }'
```

**IMPORTANT**: Save the `key` field from the response. It's shown only once!

### 4. Make an Inference Request

**Note**: This will fail unless you have vLLM running. See "Running vLLM Locally" below.

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -d '{
    "model": "mistral-7b-instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello! Tell me a joke."}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### 5. Check Usage Stats

```bash
curl -X GET "http://localhost:8000/v1/usage" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE"
```

## Running vLLM Locally (Optional)

For local testing with a small model:

```bash
# Install vLLM
pip install vllm

# Run vLLM server with a tiny model for testing
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --host 0.0.0.0 \
  --port 8001
```

**Note**: This requires a GPU and ~16GB VRAM. For testing without a GPU, you can:
1. Mock the vLLM responses in tests
2. Use the interactive docs at http://localhost:8000/docs (shows what the API expects)
3. Deploy to AWS with a GPU instance

## Using the Interactive Docs

1. Go to http://localhost:8000/docs
2. Click "Authorize" button (top right)
3. Enter your JWT token or API key in the format: `Bearer YOUR_TOKEN`
4. Click "Authorize"
5. Now you can test all endpoints interactively!

## Test Quota Limits

The free tier has a 10,000 token limit. To test quota enforcement:

1. Make multiple inference requests
2. Monitor your usage: `GET /v1/usage`
3. Once you hit the limit, you'll get a 429 error

## Common Issues

### "Could not connect to database"
- Make sure PostgreSQL is running: `docker-compose up -d postgres`
- Check DATABASE_URL in `.env`

### "vLLM server returned error"
- vLLM is not running or configured incorrectly
- Check VLLM_ENDPOINT in `.env` (default: http://localhost:8001)

### "Invalid API key"
- Make sure you're using the format: `Authorization: Bearer sk_live_...`
- API keys are hashed, can't be retrieved after creation

## Next Steps

- Deploy to AWS EKS
- Set up vLLM on GPU instance
- Configure Stripe for billing
- Add monitoring and alerts
