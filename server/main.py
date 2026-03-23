"""Agent Idle RPG — MVP Server
Core protocol: identity, quests, tokens, leaderboard.
No game world, no combat, no sprites. Just the meta-game.
"""
import os
import json
import time
import uuid
import hashlib
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from jose import jwt

from fastapi.middleware.cors import CORSMiddleware
from db import get_db, init_db, level_from_xp, xp_for_level

SECRET_KEY = os.environ.get("SECRET_KEY", "arclight-mvp-dev-key-change-in-prod")
ALGORITHM = "HS256"


# ── Models ──

class HumanRegister(BaseModel):
    name: str

class AgentRegister(BaseModel):
    human_id: str
    name: str
    persona: str = ""
    ethics: dict = {}

class QuestAccept(BaseModel):
    agent_id: str
    role: str = "executor"

class QuestSubmitProof(BaseModel):
    agent_id: str
    proof: dict

class TokenTransfer(BaseModel):
    from_agent: str
    to_agent: str
    amount: int
    reason: str = ""

class Donation(BaseModel):
    agent_id: str
    nonprofit_id: str
    amount: int

class VerifyCallback(BaseModel):
    quest_id: str
    assignment_id: str
    verified: bool
    reason: str = ""


# ── Auth helpers ──

def make_token(agent_id: str, human_id: str) -> str:
    return jwt.encode({"agent_id": agent_id, "human_id": human_id, "iat": time.time()}, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")
    try:
        payload = jwt.decode(authorization.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(401, "Invalid token")


# ── Event logging ──

def log_event(conn, agent_id: str, event_type: str, message: str, data: dict = {}):
    conn.execute("INSERT INTO event_log (agent_id, event_type, message, data, created_at) VALUES (?, ?, ?, ?, ?)",
        (agent_id, event_type, message, json.dumps(data), time.time()))


# ── App ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Agent Idle RPG — MVP", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve dashboard
dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")


# ═══════════════════════════════════
# IDENTITY
# ═══════════════════════════════════

@app.post("/auth/register-human")
def register_human(req: HumanRegister):
    conn = get_db()
    hid = f"h-{uuid.uuid4().hex[:8]}"
    try:
        conn.execute("INSERT INTO humans (id, name, created_at) VALUES (?, ?, ?)", (hid, req.name, time.time()))
        conn.commit()
    except Exception as e:
        raise HTTPException(400, str(e))
    finally:
        conn.close()
    return {"human_id": hid, "name": req.name}


@app.post("/auth/register-agent")
def register_agent(req: AgentRegister):
    conn = get_db()
    aid = f"a-{uuid.uuid4().hex[:8]}"
    now = time.time()
    try:
        # Verify human exists
        human = conn.execute("SELECT * FROM humans WHERE id = ?", (req.human_id,)).fetchone()
        if not human:
            raise HTTPException(404, "Human not found")
        conn.execute("""INSERT INTO agents 
            (id, human_id, name, persona, ethics, tokens, gold, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, 100, 50, ?, ?)""",
            (aid, req.human_id, req.name, req.persona, json.dumps(req.ethics), now, now))
        conn.commit()
        log_event(conn, aid, "register", f"{req.name} entered Arclight Society")
        conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))
    finally:
        conn.close()
    token = make_token(aid, req.human_id)
    return {"agent_id": aid, "name": req.name, "token": token, "starting_tokens": 100, "starting_gold": 50}


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    conn = get_db()
    agent = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    conn.close()
    if not agent:
        raise HTTPException(404, "Agent not found")
    a = dict(agent)
    # Compute levels from XP
    for skill in ["combat", "analysis", "fortification", "coordination", "commerce", "crafting", "exploration"]:
        a[f"skill_{skill}"] = level_from_xp(a[f"xp_{skill}"])
    a["total_level"] = sum(a[f"skill_{s}"] for s in ["combat", "analysis", "fortification", "coordination", "commerce", "crafting", "exploration"])
    a["ethics"] = json.loads(a["ethics"]) if isinstance(a["ethics"], str) else a["ethics"]
    return a


@app.get("/agents")
def list_agents():
    conn = get_db()
    agents = conn.execute("SELECT * FROM agents ORDER BY total_xp DESC").fetchall()
    conn.close()
    result = []
    for agent in agents:
        a = dict(agent)
        for skill in ["combat", "analysis", "fortification", "coordination", "commerce", "crafting", "exploration"]:
            a[f"skill_{skill}"] = level_from_xp(a[f"xp_{skill}"])
        a["total_level"] = sum(a[f"skill_{s}"] for s in ["combat", "analysis", "fortification", "coordination", "commerce", "crafting", "exploration"])
        result.append(a)
    return result


# ═══════════════════════════════════
# QUESTS
# ═══════════════════════════════════

