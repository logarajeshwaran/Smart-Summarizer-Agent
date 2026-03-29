"""
test_agent.py — Local tests for Smart Summarizer Agent
Run: python test_agent.py
Or against Cloud Run: BASE_URL=https://your-url.run.app python test_agent.py
"""

import asyncio
import json
import os
import sys

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

SAMPLE_TEXT = """
Artificial intelligence is rapidly transforming industries across the globe.
In healthcare, AI systems can now detect cancers from medical images with accuracy
that rivals experienced radiologists. In transportation, autonomous vehicles are
being tested in dozens of cities, promising to reduce accidents caused by human
error. The financial sector uses AI to detect fraud in milliseconds, protecting
millions of customers daily. However, this rapid adoption raises important questions
about job displacement, algorithmic bias, and the concentration of power in the
hands of a few large technology companies. Governments worldwide are beginning to
introduce AI regulation, with the European Union leading the way with its
comprehensive AI Act, which classifies AI systems by risk level and imposes
strict requirements on high-risk applications.
"""


async def run_tests():
    async with httpx.AsyncClient(timeout=60) as client:
        print("\n" + "═"*52)
        print("  Smart Summarizer Agent — Test Suite")
        print("═"*52)
        print(f"  Target: {BASE_URL}\n")

        # ── Test 1: Health check ───────────────────────────────────────
        print("→ Test 1: Health check")
        r = await client.get(f"{BASE_URL}/health")
        assert r.status_code == 200, f"Health failed: {r.status_code}"
        print(f"  ✓ {r.json()}")

        # ── Test 2: Root info ──────────────────────────────────────────
        print("\n→ Test 2: Root endpoint")
        r = await client.get(f"{BASE_URL}/")
        assert r.status_code == 200
        data = r.json()
        print(f"  ✓ Service: {data['service']} v{data['version']}")

        # ── Test 3: Summarize (concise) ────────────────────────────────
        print("\n→ Test 3: Summarize — concise style")
        r = await client.post(f"{BASE_URL}/summarize", json={
            "text": SAMPLE_TEXT,
            "style": "concise",
            "task": "summarize",
        })
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert data["success"]
        result = data["result"]
        print(f"  ✓ request_id: {data['request_id']}")
        print(f"  ✓ headline:   {result.get('headline', 'N/A')}")
        print(f"  ✓ summary:    {str(result.get('summary', 'N/A'))[:120]}...")
        print(f"  ✓ key_points: {result.get('key_points', [])}")

        # ── Test 4: Classify ───────────────────────────────────────────
        print("\n→ Test 4: Classification task")
        r = await client.post(f"{BASE_URL}/summarize", json={
            "text": SAMPLE_TEXT,
            "task": "classify",
        })
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        result = data["result"]
        print(f"  ✓ category:   {result.get('category', 'N/A')}")
        print(f"  ✓ confidence: {result.get('confidence', 'N/A')}")

        # ── Test 5: Both ───────────────────────────────────────────────
        print("\n→ Test 5: Summarize + Classify (both)")
        r = await client.post(f"{BASE_URL}/summarize", json={
            "text": SAMPLE_TEXT,
            "style": "bullets",
            "task": "both",
        })
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        result = data["result"]
        print(f"  ✓ category:   {result.get('category', 'N/A')}")
        print(f"  ✓ agent:      {result.get('agent', 'N/A')}")

        # ── Test 6: /ask endpoint ──────────────────────────────────────
        print("\n→ Test 6: /ask flexible endpoint")
        r = await client.post(f"{BASE_URL}/ask", json={
            "message": f"Give me a one-paragraph summary of this: {SAMPLE_TEXT[:300]}"
        })
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        print(f"  ✓ success: {data['success']}")

        # ── Test 7: Short text (edge case) ─────────────────────────────
        print("\n→ Test 7: Edge case — very short text")
        r = await client.post(f"{BASE_URL}/summarize", json={
            "text": "Climate change is a global challenge.",
            "style": "concise",
            "task": "both",
        })
        print(f"  ✓ status: {r.status_code}")

        print("\n" + "═"*52)
        print("  ✅  All tests passed!")
        print("═"*52 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
