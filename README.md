# Qualra User Research Skill (`qualra-research-skill`)

An AI agent skill that enables LLMs and agents to run AI-powered user research studies, analyze survey completion, and extract rich qualitative insights using the [Qualra](https://..vercel.app) MCP server.

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

## How to Install and Publish

This repository is ready to be published to a public GitHub repo (e.g. `github.com/marangaa/qualra`). 

### Running Locally (Testing)

You can test the provisioning and survey creation scripts end-to-end. Ensure you have Python 3 installed:

```bash
# Run the end-to-end flow test (targets http://localhost:3000 or getqualra.vercel.app)
python scripts/test_mcp_flow.py
```

### Distributing via skills.sh

Once pushed to a public GitHub repository at `marangaa/qualra`, users can immediately install your skill onto their system using the `skills` CLI:

```bash
npx skills add marangaa/qualra
```

This single command downloads the `SKILL.md` triggers, the helper scripts, and links them directly to their local agent runtime environment.
