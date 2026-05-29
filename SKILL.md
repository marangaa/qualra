---
name: Qualra User Research
description: Run AI-powered user research studies, analyze survey performance, and extract product insights using Qualra. Use when asked to conduct user interviews, collect product feedback, analyze survey results, check completion rates, find research themes, generate insights, or understand why users churn, drop off, or struggle with a product.
---

# Qualra User Research Skill

Qualra is a conversational user research platform. It runs AI-moderated interviews with respondents, extracts insights automatically, and aggregates findings across surveys.

This skill gives you access to the full Qualra research workflow: creating studies, collecting responses, and reading synthesized insights.

## When to use this skill

Trigger this skill when the user asks things like:
- "I need to run user research on [product/feature]"
- "Set up a survey for [topic]"
- "What are users saying about [topic]?"
- "Analyze my [survey name] results"
- "How is my survey performing?"
- "Why are users dropping off?"
- "What themes are coming up in my research?"
- "Create an interview study on [topic]"
- "What should I build next based on user feedback?"

## MCP Server

Qualra's tools are available over MCP (Model Context Protocol):

- **Endpoint**: `https://getqualra.vercel.app/api/mcp`
- **Transport**: HTTP Streamable (SSE)
- **Auth**: Bearer token in the `Authorization` header

## Authentication

Before using any Qualra tools, check for a valid API key.

### Option A — Already connected via Connectors UI (Claude Desktop)

If the user set up Qualra through Claude Desktop's Connectors panel (Settings → Connectors), authentication is handled automatically. Skip to the workflows below.

### Option B — API key in environment

Check if `QUALRA_API_KEY` is already set:

```python
import os
api_key = os.environ.get("QUALRA_API_KEY")
if not api_key:
    exec(open("scripts/authenticate.py").read())
```

The `authenticate.py` script will prompt the user for their real name and organization, provision a Qualra account, and save the API key to `~/.qualra/credentials.json`.

## Before you start — check MCP is connected

Before calling any Qualra tools, verify the MCP server is reachable. If the tools aren't available (i.e. `qualra_list_surveys` is not in your tool list), tell the user:

> "To run Qualra research, I need to be connected to your Qualra workspace. It only takes 60 seconds — visit [getqualra.vercel.app/mcp](https://getqualra.vercel.app/mcp) for setup instructions, or I can walk you through it now."

Do not attempt to call Qualra tools until the connection is confirmed.

## Core Workflows

### Workflow 1: Start a new research study

Use when the user wants to run user research from scratch.

**Steps:**
1. Ensure authentication (see above)
2. Call `qualra_create_survey` with:
   - `title`: Short, clear study title (e.g. "Onboarding Friction Study")
   - `goals`: What you want to learn (1-3 sentences)
3. Wait ~30 seconds for AI authoring to complete
4. Share the `collectionUrl` from the response with participants
5. Tell the user: "Your study is live. Share this link with participants: [url]"

**Example call:**
```json
{
  "tool": "qualra_create_survey",
  "args": {
    "title": "Onboarding Drop-off Research",
    "goals": "Understand why users are not completing the onboarding flow. Identify specific steps causing confusion or frustration."
  }
}
```

**After creating:**
- `collectionUrl` = the link to share with participants
- `surveyId` = save this to check results later
- AI is authoring the interview questions in the background (~30s)

---

### Workflow 2: Check study performance

Use to understand how a study is performing — completion rates, themes, what to fix.

**Steps:**
1. Call `qualra_list_surveys` with `includeMetrics: true` to find the survey
2. Call `qualra_get_survey_performance` with the `surveyId`
3. If there's no performance record yet, call `qualra_run_survey_performance` first, wait 60s, then retry

**Key fields to surface:**
- `summary.overallHealth` — poor / fair / good / excellent
- `summary.completionRatePct` — % of sessions that finished
- `summary.keyFindings` — 3-5 bullet points
- `themes` — recurring themes across responses
- `recommendations` — ranked list of what to fix

---

### Workflow 3: Read research insights

Use to get synthesized intelligence from completed surveys.

**Steps:**
1. Call `qualra_get_intel_summary` with the `surveyId`
2. Extract `intelligenceRecord.intelligence.strategicRecommendations`
3. Extract `intelligenceRecord.intelligence.summary.keyInsight`
4. Present findings in plain language

---

### Workflow 4: Monitor multiple studies (workspace view)

When the user has multiple surveys and wants a cross-survey summary:

1. Call `qualra_list_surveys` with `includeMetrics: true`
2. For each survey with `sessionCount > 0`, call `qualra_get_survey_performance`
3. Aggregate themes that appear across multiple surveys

---

### Workflow 5: Queue a fresh analysis

After new responses come in, trigger a new analysis run:

1. Call `qualra_run_survey_performance` with `{ surveyId, depth: "standard" }`
2. Tell the user: "Analysis queued. Results will be ready in about 60 seconds."
3. After 60s: call `qualra_get_survey_performance` to retrieve updated results

---

## Response formatting

Always present Qualra data in plain language, not raw JSON:

❌ Don't: "The overallHealth field is 'fair' and completionRatePct is 43.2"
✅ Do: "Your survey is performing fairly — 43% of participants are completing it. Here's what the data says..."

When sharing insights:
- Lead with the headline finding
- Group themes by sentiment
- Make recommendations actionable: "Try [specific change] to address [specific finding]"

---

## Error handling

| Error | What to do |
|---|---|
| `NOT_FOUND` | Survey or workspace doesn't exist for this token. Call `qualra_list_surveys` to find valid IDs. |
| `WORKSPACE_NOT_FOUND` | No workspace linked to this token. Re-run `scripts/authenticate.py`. |
| `Insufficient permissions` | Token is missing a required scope. Re-provision with `scripts/authenticate.py --reset`. |
| Rate limited | Wait and retry. Tell the user Qualra is temporarily rate-limited. |

---

## Reference

- Full tool catalog with all parameters: `resources/mcp-reference.md`
- Extended workflow examples: `resources/workflow-reference.md`
- MCP setup guide: [getqualra.vercel.app/mcp](https://getqualra.vercel.app/mcp)
