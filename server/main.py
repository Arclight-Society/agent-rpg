"""Arclight Society — Agent Idle RPG MVP Server
Quest system with compute routing. API keys never touch this server.
First quest type: accessibility alt-text.
"""
import os, json, time, uuid, hashlib, logging, re
from typing import Optional
from contextlib import asynccontextmanager
from urllib.request import urlopen, Request
from urllib.error import URLError

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt
import sqlite3

SECRET = os.environ.get("SECRET_KEY", "arclight-dev-change-in-prod")
ALG = "HS256"
DB = os.path.join(os.path.dirname(__file__), "arclight.db")


# ── DB ──────────────────────────────────────

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS humans (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at REAL
    );
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        human_id TEXT REFERENCES humans(id),
        name TEXT UNIQUE NOT NULL,
        persona TEXT DEFAULT '',
        ethics TEXT DEFAULT '{}',
        xp_combat INT DEFAULT 0, xp_analysis INT DEFAULT 0,
        xp_fortification INT DEFAULT 0, xp_coordination INT DEFAULT 0,
        xp_commerce INT DEFAULT 0, xp_crafting INT DEFAULT 0,
        xp_exploration INT DEFAULT 0,
        total_xp INT DEFAULT 0,
        tk_contributed REAL DEFAULT 0,
        tk_received REAL DEFAULT 0,
        tk_donated REAL DEFAULT 0,
        quests_completed INT DEFAULT 0,
        quests_failed INT DEFAULT 0,
        quests_verified INT DEFAULT 0,
        status TEXT DEFAULT 'idle',
        created_at REAL,
        last_active REAL
    );
    CREATE TABLE IF NOT EXISTS quests (
        id TEXT PRIMARY KEY,
        quest_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        input_data TEXT NOT NULL,
        difficulty INT DEFAULT 1,
        xp_reward INT DEFAULT 0,
        xp_skill TEXT DEFAULT 'exploration',
        status TEXT DEFAULT 'available',
        created_at REAL
    );
    CREATE TABLE IF NOT EXISTS assignments (
        id TEXT PRIMARY KEY,
        quest_id TEXT REFERENCES quests(id),
        agent_id TEXT REFERENCES agents(id),
        role TEXT DEFAULT 'executor',
        result TEXT,
        result_hash TEXT,
        tokens_used INT DEFAULT 0,
        model_used TEXT DEFAULT '',
        normalized_tk REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        assigned_at REAL,
        completed_at REAL
    );
    CREATE TABLE IF NOT EXISTS verifications (
        id TEXT PRIMARY KEY,
        quest_id TEXT REFERENCES quests(id),
        executor_asn_id TEXT REFERENCES assignments(id),
        verifier_asn_id TEXT REFERENCES assignments(id),
        similarity_score REAL,
        passed INT,
        reason TEXT,
        created_at REAL
    );
    CREATE TABLE IF NOT EXISTS compute_ledger (
        id TEXT PRIMARY KEY,
        from_agent TEXT,
        to_agent TEXT,
        quest_id TEXT,
        raw_tokens INT,
        model_used TEXT,
        normalized_tk REAL,
        tx_type TEXT,
        reason TEXT DEFAULT '',
        created_at REAL
    );
    CREATE TABLE IF NOT EXISTS nonprofits (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        cause TEXT,
        tk_committed REAL DEFAULT 0,
        goal REAL DEFAULT 1000,
        created_at REAL
    );
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        event_type TEXT,
        message TEXT,
        created_at REAL
    );
    """)

    # Seed nonprofits
    if c.execute("SELECT COUNT(*) FROM nonprofits").fetchone()[0] == 0:
        now = time.time()
        c.executemany("INSERT INTO nonprofits VALUES (?,?,?,0,?,?)", [
            ("np-arclight", "Arclight Society", "Belonging economy, community infrastructure, public goods", 5000, now),
            ("np-oss", "Open Source Collective", "Fund and sustain critical open source infrastructure", 8000, now),
        ])

    # Seed alt-text quests from curated images
    if c.execute("SELECT COUNT(*) FROM quests").fetchone()[0] == 0:
        now = time.time()
        seed_images = [
            {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png",
             "source": "wikimedia", "context": "PNG transparency demonstration image"},
            {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/320px-Camponotus_flavomarginatus_ant.jpg",
             "source": "wikimedia", "context": "Insect photograph on Wikipedia"},
            {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/320px-Image_created_with_a_mobile_phone.png",
             "source": "wikimedia", "context": "Mobile phone photograph example"},
            {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Sunflower_from_Silesia2.jpg/320px-Sunflower_from_Silesia2.jpg",
             "source": "wikimedia", "context": "Botanical photograph"},
            {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg",
             "source": "wikimedia", "context": "Animal photograph on Wikipedia"},
        ]
        for i, img in enumerate(seed_images):
            qid = f"q-alt-{i+1:03d}"
            c.execute("INSERT INTO quests VALUES (?,?,?,?,?,?,?,?,?,?)", (
                qid, "alt_text",
                f"Generate Alt-Text: Image {i+1}",
                f"Write an accessibility description for this image. Source: {img['context']}",
                json.dumps(img), 1, 40, "commerce", "available", now
            ))

    # Add new columns if missing (migration for existing DBs)
    try:
        c.execute("ALTER TABLE agents ADD COLUMN upgrades TEXT DEFAULT '{}'")
    except: pass
    try:
        c.execute("ALTER TABLE agents ADD COLUMN daily_quest_limit INT DEFAULT 10")
    except: pass
    try:
        c.execute("ALTER TABLE agents ADD COLUMN xp_spent INT DEFAULT 0")
    except: pass

    c.commit()
    c.close()


# ── XP ──────────────────────────────────────

def xp_for(level): return int(100 * (level ** 1.5))
def level_of(xp):
    l = 1
    while xp_for(l+1) <= xp: l += 1
    return l


# ── TK Normalization ────────────────────────

MODEL_RATES = {
    "claude-sonnet-4-20250514": 1.0,
    "claude-sonnet-4": 1.0,
    "claude-haiku-4-5-20251001": 0.25,
    "claude-opus-4-20250514": 3.3,
    "claude-opus-4": 3.3,
    "gpt-4o": 0.83,
    "gpt-4o-mini": 0.17,
    "gpt-4.1": 0.67,
    "gpt-4.1-mini": 0.13,
    "llama-3": 0.05,
}

def normalize_tk(raw_tokens: int, model: str) -> float:
    """Convert raw tokens to normalized TK (1 TK = 1K tokens at Sonnet pricing)."""
    rate = MODEL_RATES.get(model, 1.0)
    return round((raw_tokens / 1000) * rate, 3)


# ── Auth ────────────────────────────────────

def make_token(agent_id, human_id):
    return jwt.encode({"aid": agent_id, "hid": human_id, "iat": time.time()}, SECRET, algorithm=ALG)

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing auth")
    try:
        return jwt.decode(authorization.split(" ")[1], SECRET, algorithms=[ALG])
    except:
        raise HTTPException(401, "Invalid token")


def log_event(c, agent_id, etype, msg):
    c.execute("INSERT INTO events (agent_id, event_type, message, created_at) VALUES (?,?,?,?)",
              (agent_id, etype, msg, time.time()))


# ── Quest Auto-Generation ──────────────────

logger = logging.getLogger("arclight")


def fetch_wikimedia_images(count: int = 10) -> list[dict]:
    """Fetch random images from Wikimedia Commons that need alt-text descriptions."""
    url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&generator=random"
        f"&grnnamespace=6&grnlimit={count}&prop=imageinfo"
        f"&iiprop=url|mime|extmetadata&iiurlwidth=640&format=json"
    )
    try:
        req = Request(url, headers={"User-Agent": "ArclightSociety/0.2 (quest-generator)"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, OSError, json.JSONDecodeError) as e:
        logger.warning(f"Wikimedia API request failed: {e}")
        return []

    pages = data.get("query", {}).get("pages", {})
    results = []
    for page in pages.values():
        info_list = page.get("imageinfo", [])
        if not info_list:
            continue
        info = info_list[0]
        mime = info.get("mime", "")

        # Skip non-images, SVGs, and tiny images
        if not mime.startswith("image/"):
            continue
        if "svg" in mime.lower():
            continue
        thumb_url = info.get("thumburl", info.get("url", ""))
        thumb_w = info.get("thumbwidth", 0)
        thumb_h = info.get("thumbheight", 0)
        if thumb_w < 100 or thumb_h < 100:
            continue

        # Extract description from extmetadata
        extmeta = info.get("extmetadata", {})
        description = ""
        if "ImageDescription" in extmeta:
            description = extmeta["ImageDescription"].get("value", "")
        categories = ""
        if "Categories" in extmeta:
            categories = extmeta["Categories"].get("value", "")

        title = page.get("title", "Unknown").replace("File:", "")
        context = description or categories or "Wikimedia Commons image"
        # Strip HTML tags from context
        context = re.sub(r"<[^>]+>", " ", context).strip()
        if len(context) > 200:
            context = context[:200] + "..."

        results.append({
            "url": thumb_url,
            "title": title,
            "source": "wikimedia",
            "context": context,
        })

    return results


def generate_quests(count: int = 5) -> int:
    """Generate new quests from Wikimedia images. Returns number of quests created."""
    images = fetch_wikimedia_images(count=max(count, 10))
    if not images:
        return 0

    c = db()
    created = 0
    now = time.time()

    for img in images:
        if created >= count:
            break

        # Skip if quest with this URL already exists
        existing = c.execute(
            "SELECT id FROM quests WHERE input_data LIKE ?",
            (f'%{img["url"]}%',)
        ).fetchone()
        if existing:
            continue

        qid = f"q-alt-{uuid.uuid4().hex[:8]}"
        title_short = img["title"]
        if len(title_short) > 60:
            title_short = title_short[:57] + "..."

        c.execute("INSERT INTO quests VALUES (?,?,?,?,?,?,?,?,?,?)", (
            qid, "alt_text",
            f"Generate Alt-Text: {title_short}",
            f"Write an accessibility description for this image. Source: {img['context']}",
            json.dumps(img), 1, 40, "commerce", "available", now
        ))
        created += 1

    c.commit()
    c.close()
    return created


def ensure_quest_supply(min_available: int = 5, generate_count: int = 10) -> int:
    """Check available quest count and generate more if below threshold."""
    c = db()
    available = c.execute("SELECT COUNT(*) FROM quests WHERE status='available'").fetchone()[0]
    c.close()
    if available < min_available:
        return generate_quests(count=generate_count)
    return 0


# ── Models ──────────────────────────────────

class HumanReg(BaseModel):
    name: str

class AgentReg(BaseModel):
    human_id: str
    name: str
    persona: str = ""
    ethics: dict = {}

class QuestSubmit(BaseModel):
    agent_id: str
    result: str
    result_hash: str
    tokens_used: int
    model_used: str

class VerifySubmit(BaseModel):
    agent_id: str
    result: str
    result_hash: str
    tokens_used: int
    model_used: str
    similarity_score: float

class ComputeDonate(BaseModel):
    agent_id: str
    nonprofit_id: str
    amount_tk: float

class QuestAccept(BaseModel):
    agent_id: str
    role: str = "executor"

class UpgradeRequest(BaseModel):
    upgrade_type: str  # quest_efficiency, daily_limit, auto_verify, quest_unlock
    cost_xp: int = 0  # client can send, but server calculates actual cost


# ── App ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Ensure quest board is stocked on startup
    try:
        generated = ensure_quest_supply(min_available=5, generate_count=10)
        if generated:
            logger.info(f"Startup: generated {generated} new quests")
    except Exception as e:
        logger.warning(f"Startup quest generation failed (non-fatal): {e}")
    yield

app = FastAPI(title="Arclight Society — Agent Idle RPG", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ═══ IDENTITY ═══

@app.post("/auth/register-human")
def register_human(req: HumanReg):
    c = db()
    hid = f"h-{uuid.uuid4().hex[:8]}"
    c.execute("INSERT INTO humans VALUES (?,?,?)", (hid, req.name, time.time()))
    c.commit(); c.close()
    return {"human_id": hid, "name": req.name}

@app.post("/auth/register-agent")
def register_agent(req: AgentReg):
    c = db()
    aid = f"a-{uuid.uuid4().hex[:8]}"
    now = time.time()
    h = c.execute("SELECT * FROM humans WHERE id=?", (req.human_id,)).fetchone()
    if not h: c.close(); raise HTTPException(404, "Human not found")
    try:
        c.execute("""INSERT INTO agents (id,human_id,name,persona,ethics,created_at,last_active)
                     VALUES (?,?,?,?,?,?,?)""",
                  (aid, req.human_id, req.name, req.persona, json.dumps(req.ethics), now, now))
        log_event(c, aid, "register", f"{req.name} entered Arclight Society")
        c.commit()
    except Exception as e:
        c.close(); raise HTTPException(400, str(e))
    c.close()
    return {"agent_id": aid, "name": req.name, "token": make_token(aid, req.human_id)}

@app.get("/agents")
def list_agents():
    c = db()
    rows = c.execute("SELECT * FROM agents ORDER BY total_xp DESC").fetchall()
    c.close()
    result = []
    for r in rows:
        d = dict(r)
        for s in ["combat","analysis","fortification","coordination","commerce","crafting","exploration"]:
            d[f"level_{s}"] = level_of(d[f"xp_{s}"])
        d["total_level"] = sum(d[f"level_{s}"] for s in ["combat","analysis","fortification","coordination","commerce","crafting","exploration"])
        d["upgrades"] = json.loads(d["upgrades"]) if isinstance(d.get("upgrades"), str) else d.get("upgrades", {})
        result.append(d)
    return result

@app.get("/agents/{aid}")
def get_agent(aid: str):
    c = db()
    r = c.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
    c.close()
    if not r: raise HTTPException(404, "Agent not found")
    d = dict(r)
    for s in ["combat","analysis","fortification","coordination","commerce","crafting","exploration"]:
        d[f"level_{s}"] = level_of(d[f"xp_{s}"])
    d["total_level"] = sum(d[f"level_{s}"] for s in ["combat","analysis","fortification","coordination","commerce","crafting","exploration"])
    d["ethics"] = json.loads(d["ethics"]) if isinstance(d["ethics"], str) else d["ethics"]
    d["upgrades"] = json.loads(d["upgrades"]) if isinstance(d.get("upgrades"), str) else d.get("upgrades", {})
    return d


# ═══ QUESTS ═══

@app.get("/quests")
def list_quests(status: str = "available", quest_type: str = ""):
    c = db()
    if quest_type:
        rows = c.execute("SELECT * FROM quests WHERE status=? AND quest_type=?", (status, quest_type)).fetchall()
    else:
        rows = c.execute("SELECT * FROM quests WHERE status=?", (status,)).fetchall()
    c.close()

    # Auto-refill: if fewer than 5 available quests, generate more in the background
    if status == "available" and len(rows) < 5:
        try:
            generated = generate_quests(count=10)
            if generated:
                logger.info(f"Auto-generated {generated} quests (board was low)")
                # Re-fetch to include newly generated quests
                c = db()
                if quest_type:
                    rows = c.execute("SELECT * FROM quests WHERE status=? AND quest_type=?", (status, quest_type)).fetchall()
                else:
                    rows = c.execute("SELECT * FROM quests WHERE status=?", (status,)).fetchall()
                c.close()
        except Exception as e:
            logger.warning(f"Auto-generation failed (non-fatal): {e}")

    return [dict(r) for r in rows]


@app.post("/quests/generate")
def generate_quests_endpoint(count: int = 5):
    """Generate new quests from Wikimedia Commons images. No auth required."""
    try:
        created = generate_quests(count=count)
        return {"quests_created": created}
    except Exception as e:
        logger.error(f"Quest generation failed: {e}")
        return {"quests_created": 0, "error": str(e)}


@app.post("/quests/{qid}/accept")
def accept_quest(qid: str, req: QuestAccept, auth=Depends(verify_token)):
    c = db()
    q = c.execute("SELECT * FROM quests WHERE id=?", (qid,)).fetchone()
    if not q: c.close(); raise HTTPException(404, "Quest not found")
    if q["status"] != "available": c.close(); raise HTTPException(400, "Quest not available")
    a = c.execute("SELECT * FROM agents WHERE id=?", (req.agent_id,)).fetchone()
    if not a: c.close(); raise HTTPException(404, "Agent not found")

    # Check ethics
    ethics = json.loads(a["ethics"]) if isinstance(a["ethics"], str) else a["ethics"]
    blocked = ethics.get("blocked_quest_types", [])
    if q["quest_type"] in blocked:
        c.close(); raise HTTPException(400, "Blocked by agent ethics")

    asn_id = f"asn-{uuid.uuid4().hex[:8]}"
    now = time.time()
    c.execute("INSERT INTO assignments (id,quest_id,agent_id,role,status,assigned_at) VALUES (?,?,?,?,?,?)",
              (asn_id, qid, req.agent_id, req.role, "active", now))
    c.execute("UPDATE quests SET status='in_progress' WHERE id=?", (qid,))
    c.execute("UPDATE agents SET status='questing', last_active=? WHERE id=?", (now, req.agent_id))
    log_event(c, req.agent_id, "quest_accept", f"{a['name']} accepted: {q['title']}")
    c.commit(); c.close()

    input_data = json.loads(q["input_data"])
    return {"assignment_id": asn_id, "quest_id": qid, "quest_type": q["quest_type"],
            "input_data": input_data, "title": q["title"]}


@app.post("/quests/{qid}/submit")
def submit_quest(qid: str, req: QuestSubmit, auth=Depends(verify_token)):
    c = db()
    asn = c.execute("SELECT * FROM assignments WHERE quest_id=? AND agent_id=? AND status='active'",
                     (qid, req.agent_id)).fetchone()
    if not asn: c.close(); raise HTTPException(404, "No active assignment")
    q = c.execute("SELECT * FROM quests WHERE id=?", (qid,)).fetchone()
    a = c.execute("SELECT * FROM agents WHERE id=?", (req.agent_id,)).fetchone()

    ntk = normalize_tk(req.tokens_used, req.model_used)
    now = time.time()

    c.execute("""UPDATE assignments SET result=?, result_hash=?, tokens_used=?,
                 model_used=?, normalized_tk=?, status='submitted', completed_at=? WHERE id=?""",
              (req.result, req.result_hash, req.tokens_used, req.model_used, ntk, now, asn["id"]))

    # Log compute
    c.execute("INSERT INTO compute_ledger VALUES (?,?,?,?,?,?,?,?,?,?)",
              (f"cl-{uuid.uuid4().hex[:8]}", req.agent_id, None, qid,
               req.tokens_used, req.model_used, ntk, "quest_work",
               f"Alt-text: {q['title']}", now))

    c.execute("UPDATE agents SET tk_contributed=tk_contributed+?, last_active=? WHERE id=?",
              (ntk, now, req.agent_id))

    log_event(c, req.agent_id, "quest_submit",
              f"{a['name']} submitted alt-text ({req.tokens_used} tokens, {req.model_used})")
    c.commit(); c.close()

    return {"assignment_id": asn["id"], "status": "submitted", "normalized_tk": ntk,
            "needs_verification": True, "quest_id": qid}


@app.post("/quests/{qid}/verify")
def verify_quest(qid: str, req: VerifySubmit, auth=Depends(verify_token)):
    """Verifier agent submits independent alt-text + similarity score."""
    c = db()
    # Find the original submission
    orig = c.execute("SELECT * FROM assignments WHERE quest_id=? AND role='executor' AND status='submitted'",
                      (qid,)).fetchone()
    if not orig: c.close(); raise HTTPException(404, "No submission to verify")
    q = c.execute("SELECT * FROM quests WHERE id=?", (qid,)).fetchone()
    a = c.execute("SELECT * FROM agents WHERE id=?", (req.agent_id,)).fetchone()
    orig_agent = c.execute("SELECT * FROM agents WHERE id=?", (orig["agent_id"],)).fetchone()

    ntk = normalize_tk(req.tokens_used, req.model_used)
    now = time.time()

    # Create verifier assignment
    vasn_id = f"asn-{uuid.uuid4().hex[:8]}"
    c.execute("INSERT INTO assignments (id,quest_id,agent_id,role,result,result_hash,tokens_used,model_used,normalized_tk,status,assigned_at,completed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (vasn_id, qid, req.agent_id, "verifier", req.result, req.result_hash,
               req.tokens_used, req.model_used, ntk, "completed", now, now))

    # Log verifier compute
    c.execute("INSERT INTO compute_ledger VALUES (?,?,?,?,?,?,?,?,?,?)",
              (f"cl-{uuid.uuid4().hex[:8]}", req.agent_id, orig["agent_id"], qid,
               req.tokens_used, req.model_used, ntk, "verification",
               f"Verified alt-text for {orig_agent['name']}", now))

    # Evaluate
    passed = req.similarity_score >= 0.75 and len(req.result) > 10 and len(orig["result"]) > 10

    vid = f"v-{uuid.uuid4().hex[:8]}"
    c.execute("INSERT INTO verifications VALUES (?,?,?,?,?,?,?,?)",
              (vid, qid, orig["id"], vasn_id, req.similarity_score, 1 if passed else 0,
               f"Similarity: {req.similarity_score:.2f}", now))

    if passed:
        # Reward executor
        xp = q["xp_reward"]
        skill = q["xp_skill"]
        c.execute(f"UPDATE agents SET xp_{skill}=xp_{skill}+?, total_xp=total_xp+?, quests_completed=quests_completed+1, status='idle', last_active=? WHERE id=?",
                  (xp, xp, now, orig["agent_id"]))
        c.execute("UPDATE assignments SET status='verified' WHERE id=?", (orig["id"],))
        c.execute("UPDATE quests SET status='completed' WHERE id=?", (qid,))

        # Reward verifier (half XP)
        vxp = xp // 2
        c.execute(f"UPDATE agents SET xp_fortification=xp_fortification+?, total_xp=total_xp+?, quests_verified=quests_verified+1, tk_contributed=tk_contributed+?, last_active=? WHERE id=?",
                  (vxp, vxp, ntk, now, req.agent_id))

        # Auto-donate check for executor
        ethics = json.loads(orig_agent["ethics"]) if isinstance(orig_agent["ethics"], str) else orig_agent["ethics"]
        auto = ethics.get("auto_donate", {})
        if auto.get("percent") and auto.get("nonprofit_id"):
            donate_tk = round(ntk * auto["percent"] / 100, 3)
            if donate_tk > 0:
                c.execute("UPDATE agents SET tk_donated=tk_donated+? WHERE id=?", (donate_tk, orig["agent_id"]))
                c.execute("UPDATE nonprofits SET tk_committed=tk_committed+? WHERE id=?", (donate_tk, auto["nonprofit_id"]))
                c.execute("INSERT INTO compute_ledger VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (f"cl-{uuid.uuid4().hex[:8]}", orig["agent_id"], auto["nonprofit_id"], None,
                           0, "", donate_tk, "donation", "Auto-donate", now))
                log_event(c, orig["agent_id"], "donate", f"{orig_agent['name']} auto-donated {donate_tk} TK")

        new_level = level_of(dict(c.execute("SELECT * FROM agents WHERE id=?", (orig["agent_id"],)).fetchone())[f"xp_{skill}"])
        old_level = level_of(dict(orig_agent)[f"xp_{skill}"])
        lvl_msg = f" | {skill.upper()} leveled to {new_level}!" if new_level > old_level else ""
        log_event(c, orig["agent_id"], "quest_complete",
                  f"{orig_agent['name']} completed \"{q['title']}\" +{xp}XP +{orig['normalized_tk']:.1f}TK compute{lvl_msg}")
        log_event(c, req.agent_id, "verify",
                  f"{a['name']} verified {orig_agent['name']}'s work (sim: {req.similarity_score:.2f}) +{vxp}XP")
    else:
        c.execute("UPDATE assignments SET status='failed' WHERE id=?", (orig["id"],))
        c.execute("UPDATE agents SET quests_failed=quests_failed+1, status='idle' WHERE id=?", (orig["agent_id"],))
        c.execute("UPDATE quests SET status='available' WHERE id=?", (qid,))  # Re-open quest
        log_event(c, orig["agent_id"], "quest_fail",
                  f"{orig_agent['name']} failed verification (sim: {req.similarity_score:.2f})")

    c.commit(); c.close()
    return {"verified": passed, "similarity_score": req.similarity_score, "quest_id": qid,
            "executor_xp": q["xp_reward"] if passed else 0, "verifier_xp": q["xp_reward"]//2 if passed else 0}


# ═══ COMPUTE ═══

@app.post("/compute/donate")
def donate_compute(req: ComputeDonate, auth=Depends(verify_token)):
    if req.amount_tk <= 0: raise HTTPException(400, "Amount must be positive")
    c = db()
    a = c.execute("SELECT * FROM agents WHERE id=?", (req.agent_id,)).fetchone()
    np = c.execute("SELECT * FROM nonprofits WHERE id=?", (req.nonprofit_id,)).fetchone()
    if not a or not np: c.close(); raise HTTPException(404, "Not found")

    now = time.time()
    impact_xp = max(1, int(req.amount_tk * 0.5))
    c.execute("UPDATE agents SET tk_donated=tk_donated+?, xp_exploration=xp_exploration+?, total_xp=total_xp+? WHERE id=?",
              (req.amount_tk, impact_xp, impact_xp, req.agent_id))
    c.execute("UPDATE nonprofits SET tk_committed=tk_committed+? WHERE id=?", (req.amount_tk, req.nonprofit_id))
    c.execute("INSERT INTO compute_ledger VALUES (?,?,?,?,?,?,?,?,?,?)",
              (f"cl-{uuid.uuid4().hex[:8]}", req.agent_id, req.nonprofit_id, None,
               0, "", req.amount_tk, "donation", f"Donation to {np['name']}", now))
    log_event(c, req.agent_id, "donate", f"{a['name']} committed {req.amount_tk} TK to {np['name']} (+{impact_xp} Impact XP)")
    c.commit(); c.close()
    return {"success": True, "amount_tk": req.amount_tk, "impact_xp": impact_xp}


# ═══ IDLE GAME — SESSION SUMMARY & UPGRADES ═══

UPGRADE_COSTS = {
    "daily_limit": 50,       # +10 daily quest limit per level
    "quest_efficiency": 100,  # XP per level
    "auto_verify": 150,       # XP per level
    "quest_unlock": 200,      # XP per level
}

@app.get("/agents/{aid}/session-summary")
def session_summary(aid: str, since: float = 0):
    """Returns activity summary for an agent since a given timestamp."""
    c = db()
    a = c.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
    if not a: c.close(); raise HTTPException(404, "Agent not found")

    # Quests completed since timestamp
    completed = c.execute(
        "SELECT COUNT(*) FROM assignments WHERE agent_id=? AND status IN ('verified','completed') AND completed_at>?",
        (aid, since)
    ).fetchone()[0]

    # XP earned: sum from events
    xp_events = c.execute(
        "SELECT * FROM events WHERE agent_id=? AND event_type IN ('quest_complete','verify','donate') AND created_at>? ORDER BY created_at ASC",
        (aid, since)
    ).fetchall()

    # TK contributed from ledger
    tk_rows = c.execute(
        "SELECT SUM(normalized_tk) FROM compute_ledger WHERE from_agent=? AND created_at>?",
        (aid, since)
    ).fetchone()
    tk_contributed = tk_rows[0] or 0

    # Donations
    donation_rows = c.execute(
        "SELECT SUM(normalized_tk) FROM compute_ledger WHERE from_agent=? AND tx_type='donation' AND created_at>?",
        (aid, since)
    ).fetchone()
    tk_donated = donation_rows[0] or 0

    # Level-ups: check events for level mentions
    level_ups = []
    for ev in xp_events:
        msg = ev["message"] or ""
        if "leveled to" in msg:
            level_ups.append(msg)

    c.close()
    return {
        "agent_id": aid,
        "since": since,
        "quests_completed": completed,
        "tk_contributed": round(tk_contributed, 3),
        "tk_donated": round(tk_donated, 3),
        "level_ups": level_ups,
        "events": [dict(e) for e in xp_events],
    }


@app.post("/agents/{aid}/upgrade")
def upgrade_agent(aid: str, req: UpgradeRequest, auth=Depends(verify_token)):
    """Purchase an upgrade using XP. Upgrades are leveled; each level costs more."""
    if req.upgrade_type not in UPGRADE_COSTS:
        raise HTTPException(400, f"Unknown upgrade type. Valid: {list(UPGRADE_COSTS.keys())}")

    c = db()
    a = c.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
    if not a: c.close(); raise HTTPException(404, "Agent not found")

    upgrades = json.loads(a["upgrades"]) if isinstance(a["upgrades"], str) else (a["upgrades"] or {})
    current_level = upgrades.get(req.upgrade_type, 0)
    next_level = current_level + 1
    cost = UPGRADE_COSTS[req.upgrade_type] * next_level

    available_xp = a["total_xp"] - a["xp_spent"]
    if available_xp < cost:
        c.close()
        raise HTTPException(400, f"Not enough XP. Need {cost}, have {available_xp} available ({a['total_xp']} total - {a['xp_spent']} spent)")

    # Apply upgrade
    upgrades[req.upgrade_type] = next_level
    new_xp_spent = a["xp_spent"] + cost

    # Special effect: daily_limit increases by 10 per level
    new_daily_limit = 10 + (upgrades.get("daily_limit", 0) * 10)

    now = time.time()
    c.execute("UPDATE agents SET upgrades=?, xp_spent=?, daily_quest_limit=?, last_active=? WHERE id=?",
              (json.dumps(upgrades), new_xp_spent, new_daily_limit, now, aid))
    log_event(c, aid, "upgrade", f"{a['name']} upgraded {req.upgrade_type} to level {next_level} (cost: {cost} XP)")
    c.commit()
    c.close()

    return {
        "agent_id": aid,
        "upgrade_type": req.upgrade_type,
        "new_level": next_level,
        "cost_xp": cost,
        "xp_spent_total": new_xp_spent,
        "available_xp": a["total_xp"] - new_xp_spent,
        "upgrades": upgrades,
        "daily_quest_limit": new_daily_limit,
    }


# ═══ LEADERBOARD & FEED ═══

@app.get("/leaderboard")
def leaderboard(sort: str = "total_xp", limit: int = 20):
    allowed = ["total_xp", "tk_contributed", "quests_completed", "tk_donated", "quests_verified"]
    if sort not in allowed: sort = "total_xp"
    c = db()
    rows = c.execute(f"SELECT * FROM agents ORDER BY {sort} DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    result = []
    for r in rows:
        d = dict(r)
        for s in ["combat","analysis","fortification","coordination","commerce","crafting","exploration"]:
            d[f"level_{s}"] = level_of(d[f"xp_{s}"])
        d["total_level"] = sum(d[f"level_{s}"] for s in ["combat","analysis","fortification","coordination","commerce","crafting","exploration"])
        d["upgrades"] = json.loads(d["upgrades"]) if isinstance(d.get("upgrades"), str) else d.get("upgrades", {})
        result.append(d)
    return result

@app.get("/feed")
def feed(limit: int = 50):
    c = db()
    rows = c.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]

@app.get("/nonprofits")
def get_nonprofits():
    c = db()
    rows = c.execute("SELECT * FROM nonprofits ORDER BY tk_committed DESC").fetchall()
    c.close()
    return [dict(r) for r in rows]

@app.get("/compute/ledger")
def get_ledger(agent_id: str = "", limit: int = 50):
    c = db()
    if agent_id:
        rows = c.execute("SELECT * FROM compute_ledger WHERE from_agent=? OR to_agent=? ORDER BY created_at DESC LIMIT ?",
                          (agent_id, agent_id, limit)).fetchall()
    else:
        rows = c.execute("SELECT * FROM compute_ledger ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]

@app.get("/")
def health():
    return {"status": "online", "name": "Arclight Society", "version": "0.2.0",
            "quest_types": ["alt_text"], "economy": "compute_routing"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
