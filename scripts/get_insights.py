#!/usr/bin/env python3
"""
Qualra Insights Fetcher
========================
Reads performance analysis and synthesized insights from a Qualra survey.
Claude calls this after responses have been collected.

Usage:
  python scripts/get_insights.py --survey-id <id> [--trigger-analysis]

Output (JSON):
  {
    "surveyId": "...",
    "title": "...",
    "health": "fair",
    "completionRate": 43.2,
    "keyFindings": [...],
    "themes": [...],
    "recommendations": [...],
    "crossSurveyContext": {...},
    "collectionUrl": "..."
  }

Flags:
  --trigger-analysis   Queue a fresh analysis run first, then wait 60s
  --depth              quick | standard | comprehensive (default: standard)
  --period             24h | 7d | 30d | all (default: 7d)
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path

QUALRA_BASE_URL = os.environ.get("QUALRA_BASE_URL", "https://getqualra.vercel.app")
MCP_URL = f"{QUALRA_BASE_URL}/api/mcp"


def call_mcp_tool(tool_name: str, args: dict, api_key: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": args},
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
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    result = body.get("result", {})
    if result.get("isError"):
        content = result.get("content", [{}])
        msg = content[0].get("text", "Unknown error") if content else "Unknown error"
        raise RuntimeError(f"Tool error ({tool_name}): {msg}")

    return result.get("structuredContent") or {"text": result.get("content", [{}])[0].get("text", "")}


def resolve_api_key() -> str:
    api_key = os.environ.get("QUALRA_API_KEY")
    if not api_key:
        creds_file = Path.home() / ".qualra" / "credentials.json"
        if creds_file.exists():
            api_key = json.loads(creds_file.read_text()).get("apiKey")
            if api_key:
                os.environ["QUALRA_API_KEY"] = api_key
    if not api_key:
        raise RuntimeError("No QUALRA_API_KEY. Run scripts/authenticate.py first.")
    return api_key


def get_insights(
    survey_id: str,
    trigger_analysis: bool = False,
    depth: str = "standard",
    period: str = "7d",
) -> dict:
    api_key = resolve_api_key()

    # 1. Optionally trigger a fresh analysis run
    if trigger_analysis:
        print(f"[qualra] Queuing performance analysis for survey {survey_id}...", file=sys.stderr)
        try:
            call_mcp_tool(
                "qualra_run_survey_performance",
                {"surveyId": survey_id, "depth": depth, "period": period},
                api_key,
            )
            print("[qualra] Analysis queued. Waiting 65 seconds...", file=sys.stderr)
            time.sleep(65)
        except RuntimeError as e:
            print(f"[qualra] Warning: could not trigger analysis: {e}", file=sys.stderr)

    # 2. Get survey details
    survey_result = call_mcp_tool("qualra_get_survey", {"surveyId": survey_id}, api_key)

    # 3. Get performance data
    perf_result = call_mcp_tool(
        "qualra_get_survey_performance",
        {"surveyId": survey_id, "period": period},
        api_key,
    )

    # 4. Get collection URL
    try:
        url_result = call_mcp_tool("qualra_get_collection_url", {"surveyId": survey_id}, api_key)
        collection_url = url_result.get("collectionUrl")
    except RuntimeError:
        collection_url = None

    # 5. Try to get intelligence summary
    intel = {}
    try:
        intel_result = call_mcp_tool("qualra_get_intel_summary", {"surveyId": survey_id}, api_key)
        intel = intel_result
    except RuntimeError:
        pass

    # ── Shape the response ─────────────────────────────────────────────────────
    perf = perf_result.get("performanceRecord") or perf_result
    summary = perf.get("summary") or {}
    themes = perf.get("themes") or []
    recommendations = perf.get("recommendations") or []

    # Clean up themes for readability
    clean_themes = [
        {
            "theme": t.get("theme"),
            "prevalence": t.get("prevalence"),
            "sentiment": t.get("sentiment", "mixed"),
            "quotes": [q.get("quote") if isinstance(q, dict) else q for q in (t.get("sampleQuotes") or [])[:2]],
        }
        for t in themes[:8]
    ]

    # Clean up recommendations
    clean_recs = [
        {
            "title": r.get("title"),
            "rationale": r.get("rationale"),
            "effort": r.get("effort"),
            "confidence": r.get("confidence"),
        }
        for r in recommendations[:6]
    ]

    return {
        "surveyId": survey_id,
        "title": (survey_result.get("survey") or {}).get("title", ""),
        "sessionCount": survey_result.get("sessionCount", 0),
        "completionCount": survey_result.get("completionCount", 0),
        "health": summary.get("overallHealth", "unknown"),
        "completionRate": summary.get("completionRatePct", 0),
        "keyFindings": summary.get("keyFindings") or [],
        "themes": clean_themes,
        "recommendations": clean_recs,
        "intelligenceSummary": (
            (intel.get("intelligenceRecord") or {})
            .get("intelligence", {})
            .get("summary", {})
            .get("keyInsight")
        ),
        "collectionUrl": collection_url,
        "dataQuality": (perf.get("quality") or {}).get("confidence"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Qualra survey insights")
    parser.add_argument("--survey-id", required=True, help="Survey ID to fetch insights for")
    parser.add_argument("--trigger-analysis", action="store_true", help="Queue a fresh analysis first")
    parser.add_argument("--depth", choices=["quick", "standard", "comprehensive"], default="standard")
    parser.add_argument("--period", choices=["24h", "7d", "30d", "all"], default="7d")
    args = parser.parse_args()

    try:
        result = get_insights(
            survey_id=args.survey_id,
            trigger_analysis=args.trigger_analysis,
            depth=args.depth,
            period=args.period,
        )
        print(json.dumps(result, indent=2))
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
