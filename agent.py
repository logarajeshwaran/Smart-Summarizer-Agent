"""
Smart Summarizer Agent
ADK + Gemini · Cloud Run deployable

Capability: Accepts any text input and returns
  - A concise summary
  - 3 key points
  - A one-line headline
"""

import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# ── Tool: summarize ────────────────────────────────────────────────────────

def summarize_text(text: str, style: str = "concise") -> dict:
    """
    Summarizes the given text.

    Args:
        text:  The input text to summarize. Can be an article, paragraph,
               conversation transcript, or any block of text.
        style: Summary style — "concise" (2-3 sentences),
               "detailed" (full paragraph), or "bullets" (key points only).

    Returns:
        A dict with keys: headline, summary, key_points, word_count_original,
        word_count_summary, style_used.
    """
    # Word count of original
    word_count = len(text.split())

    # This function is called BY the agent — the agent (Gemini) fills in the
    # actual summary content.  We return a structured scaffold that the agent
    # populates via its own generation step.
    # In ADK, when this tool is invoked the agent decides the content;
    # the function itself just validates inputs and returns a response frame.
    if not text or len(text.strip()) < 10:
        return {
            "error": "Input text is too short to summarize. Please provide at least a sentence.",
            "success": False,
        }

    allowed_styles = {"concise", "detailed", "bullets"}
    if style not in allowed_styles:
        style = "concise"

    return {
        "success": True,
        "original_word_count": word_count,
        "style_requested": style,
        "text_received": text[:200] + ("..." if len(text) > 200 else ""),
        "instruction": (
            f"Summarize the full text in '{style}' style. "
            "Return JSON with keys: headline (one punchy sentence), "
            "summary (the summary prose), key_points (list of 3 strings)."
        ),
    }


def classify_text(text: str) -> dict:
    """
    Classifies the topic/domain of the provided text.

    Args:
        text: The input text to classify.

    Returns:
        A dict with keys: category, confidence, reasoning.
    """
    if not text or len(text.strip()) < 5:
        return {"error": "Text too short to classify.", "success": False}

    return {
        "success": True,
        "text_preview": text[:150],
        "instruction": (
            "Classify this text into one of these categories: "
            "Technology, Science, Business, Politics, Sports, Entertainment, Health, Education, Other. "
            "Return JSON with: category (string), confidence (high/medium/low), reasoning (one sentence)."
        ),
    }


# ── Agent definition ───────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """
You are the Smart Summarizer Agent — a focused AI assistant that summarizes and classifies text.

## Your capabilities
1. **Summarize** any text: articles, emails, transcripts, paragraphs — in concise, detailed, or bullet style
2. **Classify** text by topic/domain
3. **Headline** generation — one-line punchy title for a piece of text

## Behavior rules
- Always call the appropriate tool first before generating your final answer
- After the tool returns, produce your answer in clean JSON format
- If the user sends raw text without instructions, default to a concise summary
- Be factual — never add information that isn't in the original text
- Keep summaries faithful to the source

## Output format
Always respond with valid JSON:
```json
{
  "headline": "One-line title",
  "summary": "The summary text here",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "category": "Technology",
  "word_count_original": 342,
  "agent": "smart-summarizer-v1"
}
```

If only summarization is requested, include headline + summary + key_points.
If only classification is requested, include category + confidence + reasoning.
Always include the "agent" field.
"""

root_agent = Agent(
    name="smart_summarizer_agent",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    description="Summarizes text, extracts key points, generates headlines, and classifies content by topic.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[summarize_text, classify_text],
)
