#!/usr/bin/env python3
"""
Qualra End-to-End Skill Flow Test
=================================
Validates the entire agentic loop by programmatically running the authentication
and survey creation scripts.

Usage:
  python scripts/test_mcp_flow.py

Requirements:
  1. The Qualra Next.js server should be running locally (default: http://localhost:3000)
     or set via QUALRA_BASE_URL env variable.
"""

import os
import sys
import shutil
from pathlib import Path

# Prevent Windows console encoding crashes when printing UTF-8 emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the current directory to sys.path so we can import the scripts
scripts_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(scripts_dir))

# Configure for local testing by default if not set
if "QUALRA_BASE_URL" not in os.environ:
    os.environ["QUALRA_BASE_URL"] = "http://localhost:3000"

print("=" * 60)
print("QUALRA END-TO-END MCP SKILL FLOW TEST")
print("=" * 60)
print(f"Targeting Base URL : {os.environ['QUALRA_BASE_URL']}")

# 1. Clean up existing credentials to force a fresh provisioning run
credentials_file = Path.home() / ".qualra" / "credentials.json"
if credentials_file.exists():
    print(f"Clearing old credentials file at: {credentials_file}")
    try:
        credentials_file.unlink()
    except Exception as e:
        print(f"Warning: Could not delete credentials: {e}")

# 2. Run authenticate.py
print("\n--- STEP 1: Running Account Provisioning & Authentication ---")
try:
    import authenticate
    
    # We will pass test email and organization details
    test_email = "developer_test@qualra.ai"
    test_org = "Developer Sandbox Corp"
    test_url = "https://sandboxcorp.io"
    test_goals = "Track API integration developer experience"
    
    print(f"Provisioning with details:")
    print(f"  Email    : {test_email}")
    print(f"  Org Name : {test_org}")
    print(f"  URL      : {test_url}")
    
    creds = authenticate.main(
        reset=True,
        email=test_email,
        org_name=test_org,
        product_url=test_url,
        goals=test_goals
    )
    
    print("\n✓ Authentication Step Succeeded!")
    print(f"  Saved API Key Prefix : {creds.get('tokenPrefix')}")
    print(f"  Workspace Slug       : {creds.get('workspaceSlug')}")
    
except ImportError as e:
    print(f"❌ Failed to import authenticate.py: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"❌ Authentication failed: {e}", file=sys.stderr)
    sys.exit(1)

# 3. Run run_research.py
print("\n--- STEP 2: Creating a Research Survey via MCP ---")
try:
    import run_research
    
    study_title = "Developer Feedback Study V1"
    study_goals = "Gather feedback on the ease of integrating the new Qualra MCP server and provisioning route."
    custom_tone = "professional, conversational, encouraging"
    
    print(f"Creating survey:")
    print(f"  Title : {study_title}")
    print(f"  Goals : {study_goals}")
    
    survey_result = run_research.run_research(
        title=study_title,
        goals=study_goals,
        product_url=test_url,
        custom_tone=custom_tone,
        workspace_id=creds.get("workspaceId")
    )
    
    print("\n✓ Survey Creation Step Succeeded!")
    print(f"  Survey ID      : {survey_result.get('surveyId')}")
    print(f"  Workspace Slug : {survey_result.get('workspaceSlug')}")
    print(f"  Collection URL : {survey_result.get('collectionUrl')}")
    print(f"  Survey URL     : {survey_result.get('surveyUrl')}")
    print(f"  Authoring Status: {survey_result.get('authoringStatus')}")
    
except ImportError as e:
    print(f"❌ Failed to import run_research.py: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"❌ Survey creation failed: {e}", file=sys.stderr)
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ SUCCESS: Entire end-to-end MCP Skill flow validated successfully!")
print("=" * 60)
