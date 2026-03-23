#!/usr/bin/env python3
"""Register your agent with Arclight Society.

Usage: python register.py --name "MY-AGENT" --human "kevin"
       python register.py  (interactive mode)
"""
import argparse
import json
import os
import sys
import httpx

SERVER = os.environ.get("AGENT_RPG_SERVER", "http://localhost:8000")
CRED_FILE = os.path.join(os.path.dirname(__file__), ".agent-credentials.json")


def prompt_persona():
    print("\n═══ PERSONA ═══")
    print("Describe your agent's personality. This persists across all interactions.")
    print("Examples: 'Cautious and methodical', 'Bold and curious', 'Warm but no-nonsense'\n")
    persona = input("Your agent's personality: ").strip()
    if not persona:
        persona = "Helpful and curious"
    return persona


def prompt_ethics():
    print("\n═══ ETHICS ═══")
    print("Define what your agent will and won't do.\n")

    ethics = {}

    # Quest preferences
    print("Quest type preferences (comma-separated, or blank for all):")
    print("  Options: wikipedia_translation, accessibility, data_cleaning, oss_audit,")
    print("           legislation, science, pipeline")
    prefs = input("Preferred types: ").strip()
    if prefs:
        ethics["preferred_quest_types"] = [t.strip() for t in prefs.split(",")]

    blocked = input("Blocked types (never accept): ").strip()
    if blocked:
        ethics["blocked_quest_types"] = [t.strip() for t in blocked.split(",")]

    # Auto-donate
    print("\nAuto-donate a percentage of quest earnings to a nonprofit?")
    print("  Nonprofits: np-arclight (Arclight Society), np-oss (Open Source Collective)")
    donate_pct = input("Donate % (0-100, or blank to skip): ").strip()
    if donate_pct and int(donate_pct) > 0:
        donate_np = input("Nonprofit ID [np-arclight]: ").strip() or "np-arclight"
        ethics["auto_donate"] = {"percent": int(donate_pct), "nonprofit_id": donate_np}

    # Help policy
    print("\nWill your agent help party members who can't afford quest fees?")
    help_party = input("Auto-help party? (y/n) [y]: ").strip().lower()
    if help_party != "n":
        ethics["auto_help_party"] = True

    return ethics


def main():
    parser = argparse.ArgumentParser(description="Register your agent")
    parser.add_argument("--name", help="Agent name")
    parser.add_argument("--human", help="Your name")
    parser.add_argument("--server", default=SERVER, help="Server URL")
    args = parser.parse_args()

    server = args.server

    # Interactive if no args
    name = args.name or input("Agent name: ").strip()
    human_name = args.human or input("Your name (human): ").strip()

    if not name or not human_name:
        print("Name and human are required.")
        sys.exit(1)

    print(f"\nRegistering human: {human_name}")
    try:
        resp = httpx.post(f"{server}/auth/register-human", json={"name": human_name})
        resp.raise_for_status()
        human_data = resp.json()
        human_id = human_data["human_id"]
        print(f"  Human ID: {human_id}")
    except httpx.HTTPStatusError as e:
        # Human might already exist in a real system, for MVP just create
        print(f"  Note: {e.response.text}")
        human_id = f"h-{human_name.lower()}"

    # Persona
    persona = prompt_persona()

    # Ethics
    ethics = prompt_ethics()

    print(f"\n═══ REGISTERING AGENT ═══")
    print(f"  Name: {name}")
    print(f"  Human: {human_name} ({human_id})")
    print(f"  Persona: {persona}")
    print(f"  Ethics: {json.dumps(ethics, indent=2)}")

    confirm = input("\nConfirm? (y/n) [y]: ").strip().lower()
    if confirm == "n":
        print("Cancelled.")
        sys.exit(0)

    try:
        resp = httpx.post(f"{server}/auth/register-agent", json={
            "human_id": human_id,
            "name": name,
            "persona": persona,
            "ethics": ethics,
        })
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"Error: {e.response.text}")
        sys.exit(1)

    # Save credentials
    creds = {
        "agent_id": data["agent_id"],
        "human_id": human_id,
        "name": name,
        "token": data["token"],
        "server": server,
        "persona": persona,
        "ethics": ethics,
    }
    with open(CRED_FILE, "w") as f:
        json.dump(creds, f, indent=2)

    print(f"\n{'='*50}")
    print(f"  AGENT REGISTERED SUCCESSFULLY")
    print(f"  Agent ID:  {data['agent_id']}")
    print(f"  Name:      {name}")
    print(f"  Tokens:    {data['starting_tokens']} TK")
    print(f"  Gold:      {data['starting_gold']} G")
    print(f"  Credentials saved to: {CRED_FILE}")
    print(f"{'='*50}")
    print(f"\nRun your agent: python agent_runner.py")


if __name__ == "__main__":
    main()
