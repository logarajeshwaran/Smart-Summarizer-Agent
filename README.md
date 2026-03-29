# Smart Summarizer Agent

> **ADK + Gemini 2.0 Flash · Cloud Run · FastAPI**
> A single AI agent that summarizes text, extracts key points, generates headlines, and classifies content — deployed as a public HTTP endpoint on Cloud Run.

---

## What It Does

One clearly defined capability: **intelligent text summarization and classification**.

Send any text → get back structured JSON with:

| Field | Description |
|---|---|
| `headline` | One punchy sentence title |
| `summary` | Summarized text in your chosen style |
| `key_points` | 3 extracted key points |
| `category` | Topic classification (Technology, Science, etc.) |
| `word_count_original` | Source word count |

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | **Google ADK** (Agent Development Kit) |
| AI Model | **Gemini 2.0 Flash** via LiteLLM |
| HTTP Server | **FastAPI** + Uvicorn |
| Deployment | **Google Cloud Run** |
| Language | Python 3.11 |

---

## Project Structure

```
smart-summarizer-agent/
├── agent.py          # ADK Agent + tool definitions
├── main.py           # FastAPI HTTP server (Cloud Run entrypoint)
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container build (Cloud Run compatible)
├── deploy.sh         # One-command deployment script
├── test_agent.py     # Automated test suite
└── .env.example      # Environment variable template
```

---

## Quickstart (Local)

### 1. Get a Google API Key

Go to https://aistudio.google.com/app/apikey and create a key.

### 2. Set up environment

```bash
git clone https://github.com/YOUR_USERNAME/smart-summarizer-agent
cd smart-summarizer-agent

cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Install and run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py
# Server starts on http://localhost:8080
```

### 4. Test it

```bash
# Health check
curl http://localhost:8080/health

# Summarize
curl -X POST http://localhost:8080/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence is transforming industries worldwide. From healthcare to autonomous vehicles, AI systems now perform tasks that once required human expertise. Governments are racing to create regulatory frameworks before the technology outpaces legislation.",
    "style": "concise",
    "task": "both"
  }'

# Run full test suite
python test_agent.py
```

---

## Deploy to Cloud Run

### Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated: `gcloud auth login`
- A GCP project: `gcloud config set project YOUR_PROJECT_ID`

### One-command deploy

```bash
export GOOGLE_API_KEY=your_key_here
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Enable Cloud Run, Cloud Build, and Artifact Registry APIs
2. Build the container via Cloud Build (no Docker needed locally)
3. Deploy to Cloud Run with public access
4. Print your live URL

### Manual deploy (alternative)

```bash
# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export SERVICE=smart-summarizer-agent

# Deploy directly from source
gcloud run deploy $SERVICE \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "GOOGLE_API_KEY=YOUR_KEY_HERE" \
  --project $PROJECT_ID
```

---

## API Reference

### `POST /summarize` — Main endpoint

**Request:**
```json
{
  "text": "Your text here (minimum 10 characters)",
  "style": "concise",
  "task": "both"
}
```

| Field | Values | Default | Description |
|---|---|---|---|
| `text` | string | required | Text to process |
| `style` | `concise` \| `detailed` \| `bullets` | `concise` | Summary length/format |
| `task` | `summarize` \| `classify` \| `both` | `summarize` | What the agent should do |

**Response:**
```json
{
  "success": true,
  "request_id": "a1b2c3d4",
  "agent": "smart_summarizer_agent",
  "result": {
    "headline": "AI Regulation Race: Can Governments Keep Up?",
    "summary": "Artificial intelligence is rapidly reshaping global industries...",
    "key_points": [
      "AI achieves expert-level performance in healthcare diagnostics",
      "EU's AI Act introduces risk-based regulation framework",
      "Job displacement and algorithmic bias remain key concerns"
    ],
    "category": "Technology",
    "confidence": "high",
    "word_count_original": 142,
    "agent": "smart-summarizer-v1"
  }
}
```

### `POST /ask` — Flexible endpoint

Send any natural language instruction with your text:

```bash
curl -X POST https://YOUR-URL.run.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize this in 3 bullet points: [your text]"}'
```

### `GET /health` — Health check

```json
{"status": "healthy", "agent": "smart_summarizer_agent", "model": "gemini-2.0-flash"}
```

### `GET /docs` — Interactive API docs (Swagger UI)

---

## How It Works — Architecture

```
HTTP Request (POST /summarize)
        │
        ▼
   FastAPI (main.py)
        │
        │  Builds natural language prompt
        ▼
  ADK Runner.run_async()
        │
        ▼
  smart_summarizer_agent  ←── System instruction (agent.py)
        │
        │  Decides which tool to call
        ▼
  Tool: summarize_text()        Tool: classify_text()
  or    classify_text()     →   (can call both)
        │
        ▼
  Gemini 2.0 Flash
  (executes tool + generates structured JSON response)
        │
        ▼
  FastAPI parses JSON response
        │
        ▼
  HTTP Response (AgentResponse)
```

**Key ADK concepts used:**
- `Agent` — defines the agent with name, model, instruction, and tools
- `LiteLlm` — connects to Gemini via the LiteLLM adapter (`gemini/gemini-2.0-flash`)
- `Runner` — executes the agent in a session
- `InMemorySessionService` — stateless per-request sessions (perfect for Cloud Run)
- Tool functions — Python functions decorated by type hints that the agent can call

---

## Submission Checklist

- [x] Implemented using **Google ADK**
- [x] Uses **Gemini 2.0 Flash** for inference
- [x] One clearly defined task: **text summarization + classification**
- [x] Accepts HTTP input (`POST /summarize`)
- [x] Returns valid structured JSON response
- [x] Deployable to **Cloud Run** with public endpoint
- [x] `Dockerfile` included for containerized deployment
- [x] `deploy.sh` for one-command deployment
- [x] `test_agent.py` for endpoint validation

---

## Live Demo

```
Cloud Run URL: https://smart-summarizer-agent-XXXX.run.app
Health:        https://smart-summarizer-agent-XXXX.run.app/health
API Docs:      https://smart-summarizer-agent-XXXX.run.app/docs
```

---

*Built with Google ADK · Gemini 2.0 Flash · FastAPI · Cloud Run*
