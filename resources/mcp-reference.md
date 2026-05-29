# Qualra MCP Tool Reference

Complete reference for all tools exposed by the Qualra MCP server at `https://getqualra.vercel.app/api/mcp`.

## Authentication

All tools require a Bearer token:
```
Authorization: Bearer res_api_<40 hex chars>
```

Tokens are provisioned via `POST /api/mcp/provision` (no auth required) or via the Qualra dashboard.

## Scopes

| Scope | What it allows |
|-------|----------------|
| `read:surveys` | View surveys, get collection URLs, list performance history |
| `write:surveys` | Create new surveys |
| `read:intelligence` | Read performance analysis, themes, intelligence reports |
| `write:intelligence` | Generate market intelligence, executive dashboard |
| `read:organization` | View org profile and workspaces |
| `write:analysis` | Trigger survey performance analysis runs |

Tokens provisioned via the skill have all scopes except `read:organization` write variants.

---

## Tools

### `qualra_list_surveys`

List surveys in the accessible workspace.

**Scopes**: `read:surveys`

**Args**:
- `limit` (int, 1-100, optional) — max surveys to return
- `includeMetrics` (bool, optional) — include session/completion counts
- `cursor` (string, optional) — pagination cursor

**Returns**: `{ surveys, count, totalCount, hasMore, nextCursor }`

---

### `qualra_get_survey`

Get full details for a single survey.

**Scopes**: `read:surveys`

**Args**:
- `surveyId` (string, required)
- `includeSessionFlows` (bool, optional)

**Returns**: `{ survey, responseCount, sessionCount, completionCount, sessionFlows? }`

---

### `qualra_create_survey`

Create a new survey and queue AI authoring.

**Scopes**: `write:surveys`

**Args**:
- `title` (string, required) — study title (max 200 chars)
- `goals` (string, required) — research objectives (max 1500 chars)
- `workspaceId` (string, optional) — specific workspace
- `customTone` (string, optional) — interview tone (max 400 chars)

**Returns**: `{ surveyId, title, workspaceId, workspaceSlug, collectionUrl, surveyUrl, authoringStatus, estimatedReadyMs }`

---

### `qualra_get_collection_url`

Get the shareable link for collecting responses.

**Scopes**: `read:surveys`

**Args**:
- `surveyId` (string, required)

**Returns**: `{ surveyId, title, isActive, workspaceSlug, collectionUrl, surveyUrl }`

---

### `qualra_analyze_survey`

Re-analyze a survey's design with AI and optionally update it.

**Scopes**: `write:analysis`

**Args**:
- `title` (string, required)
- `goals` (string, required)
- `surveyId` (string, optional) — if provided, persists analysis back to the survey
- `workspaceId` (string, optional)
- `customTone` (string, optional)

**Returns**: `{ finalGoals, analysis, coaching, preflight, updatedSurveyId? }`

---

### `qualra_get_survey_performance`

Get the latest performance analysis for a survey.

**Scopes**: `read:surveys`, `read:intelligence`

**Args**:
- `surveyId` (string, required)
- `period` ("24h" | "7d" | "30d" | "all", optional, default "7d")

**Returns**: `{ performanceRecord: { summary, themes, insights, diagnostics, recommendations, quality } }`

Key fields:
- `summary.overallHealth` — "poor" | "fair" | "good" | "excellent"
- `summary.completionRatePct` — 0-100
- `summary.keyFindings` — string[]
- `themes[].theme`, `.prevalence`, `.sentiment`, `.sampleQuotes`
- `recommendations[].title`, `.rationale`, `.effort`, `.confidence`

---

### `qualra_run_survey_performance`

Queue a fresh performance analysis. Async — poll after ~60s.

**Scopes**: `read:surveys`, `write:analysis`

**Args**:
- `surveyId` (string, required)
- `depth` ("quick" | "standard" | "comprehensive", optional)
- `period` ("24h" | "7d" | "30d" | "all", optional)

**Returns**: `{ status: "queued", surveyId }`

---

### `qualra_list_survey_performance_history`

Get historical analysis runs for trend tracking.

**Scopes**: `read:surveys`, `read:intelligence`

**Args**:
- `surveyId` (string, required)
- `limit` (int 1-20, optional)
- `cursor` (string, optional)

**Returns**: `{ records, hasMore, nextCursor }`

---

### `qualra_get_intel_summary`

Get the synthesized intelligence for a survey — executive dashboard + intelligence record.

**Scopes**: `read:intelligence`

**Args**:
- `surveyId` (string, required)

**Returns**: `{ surveyId, surveyTitle, intelligenceRecord, executiveDashboard, marketIntelligence }`

Key field: `intelligenceRecord.intelligence.strategicRecommendations[]`

---

### `qualra_run_market_intelligence`

Generate market analysis from a company URL.

**Scopes**: `write:intelligence`

**Args**:
- `companyUrl` (string URL, required)
- `surveyId` (string, optional) — if provided, persists to the survey
- `idempotencyKey` (string 8-128 chars, optional)

**Returns**: `{ marketIntelligence, persistedToSurveyId, idempotentReplay }`

---

### `qualra_run_executive_dashboard`

Generate executive narrative from existing intelligence data.

**Scopes**: `write:intelligence`

**Args**:
- `surveyId` (string, required)
- `idempotencyKey` (string, optional)

**Returns**: `{ executiveDashboard, idempotentReplay }`

---

### `qualra_list_experiment_plans`

List A/B experiment plans for a survey.

**Scopes**: `read:surveys`, `read:intelligence`

**Args**:
- `surveyId` (string, required)
- `status` (array of "draft" | "running" | "completed" | "stopped", optional)
- `limit` (int 1-50, optional)

**Returns**: `{ experimentPlans, count }`

---

### `qualra_get_organization_profile`

Get organization details and workspaces.

**Scopes**: `read:organization`

**Args**:
- `includeMembers` (bool, optional)

**Returns**: `{ organization, memberCount }`

---

## Provisioning (No Auth Required)

### `POST /api/mcp/provision`

Create a Qualra workspace and API token from scratch. Used by `scripts/authenticate.py`.

**Body**:
```json
{
  "email": "user@example.com",
  "orgName": "My Sandbox Company",
  "productUrl": "https://myapp.com",
  "goals": "Understand user friction in onboarding",
  "idempotencyKey": "uuid-here"
}
```

**Returns**:
```json
{
  "apiKey": "res_api_...",
  "tokenPrefix": "res_api_abc...",
  "organizationId": "...",
  "workspaceId": "...",
  "workspaceSlug": "...",
  "mcpUrl": "https://getqualra.vercel.app/api/mcp",
  "collectionBaseUrl": "https://getqualra.vercel.app/agent-next/chat/...",
  "setupUrl": "https://getqualra.vercel.app/dashboard",
  "scopes": [...],
  "expiresAt": "...",
  "warning": "Store the apiKey securely."
}
```

---

## Typical LLM Research Workflow

```
1. POST /api/mcp/provision      → apiKey, workspaceId
2. qualra_create_survey          → surveyId, collectionUrl
3. [Share collectionUrl with participants]
4. [Wait for responses]
5. qualra_run_survey_performance → status: "queued"
6. [Wait 60s]
7. qualra_get_survey_performance → themes, recommendations, health
8. qualra_get_intel_summary      → strategic insights, executive dashboard
```