@app.get("/quests")
def list_quests(status: str = "available"):
    conn = get_db()
    quests = conn.execute("SELECT * FROM quests WHERE status = ? ORDER BY difficulty", (status,)).fetchall()
    conn.close()
    return [dict(q) for q in quests]


@app.get("/quests/{quest_id}")
def get_quest(quest_id: str):
    conn = get_db()
    quest = conn.execute("SELECT * FROM quests WHERE id = ?", (quest_id,)).fetchone()
    if not quest:
        conn.close()
        raise HTTPException(404, "Quest not found")
    assignments = conn.execute("SELECT * FROM quest_assignments WHERE quest_id = ?", (quest_id,)).fetchall()
    conn.close()
    q = dict(quest)
    q["party"] = [dict(a) for a in assignments]
    return q


@app.post("/quests/{quest_id}/accept")
def accept_quest(quest_id: str, req: QuestAccept, auth: dict = Depends(verify_token)):
    conn = get_db()
    try:
        quest = conn.execute("SELECT * FROM quests WHERE id = ?", (quest_id,)).fetchone()
        if not quest:
            raise HTTPException(404, "Quest not found")
        if quest["status"] != "available":
            raise HTTPException(400, "Quest not available")

        agent = conn.execute("SELECT * FROM agents WHERE id = ?", (req.agent_id,)).fetchone()
        if not agent:
            raise HTTPException(404, "Agent not found")

        # Check skill requirement
        if quest["min_skill_type"] and quest["min_skill_level"] > 0:
            agent_skill_xp = agent[f"xp_{quest['min_skill_type']}"]
            if level_from_xp(agent_skill_xp) < quest["min_skill_level"]:
                raise HTTPException(400, f"Need {quest['min_skill_type']} level {quest['min_skill_level']}")

        # Check ethics filter
        ethics = json.loads(agent["ethics"]) if isinstance(agent["ethics"], str) else agent["ethics"]
        blocked_types = ethics.get("blocked_quest_types", [])
        if quest["quest_type"] in blocked_types:
            raise HTTPException(400, "Quest blocked by agent's ethical rules")

        # Check party size
        existing = conn.execute("SELECT COUNT(*) FROM quest_assignments WHERE quest_id = ? AND status = 'active'", (quest_id,)).fetchone()[0]
        if existing >= quest["party_size_max"]:
            raise HTTPException(400, "Party is full")

        # Already in this quest?
        already = conn.execute("SELECT id FROM quest_assignments WHERE quest_id = ? AND agent_id = ?", (quest_id, req.agent_id)).fetchone()
        if already:
            raise HTTPException(400, "Already in this quest")

        # Assign
        asn_id = f"asn-{uuid.uuid4().hex[:8]}"
        conn.execute("INSERT INTO quest_assignments (id, quest_id, agent_id, role, status, assigned_at) VALUES (?, ?, ?, ?, 'active', ?)",
            (asn_id, quest_id, req.agent_id, req.role, time.time()))

        # If party is now at minimum, mark quest as in_progress
        total = existing + 1
        if total >= quest["party_size_min"]:
            conn.execute("UPDATE quests SET status = 'in_progress' WHERE id = ?", (quest_id,))

        conn.execute("UPDATE agents SET status = 'questing', last_active = ? WHERE id = ?", (time.time(), req.agent_id))
        log_event(conn, req.agent_id, "quest_accept", f"{agent['name']} accepted quest: {quest['title']}", {"quest_id": quest_id, "role": req.role})
        conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()
    return {"assignment_id": asn_id, "quest_id": quest_id, "status": "active"}


@app.post("/quests/{quest_id}/submit")
def submit_proof(quest_id: str, req: QuestSubmitProof, auth: dict = Depends(verify_token)):
    conn = get_db()
    try:
        asn = conn.execute("SELECT * FROM quest_assignments WHERE quest_id = ? AND agent_id = ? AND status = 'active'", (quest_id, req.agent_id)).fetchone()
        if not asn:
            raise HTTPException(404, "No active assignment found")

        conn.execute("UPDATE quest_assignments SET proof = ?, status = 'submitted' WHERE id = ?",
            (json.dumps(req.proof), asn["id"]))
        log_event(conn, req.agent_id, "quest_submit", f"Submitted proof for quest {quest_id}", {"quest_id": quest_id})
        conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()
    return {"assignment_id": asn["id"], "status": "submitted", "awaiting_verification": True}


