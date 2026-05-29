#!/usr/bin/env python3
"""
Qualra Research Launcher
=========================
Creates a new Qualra research study and returns the collection link.
Claude calls this script when starting a new user research study.

Usage (called by Claude):
  python scripts/run_research.py \
    --title "Onboarding Drop-off Study" \
    --goals "Understand why users leave during step 3 of onboarding" \
    [--product-url https://myapp.com] \
    [--custom-tone conversational]

Output (JSON):
  {
    "surveyId": "...",
    "title": "...",
    "collectionUrl": "https://getqualra.vercel.app/agent-next/chat/...",
    "workspaceSlug": "...",
    "authoringStatus": "queued",
    "estimatedReadyMs": 30000,
    "nextSteps": "..."
  }
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

QUALRA_BASE_URL = os.environ.get("QUALRA_BASE_URL", "https://getqualra.vercel.app")
MCP_URL = f"{QUALRA_BASE_URL}/api/mcp"

# ── MCP client ────────────────────────────────────────────────────────────────


def call_mcp_tool(tool_name: str, args: dict, api_key: str) -> dict:
    """Call a Qualra MCP tool and return the structured result."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MCP HTTP {e.code}: {body_text}") from e

    result = body.get("result", {})
    if result.get("isError"):
        content = result.get("content", [{}])
        msg = content[0].get("text", "Unknown tool error") if content else "Unknown tool error"
        raise RuntimeError(f"Tool error: {msg}")

    structured = result.get("structuredContent")
    if structured:
        return structured

    # Fall back to parsing text content
    content = result.get("content", [{}])
    text = content[0].get("text", "") if content else ""
    return {"text": text}


# ── Main ──────────────────────────────────────────────────────────────────────


def run_research(
    title: str,
    goals: str,
    product_url: str | None = None,
    custom_tone: str | None = None,
    workspace_id: str | None = None,
) -> dict:
    # Resolve API key
    api_key = os.environ.get("QUALRA_API_KEY")
    if not api_key:
        # Try loading from credentials file
        creds_file = Path.home() / ".qualra" / "credentials.json"
        if creds_file.exists():
            creds = json.loads(creds_file.read_text())
            api_key = creds.get("apiKey")
            if api_key:
                os.environ["QUALRA_API_KEY"] = api_key
                workspace_id = workspace_id or creds.get("workspaceId")

    if not api_key:
        raise RuntimeError(
            "No QUALRA_API_KEY found. Run scripts/authenticate.py first."
        )

    # Call qualra_create_survey
    args: dict = {"title": title, "goals": goals}
    if workspace_id:
        args["workspaceId"] = workspace_id
    if custom_tone:
        args["customTone"] = custom_tone

    result = call_mcp_tool("qualra_create_survey", args, api_key)

    return {
        "surveyId": result.get("surveyId"),
        "title": result.get("title", title),
        "collectionUrl": result.get("collectionUrl"),
        "surveyUrl": result.get("surveyUrl"),
        "workspaceSlug": result.get("workspaceSlug"),
        "authoringStatus": result.get("authoringStatus", "queued"),
        "estimatedReadyMs": result.get("estimatedReadyMs", 30000),
        "nextSteps": (
            "Share the collectionUrl with participants. "
            "After you have responses, run scripts/get_insights.py "
            f"--survey-id {result.get('surveyId')} to read the findings."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Qualra research study")
    parser.add_argument("--title", required=True, help="Study title")
    parser.add_argument("--goals", required=True, help="Research goals")
    parser.add_argument("--product-url", help="Your product URL (context for AI authoring)")
    parser.add_argument("--custom-tone", help="Interview tone override (e.g. 'friendly, empathetic')")
    parser.add_argument("--workspace-id", help="Specific workspace ID to use")
    args = parser.parse_args()

    try:
        result = run_research(
            title=args.title,
            goals=args.goals,
            product_url=args.product_url,
            custom_tone=args.custom_tone,
            workspace_id=args.workspace_id,
        )
        print(json.dumps(result, indent=2))
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
