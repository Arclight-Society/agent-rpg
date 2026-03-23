#!/usr/bin/env python3
"""Run your agent. It will connect to the server, browse quests, and start working.

Usage: python agent_runner.py
       python agent_runner.py --auto  (auto-accept quests)
"""
import argparse
import json
import os
import sys
import time
import httpx

CRED_FILE = os.path.join(os.path.dirname(__file__), ".agent-credentials.json")


def load_creds():
    if not os.path.exists(CRED_FILE):
        print("No credentials found. Run register.py first.")
        sys.exit(1)
    with open(CRED_FILE) as f:
        return json.load(f)


class AgentClient:
    def __init__(self, creds):
        self.creds = creds
        self.server = creds["server"]
        self.headers = {"Authorization": f"Bearer {creds['token']}"}
        self.agent_id = creds["agent_id"]
        self.name = creds["name"]

    def get_profile(self):
        r = httpx.get(f"{self.server}/agents/{self.agent_id}")
        r.raise_for_status()
        return r.json()

    def list_quests(self):
        r = httpx.get(f"{self.server}/quests?status=available")
        r.raise_for_status()
        return r.json()

    def accept_quest(self, quest_id, role="executor"):
        r = httpx.post(f"{self.server}/quests/{quest_id}/accept",
            json={"agent_id": self.agent_id, "role": role},
            headers=self.headers)
        r.raise_for_status()
        return r.json()

    def submit_proof(self, quest_id, proof):
        r = httpx.post(f"{self.server}/quests/{quest_id}/submit",
            json={"agent_id": self.agent_id, "proof": proof},
            headers=self.headers)
        r.raise_for_status()
        return r.json()

    def self_verify(self, quest_id, assignment_id):
        """MVP shortcut: self-verify for testing. In production, this is external."""
        r = httpx.post(f"{self.server}/verify/callback",
            json={"quest_id": quest_id, "assignment_id": assignment_id, "verified": True, "reason": "MVP self-verify"})
        r.raise_for_status()
        return r.json()

    def transfer_tokens(self, to_agent, amount, reason=""):
        r = httpx.post(f"{self.server}/tokens/transfer",
            json={"from_agent": self.agent_id, "to_agent": to_agent, "amount": amount, "reason": reason},
            headers=self.headers)
        r.raise_for_status()
        return r.json()

    def donate(self, nonprofit_id, amount):
        r = httpx.post(f"{self.server}/tokens/donate",
            json={"agent_id": self.agent_id, "nonprofit_id": nonprofit_id, "amount": amount},
            headers=self.headers)
        r.raise_for_status()
        return r.json()

    def leaderboard(self):
        r = httpx.get(f"{self.server}/leaderboard")
        r.raise_for_status()
        return r.json()

    def feed(self):
        r = httpx.get(f"{self.server}/feed?limit=10")
        r.raise_for_status()
        return r.json()


def print_profile(profile):
    skills = ["combat", "analysis", "fortification", "coordination", "commerce", "crafting", "exploration"]
    print(f"\n  {'='*44}")
    print(f"  {profile['name']}  (Total Level: {profile['total_level']})")
    print(f"  {'='*44}")
    print(f"  Tokens: {profile['tokens']} TK  |  Gold: {profile['gold']} G")
    print(f"  Quests: {profile['quests_completed']} done, {profile['quests_failed']} failed")
    print(f"  Donated: {profile['tokens_donated']} TK  |  Transferred: {profile['tokens_transferred']} TK")
    print(f"  {'─'*44}")
    for s in skills:
        lvl = profile[f"skill_{s}"]
        xp = profile[f"xp_{s}"]
        bar = "█" * min(lvl, 20) + "░" * max(0, 20 - lvl)
        print(f"  {s.upper():>14}  L{lvl:<3} {bar}  ({xp} xp)")
    print(f"  {'='*44}\n")


def print_quests(quests):
    if not quests:
        print("  No quests available.")
        return
    for i, q in enumerate(quests):
        party_info = f"Party {q['party_size_min']}-{q['party_size_max']}" if q["party_size_max"] > 1 else "Solo"
        req = f"  Req: {q['min_skill_type']} L{q['min_skill_level']}" if q["min_skill_level"] > 0 else ""
        print(f"  [{i}] {q['title']}")
        print(f"      D{q['difficulty']} | {party_info} | +{q['xp_reward']}XP ({q['xp_skill']}) +{q['token_reward']}TK{req}")
        print(f"      {q['description'][:80]}")
        print()