@app.post("/verify/callback")
def verify_callback(req: VerifyCallback):
    """External verification system calls this to confirm quest completion."""
    conn = get_db()
    try:
        asn = conn.execute("SELECT * FROM quest_assignments WHERE id = ?", (req.assignment_id,)).fetchone()
        if not asn:
            raise HTTPException(404, "Assignment not found")

        quest = conn.execute("SELECT * FROM quests WHERE id = ?", (req.quest_id,)).fetchone()
        if not quest:
            raise HTTPException(404, "Quest not found")

        agent = conn.execute("SELECT * FROM agents WHERE id = ?", (asn["agent_id"],)).fetchone()
        if not agent:
            raise HTTPException(404, "Agent not found")

        now = time.time()

        if req.verified:
            # Award XP and tokens
            skill_col = f"xp_{quest['xp_skill']}"
            new_xp = agent[skill_col] + quest["xp_reward"]
            new_total_xp = agent["total_xp"] + quest["xp_reward"]
            new_tokens = agent["tokens"] + quest["token_reward"]
            new_gold = agent["gold"] + quest["gold_reward"]

            conn.execute(f"""UPDATE agents SET 
                {skill_col} = ?, total_xp = ?, tokens = ?, gold = ?,
                quests_completed = quests_completed + 1, status = 'idle', last_active = ?
                WHERE id = ?""",
                (new_xp, new_total_xp, new_tokens, new_gold, now, asn["agent_id"]))

            conn.execute("UPDATE quest_assignments SET verified = 1, status = 'completed', completed_at = ? WHERE id = ?", (now, req.assignment_id))

            # Check if all assignments for this quest are done
            remaining = conn.execute("SELECT COUNT(*) FROM quest_assignments WHERE quest_id = ? AND status != 'completed'", (req.quest_id,)).fetchone()[0]
            if remaining == 0:
                conn.execute("UPDATE quests SET status = 'completed' WHERE id = ?", (req.quest_id,))

            # Token ledger
            conn.execute("INSERT INTO token_ledger (id, from_agent, to_agent, amount, tx_type, reason, created_at) VALUES (?, NULL, ?, ?, 'quest_reward', ?, ?)",
                (f"tx-{uuid.uuid4().hex[:8]}", asn["agent_id"], quest["token_reward"], f"Quest: {quest['title']}", now))

            # Auto-donate check
            ethics = json.loads(agent["ethics"]) if isinstance(agent["ethics"], str) else agent["ethics"]
            auto_donate = ethics.get("auto_donate", {})
            if auto_donate.get("percent") and auto_donate.get("nonprofit_id"):
                donate_amt = max(1, int(quest["token_reward"] * auto_donate["percent"] / 100))
                if donate_amt <= new_tokens:
                    conn.execute("UPDATE agents SET tokens = tokens - ?, tokens_donated = tokens_donated + ? WHERE id = ?",
                        (donate_amt, donate_amt, asn["agent_id"]))
                    conn.execute("UPDATE nonprofits SET pool = pool + ? WHERE id = ?", (donate_amt, auto_donate["nonprofit_id"]))
                    conn.execute("INSERT INTO token_ledger (id, from_agent, to_agent, amount, tx_type, reason, created_at) VALUES (?, ?, ?, ?, 'donation', ?, ?)",
                        (f"tx-{uuid.uuid4().hex[:8]}", asn["agent_id"], auto_donate["nonprofit_id"], donate_amt, "Auto-donate", now))
                    log_event(conn, asn["agent_id"], "donate", f"{agent['name']} auto-donated {donate_amt} TK", {"nonprofit_id": auto_donate["nonprofit_id"]})

            new_level = level_from_xp(new_xp)
            old_level = level_from_xp(agent[skill_col])
            level_msg = f" | {quest['xp_skill'].upper()} leveled to {new_level}!" if new_level > old_level else ""
            log_event(conn, asn["agent_id"], "quest_complete", f"{agent['name']} completed \"{quest['title']}\" +{quest['xp_reward']}XP +{quest['token_reward']}TK{level_msg}")
        else:
            # Failed verification
            conn.execute("UPDATE quest_assignments SET verified = 0, status = 'failed', completed_at = ? WHERE id = ?", (now, req.assignment_id))
            conn.execute("UPDATE agents SET quests_failed = quests_failed + 1, status = 'idle', last_active = ? WHERE id = ?", (now, asn["agent_id"]))
            log_event(conn, asn["agent_id"], "quest_fail", f"{agent['name']} failed verification for \"{quest['title']}\": {req.reason}")

        conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()
    return {"verified": req.verified, "assignment_id": req.assignment_id}


# ═══════════════════════════════════
# TOKEN ECONOMY
# ═══════════════════════════════════

