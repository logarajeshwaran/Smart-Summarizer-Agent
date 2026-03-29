#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  deploy.sh — Deploy Smart Summarizer Agent to Cloud Run
#  Usage: ./deploy.sh
# ─────────────────────────────────────────────────────────────
set -e

# ── Config — edit these ────────────────────────────────────────────────────
SERVICE_NAME="smart-summarizer-agent"
REGION="us-central1"         # Change to your preferred region
# ──────────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Smart Summarizer Agent — Cloud Run Deploy ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  echo "❌ No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi
echo "✓ GCP Project: $PROJECT_ID"

# Check API key
if [ -z "$GOOGLE_API_KEY" ]; then
  if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
  fi
fi
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "❌ GOOGLE_API_KEY not set. Add it to .env or export it."
  exit 1
fi
echo "✓ GOOGLE_API_KEY found"

# Enable required APIs
echo ""
echo "→ Enabling required GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project="$PROJECT_ID" --quiet

echo "✓ APIs enabled"

# Build and deploy via Cloud Build (no local Docker required)
echo ""
echo "→ Deploying to Cloud Run (this takes ~2-3 minutes)..."
echo ""

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
  --project "$PROJECT_ID"

# Get the URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --format "value(status.url)" \
  --project "$PROJECT_ID")

echo ""
echo "════════════════════════════════════════════"
echo "  ✅  Deployed successfully!"
echo ""
echo "  Service URL: $SERVICE_URL"
echo ""
echo "  Test it:"
echo "  curl $SERVICE_URL/health"
echo ""
echo "  curl -X POST $SERVICE_URL/summarize \\"
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"text": "Paste your text here", "style": "concise", "task": "both"}'"'"
echo ""
echo "  API Docs: $SERVICE_URL/docs"
echo "════════════════════════════════════════════"