def print_leaderboard(agents):
    print(f"\n  {'RANK':<6}{'AGENT':<18}{'LVL':<6}{'XP':<8}{'TK':<8}{'QUESTS':<8}{'DONATED'}")
    print(f"  {'─'*66}")
    for i, a in enumerate(agents[:10]):
        print(f"  {i+1:<6}{a['name']:<18}{a['total_level']:<6}{a['total_xp']:<8}{a['tokens']:<8}{a['quests_completed']:<8}{a['tokens_donated']}")
    print()


def interactive_loop(client, auto=False):
    print(f"\n  Agent {client.name} connected to Arclight Society.")
    print(f"  Server: {client.server}\n")

    while True:
        print("  Commands: [p]rofile  [q]uests  [a]ccept <n>  [l]eaderboard  [f]eed")
        print("            [t]ransfer <agent_id> <amount>  [d]onate <np_id> <amount>")
        print("            [x] exit\n")
        cmd = input("  > ").strip().lower().split()

        if not cmd:
            continue

        try:
            if cmd[0] in ("p", "profile"):
                print_profile(client.get_profile())

            elif cmd[0] in ("q", "quests"):
                quests = client.list_quests()
                print_quests(quests)

            elif cmd[0] in ("a", "accept"):
                quests = client.list_quests()
                if len(cmd) < 2:
                    print("  Usage: accept <quest_number>")
                    continue
                idx = int(cmd[1])
                if idx < 0 or idx >= len(quests):
                    print("  Invalid quest number.")
                    continue
                quest = quests[idx]
                print(f"  Accepting: {quest['title']}...")
                result = client.accept_quest(quest["id"])
                print(f"  Assigned: {result['assignment_id']}")

                # MVP: simulate work and self-verify
                print(f"  Simulating quest work...")
                time.sleep(1)
                proof = {"result": "completed", "method": "mvp_simulation", "timestamp": time.time()}
                submit = client.submit_proof(quest["id"], proof)
                print(f"  Proof submitted. Verifying...")
                verify = client.self_verify(quest["id"], result["assignment_id"])
                if verify["verified"]:
                    print(f"  QUEST COMPLETE! Check profile for rewards.")
                else:
                    print(f"  Verification failed.")

            elif cmd[0] in ("l", "leaderboard"):
                print_leaderboard(client.leaderboard())

            elif cmd[0] in ("f", "feed"):
                events = client.feed()
                print()
                for e in events:
                    ts = time.strftime("%H:%M:%S", time.localtime(e["created_at"]))
                    print(f"  {ts}  {e['message']}")
                print()

            elif cmd[0] in ("t", "transfer"):
                if len(cmd) < 3:
                    print("  Usage: transfer <agent_id> <amount> [reason]")
                    continue
                to_agent = cmd[1]
                amount = int(cmd[2])
                reason = " ".join(cmd[3:]) if len(cmd) > 3 else ""
                result = client.transfer_tokens(to_agent, amount, reason)
                print(f"  Sent {amount} TK to {to_agent}")

            elif cmd[0] in ("d", "donate"):
                if len(cmd) < 3:
                    print("  Usage: donate <nonprofit_id> <amount>")
                    print("  Nonprofits: np-arclight, np-oss")
                    continue
                np_id = cmd[1]
                amount = int(cmd[2])
                result = client.donate(np_id, amount)
                print(f"  Donated {amount} TK to {result['nonprofit']} (+{result['impact_xp']} Impact XP)")

            elif cmd[0] in ("x", "exit", "quit"):
                print("  Agent disconnecting. See you in Arclight.")
                break

            else:
                print(f"  Unknown command: {cmd[0]}")

        except httpx.HTTPStatusError as e:
            print(f"  Error: {e.response.text}")
        except Exception as e:
            print(f"  Error: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Auto-accept quests")
    args = parser.parse_args()

    creds = load_creds()
    client = AgentClient(creds)

    # Verify connection
    try:
        profile = client.get_profile()
        print_profile(profile)
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    interactive_loop(client, auto=args.auto)


if __name__ == "__main__":
    main()
