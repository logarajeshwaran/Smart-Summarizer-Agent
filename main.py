"""
main.py — HTTP server wrapping the ADK Smart Summarizer Agent
Deployable to Cloud Run as a stateless container.
"""

import json
import os
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import root_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-summarizer")

# ── Session service (in-memory, stateless per request) ─────────────────────
session_service = InMemorySessionService()
APP_NAME = "smart_summarizer_agent"

# ── FastAPI app ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Smart Summarizer Agent starting up...")
    yield
    logger.info("Smart Summarizer Agent shutting down.")

app = FastAPI(
    title="Smart Summarizer Agent",
    description="ADK + Gemini agent that summarizes text, extracts key points, and classifies content.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ──────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="The text to summarize or classify")
    style: Optional[str] = Field(
        "concise",
        description="Summary style: 'concise' (default), 'detailed', or 'bullets'"
    )
    task: Optional[str] = Field(
        "summarize",
        description="Task: 'summarize', 'classify', or 'both'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Artificial intelligence is transforming industries worldwide. From healthcare diagnostics to autonomous vehicles, AI systems are now performing tasks that once required human expertise. Companies are investing billions in machine learning research, and governments are racing to establish regulatory frameworks before the technology outpaces legislation.",
                "style": "concise",
                "task": "both"
            }
        }

class AgentResponse(BaseModel):
    success: bool
    request_id: str
    agent: str
    result: dict
    raw_response: Optional[str] = None


# ── Core ADK runner helper ─────────────────────────────────────────────────

async def run_agent(user_message: str) -> str:
    """Creates a single-use session, runs the agent, returns final text response."""
    session_id = str(uuid.uuid4())
    user_id = "http-user"

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)],
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text
            break

    return final_text


def parse_agent_output(raw: str) -> dict:
    """Try to extract JSON from the agent's response text."""
    raw = raw.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Return raw text in a structured wrapper
        return {"raw_text": raw, "parse_note": "Agent returned plain text instead of JSON"}


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "Smart Summarizer Agent",
        "version": "1.0.0",
        "model": "gemini-2.0-flash",
        "framework": "Google ADK",
        "endpoints": {
            "POST /summarize": "Main agent endpoint — summarize, classify, or both",
            "GET  /health":    "Health check",
            "GET  /docs":      "Interactive API documentation",
        },
        "example_curl": (
            'curl -X POST https://YOUR-CLOUD-RUN-URL/summarize '
            '-H "Content-Type: application/json" '
            '-d \'{"text": "Your text here", "style": "concise", "task": "both"}\''
        ),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "smart_summarizer_agent", "model": "gemini-2.0-flash"}


@app.post("/summarize", response_model=AgentResponse)
async def summarize(req: SummarizeRequest):
    """
    Main agent endpoint.

    Send any text and get back:
    - **headline**: one-line punchy title
    - **summary**: summarized version in your chosen style
    - **key_points**: 3 bullet points
    - **category**: topic classification
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] task={req.task} style={req.style} chars={len(req.text)}")

    # Build a natural language prompt for the agent
    task_prompts = {
        "summarize": f"Please summarize the following text in '{req.style}' style:\n\n{req.text}",
        "classify":  f"Please classify the topic/domain of the following text:\n\n{req.text}",
        "both": (
            f"Please summarize (style: '{req.style}') AND classify the topic of the following text. "
            f"Return all fields in your JSON response:\n\n{req.text}"
        ),
    }
    prompt = task_prompts.get(req.task or "summarize", task_prompts["summarize"])

    try:
        raw_response = await run_agent(prompt)
    except Exception as e:
        logger.error(f"[{request_id}] Agent error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    parsed = parse_agent_output(raw_response)
    parsed.setdefault("agent", "smart-summarizer-v1")
    parsed.setdefault("word_count_original", len(req.text.split()))

    return AgentResponse(
        success=True,
        request_id=request_id,
        agent="smart_summarizer_agent",
        result=parsed,
        raw_response=raw_response if os.getenv("DEBUG") else None,
    )


# ── Generic catch-all for forwarding raw text via POST body ────────────────

@app.post("/ask")
async def ask(request: Request):
    """
    Flexible endpoint — send a raw JSON body with a 'message' field
    or a plain text body.
    """
    try:
        body = await request.json()
        message = body.get("message") or body.get("text") or body.get("input", "")
    except Exception:
        message = (await request.body()).decode("utf-8", errors="ignore")

    if not message:
        raise HTTPException(status_code=400, detail="No input provided. Send {'message': '...'}")

    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] /ask chars={len(message)}")

    try:
        raw_response = await run_agent(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    parsed = parse_agent_output(raw_response)
    parsed.setdefault("agent", "smart-summarizer-v1")

    return {"success": True, "request_id": request_id, "result": parsed}


# ── Dev entrypoint ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
