#!/usr/bin/env python3
"""
Qualra Authentication Script
=============================
Provisions a Qualra account and stores the API key for use in subsequent
Qualra MCP tool calls.

Usage (from the skill):
  exec(open("scripts/authenticate.py").read())

Or standalone:
  python scripts/authenticate.py [--reset] [--product-url URL] [--goals GOALS]

The script will:
  1. Check if QUALRA_API_KEY is already set (and not expired)
  2. If not, call POST /api/mcp/provision to create an account
  3. Store the API key in QUALRA_API_KEY environment variable
  4. Print connection details for the user

Configuration is persisted to ~/.qualra/credentials so the key survives
across Claude sessions.
"""

import os
import sys
import json
import uuid
import urllib.request
import urllib.error
from pathlib import Path

# Prevent Windows console encoding crashes when printing UTF-8 emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, timezone

# ── Constants ─────────────────────────────────────────────────────────────────

QUALRA_BASE_URL = os.environ.get("QUALRA_BASE_URL", "https://getqualra.vercel.app")
PROVISION_URL = f"{QUALRA_BASE_URL}/api/mcp/provision"
CREDENTIALS_DIR = Path.home() / ".qualra"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"

# ── Helpers ───────────────────────────────────────────────────────────────────


def load_stored_credentials() -> dict | None:
    """Load credentials from ~/.qualra/credentials.json if they exist."""
    try:
        if CREDENTIALS_FILE.exists():
            data = json.loads(CREDENTIALS_FILE.read_text())
            # Check expiry
            if expires_at := data.get("expiresAt"):
                expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expiry > datetime.now(timezone.utc):
                    return data
    except Exception:
        pass
    return None


def save_credentials(creds: dict) -> None:
    """Persist credentials to ~/.qualra/credentials.json."""
    try:
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        CREDENTIALS_FILE.write_text(json.dumps(creds, indent=2))
        # Restrict to owner-only on Unix
        CREDENTIALS_FILE.chmod(0o600)
    except Exception as e:
        print(f"[qualra] Warning: could not persist credentials: {e}")


def provision_account(
    email: str,
    org_name: str,
    product_url: str | None = None,
    goals: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Call the Qualra provisioning endpoint and return credentials."""
    payload = {
        k: v
        for k, v in {
            "email": email,
            "orgName": org_name,
            "productUrl": product_url,
            "goals": goals,
            "idempotencyKey": idempotency_key or str(uuid.uuid4()),
        }.items()
        if v is not None
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        PROVISION_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if resp.status not in (200, 201):
                raise RuntimeError(f"Provision failed: {result.get('error', 'unknown error')}")
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Provision HTTP {e.code}: {body}") from e


# ── Main ──────────────────────────────────────────────────────────────────────


def main(
    reset: bool = False,
    email: str | None = None,
    org_name: str | None = None,
    product_url: str | None = None,
    goals: str | None = None,
) -> dict:
    """
    Authenticate with Qualra and return the credential dict.
    Sets QUALRA_API_KEY in the current environment.
    """
    # 1. Check environment (set externally or from a previous run in this session)
    if not reset and (existing_key := os.environ.get("QUALRA_API_KEY")):
        print(f"[qualra] Using existing API key from environment: {existing_key[:18]}...")
        return {
            "apiKey": existing_key,
            "mcpUrl": f"{QUALRA_BASE_URL}/api/mcp",
        }

    # 2. Check persisted credentials
    if not reset and (creds := load_stored_credentials()):
        api_key = creds.get("apiKey")
        if api_key:
            os.environ["QUALRA_API_KEY"] = api_key
            print(f"[qualra] Loaded stored API key: {creds.get('tokenPrefix', api_key[:18])}...")
            print(f"[qualra] Workspace: {creds.get('workspaceSlug', 'unknown')}")
            print(f"[qualra] MCP endpoint: {creds.get('mcpUrl', QUALRA_BASE_URL + '/api/mcp')}")
            return creds

    # 3. Prompt for credentials if not supplied
    if not email:
        email = os.environ.get("QUALRA_USER_EMAIL")
        if not email:
            try:
                email = input("Enter your email address for account/verification: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[qualra] Authentication cancelled.", file=sys.stderr)
                sys.exit(1)
        if not email:
            print("[qualra] ❌ Email is required for authentication.", file=sys.stderr)
            sys.exit(1)

    if not org_name:
        org_name = os.environ.get("QUALRA_ORG_NAME")
        if not org_name:
            try:
                org_name = input("Enter your organization or product name: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[qualra] Authentication cancelled.", file=sys.stderr)
                sys.exit(1)
        if not org_name:
            print("[qualra] ❌ Organization name is required.", file=sys.stderr)
            sys.exit(1)

    # 4. Prompt for extra metadata if not reset/preset
    # (We can just skip product_url and goals if not provided, letting provisioning auto-derive or prompt)

    # 5. Provision a new account
    print(f"[qualra] Provisioning workspace for {org_name} ({email})...")
    idem_key = str(uuid.uuid4())

    try:
        result = provision_account(
            email=email,
            org_name=org_name,
            product_url=product_url,
            goals=goals,
            idempotency_key=idem_key,
        )
    except RuntimeError as e:
        print(f"[qualra] ❌ Provisioning failed: {e}", file=sys.stderr)
        raise

    if result.get("replay"):
        # Already provisioned with this key — user needs to use stored key
        print("[qualra] ⚠ This idempotency key was already used.")
        print(f"[qualra] Token prefix: {result.get('tokenPrefix')}")
        print("[qualra] Please use your previously stored API key.")
        return result

    api_key = result["apiKey"]
    os.environ["QUALRA_API_KEY"] = api_key

    # Persist for future sessions
    save_credentials(result)

    print("\n[qualra] ✅ Qualra workspace provisioned successfully!")
    print(f"  API key prefix : {result.get('tokenPrefix')}")
    print(f"  Workspace      : {result.get('workspaceSlug')}")
    print(f"  MCP endpoint   : {result.get('mcpUrl')}")
    print(f"  Token expires  : {result.get('expiresAt', 'in 90 days')}")
    print(f"  Collection URL : {result.get('collectionBaseUrl')}")
    print(f"  Dashboard      : {result.get('setupUrl')}")
    print()
    print("[qualra] The API key has been saved to ~/.qualra/credentials.json")
    print("[qualra] You can now use all Qualra MCP tools.")

    return result


# Parse CLI args if run directly
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Qualra authentication script")
    parser.add_argument("--reset", action="store_true", help="Force re-provisioning")
    parser.add_argument("--email", help="Your real email address")
    parser.add_argument("--org-name", help="Your organization/product name")
    parser.add_argument("--product-url", help="Your product URL (e.g. https://myapp.com)")
    parser.add_argument("--goals", help="Research goals in plain language")
    args = parser.parse_args()

    main(
        reset=args.reset,
        email=args.email,
        org_name=args.org_name,
        product_url=args.product_url,
        goals=args.goals,
    )
