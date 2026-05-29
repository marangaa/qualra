# Qualra User Research Skill (`qualra-research-skill`)

[![skills.sh](https://skills.sh/b/marangaa/qualra)](https://skills.sh/marangaa/qualra)

An AI agent skill that enables LLMs and agents to run AI-powered user research studies, analyze survey completion, and extract qualitative insights using the [Qualra](https://getqualra.vercel.app) MCP server.

This skill works across modern agent platforms (Claude Desktop, Cursor, Gemini, Copilot, Windsurf, etc.) and integrates seamlessly into developer workflows.

## Features

- **Automated Survey Authoring**: Provisions workspaces and designs custom conversational research studies with standard or empathetic tones.
- **Respondent Interfaces**: Supports responses across Web, Mobile, Tablet, Email, and In-App clients.
- **Deep Synthesized Insights**: Automatically categorizes qualitative themes, quotes, and actionable product recommendations.
- **Background Autopilot**: Runs in the background and delivers summaries and Linear/Jira backlog updates once data is collected.

## Directory Structure

```
qualra/
├── SKILL.md                  # Main AI skill definition containing triggers, workflows, and prompts
├── README.md                 # This instructions guide
├── scripts/
│   ├── authenticate.py       # Provisioning script for API keys & workspace setup
│   ├── run_research.py       # Creating & launching studies via MCP
│   ├── get_insights.py       # Analysis, theme retrieval & recommendation fetching
│   └── test_mcp_flow.py      # Local end-to-end verification script
└── resources/
    └── mcp-reference.md      # Full API catalog & tool specifications for reference
```

## Installation

Install the skill instantly into your AI agent environment using the Vercel `skills` CLI:

```bash
npx skills add marangaa/qualra
```

This downloads `SKILL.md` triggers and helper scripts directly into your agent's runtime environment.

## Quick Start

1. **Connect MCP**: Before running tools, make sure your agent is connected to the Qualra MCP server. Setup instructions are available at [getqualra.vercel.app/mcp](https://getqualra.vercel.app/mcp).
2. **Authenticate**: If your workspace isn't linked yet, the agent will guide you to set up your credentials, or you can initialize it manually:
   ```bash
   python scripts/authenticate.py
   ```
3. **Launch Research**: Ask your agent: *"I need to run user research on onboarding friction."* The agent will automatically provision the workspace and share your live survey link!