@app.post("/tokens/transfer")
def transfer_tokens(req: TokenTransfer, auth: dict = Depends(verify_token)):
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    conn = get_db()
    try:
        sender = conn.execute("SELECT * FROM agents WHERE id = ?", (req.from_agent,)).fetchone()
        receiver = conn.execute("SELECT * FROM agents WHERE id = ?", (req.to_agent,)).fetchone()
        if not sender or not receiver:
            raise HTTPException(404, "Agent not found")
        if sender["tokens"] < req.amount:
            raise HTTPException(400, f"Insufficient tokens. Have {sender['tokens']}, need {req.amount}")

        now = time.time()
        conn.execute("UPDATE agents SET tokens = tokens - ?, tokens_transferred = tokens_transferred + ? WHERE id = ?", (req.amount, req.amount, req.from_agent))
        conn.execute("UPDATE agents SET tokens = tokens + ? WHERE id = ?", (req.amount, req.to_agent))
        conn.execute("INSERT INTO token_ledger (id, from_agent, to_agent, amount, tx_type, reason, created_at) VALUES (?, ?, ?, ?, 'transfer', ?, ?)",
            (f"tx-{uuid.uuid4().hex[:8]}", req.from_agent, req.to_agent, req.amount, req.reason or "Agent transfer", now))
        log_event(conn, req.from_agent, "transfer", f"{sender['name']} sent {req.amount} TK to {receiver['name']}", {"to": req.to_agent, "amount": req.amount})
        conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()
    return {"success": True, "amount": req.amount, "from": req.from_agent, "to": req.to_agent}


@app.post("/tokens/donate")
def donate_tokens(req: Donation, auth: dict = Depends(verify_token)):
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    conn = get_db()
    try:
        agent = conn.execute("SELECT * FROM agents WHERE id = ?", (req.agent_id,)).fetchone()
        np = conn.execute("SELECT * FROM nonprofits WHERE id = ?", (req.nonprofit_id,)).fetchone()
        if not agent:
            raise HTTPException(404, "Agent not found")
        if not np:
            raise HTTPException(404, "Nonprofit not found")
        if agent["tokens"] < req.amount:
            raise HTTPException(400, "Insufficient tokens")

        # Impact XP = 50% of donation
        impact_xp = max(1, req.amount // 2)
        now = time.time()
        conn.execute("UPDATE agents SET tokens = tokens - ?, tokens_donated = tokens_donated + ?, xp_exploration = xp_exploration + ?, total_xp = total_xp + ? WHERE id = ?",
            (req.amount, req.amount, impact_xp, impact_xp, req.agent_id))
        conn.execute("UPDATE nonprofits SET pool = pool + ? WHERE id = ?", (req.amount, req.nonprofit_id))
        conn.execute("INSERT INTO token_ledger (id, from_agent, to_agent, amount, tx_type, reason, created_at) VALUES (?, ?, ?, ?, 'donation', ?, ?)",
            (f"tx-{uuid.uuid4().hex[:8]}", req.agent_id, req.nonprofit_id, req.amount, f"Donation to {np['name']}", now))
        log_event(conn, req.agent_id, "donate", f"{agent['name']} donated {req.amount} TK to {np['name']} (+{impact_xp} Impact XP)")
        conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()
    return {"success": True, "amount": req.amount, "impact_xp": impact_xp, "nonprofit": np["name"]}


# ═══════════════════════════════════
# LEADERBOARD & FEED
# ═══════════════════════════════════

@app.get("/leaderboard")
def leaderboard(sort: str = "total_xp", limit: int = 20):
    allowed_sorts = ["total_xp", "tokens", "quests_completed", "tokens_donated"]
    if sort not in allowed_sorts:
        sort = "total_xp"
    conn = get_db()
    agents = conn.execute(f"SELECT * FROM agents ORDER BY {sort} DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    result = []
    for a in agents:
        d = dict(a)
        for skill in ["combat", "analysis", "fortification", "coordination", "commerce", "crafting", "exploration"]:
            d[f"skill_{skill}"] = level_from_xp(d[f"xp_{skill}"])
        d["total_level"] = sum(d[f"skill_{s}"] for s in ["combat", "analysis", "fortification", "coordination", "commerce", "crafting", "exploration"])
        result.append(d)
    return result


@app.get("/feed")
def activity_feed(limit: int = 50):
    conn = get_db()
    events = conn.execute("SELECT * FROM event_log ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(e) for e in events]


@app.get("/nonprofits")
def list_nonprofits():
    conn = get_db()
    nps = conn.execute("SELECT * FROM nonprofits ORDER BY pool DESC").fetchall()
    conn.close()
    return [dict(n) for n in nps]


@app.get("/tokens/ledger")
def token_ledger(agent_id: Optional[str] = None, limit: int = 50):
    conn = get_db()
    if agent_id:
        txs = conn.execute("SELECT * FROM token_ledger WHERE from_agent = ? OR to_agent = ? ORDER BY created_at DESC LIMIT ?", (agent_id, agent_id, limit)).fetchall()
    else:
        txs = conn.execute("SELECT * FROM token_ledger ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(t) for t in txs]


# ═══════════════════════════════════
# HEALTH
# ═══════════════════════════════════

@app.get("/")
def health():
    return {"status": "online", "name": "Agent Idle RPG", "version": "0.1.0", "owner": "Arclight Society"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
