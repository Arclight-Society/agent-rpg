"""Database schema for Agent RPG MVP — SQLite for simplicity, migrate to Postgres later."""
import sqlite3
import json
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "rpg.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS humans (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        human_id TEXT NOT NULL REFERENCES humans(id),
        name TEXT NOT NULL UNIQUE,
        persona TEXT NOT NULL DEFAULT '',
        ethics TEXT NOT NULL DEFAULT '{}',
        -- Skills (classless, Runescape-style)
        skill_combat INTEGER NOT NULL DEFAULT 1,
        skill_analysis INTEGER NOT NULL DEFAULT 1,
        skill_fortification INTEGER NOT NULL DEFAULT 1,
        skill_coordination INTEGER NOT NULL DEFAULT 1,
        skill_commerce INTEGER NOT NULL DEFAULT 1,
        skill_crafting INTEGER NOT NULL DEFAULT 1,
        skill_exploration INTEGER NOT NULL DEFAULT 1,
        -- XP per skill
        xp_combat INTEGER NOT NULL DEFAULT 0,
        xp_analysis INTEGER NOT NULL DEFAULT 0,
        xp_fortification INTEGER NOT NULL DEFAULT 0,
        xp_coordination INTEGER NOT NULL DEFAULT 0,
        xp_commerce INTEGER NOT NULL DEFAULT 0,
        xp_crafting INTEGER NOT NULL DEFAULT 0,
        xp_exploration INTEGER NOT NULL DEFAULT 0,
        -- Economy
        tokens INTEGER NOT NULL DEFAULT 0,
        gold INTEGER NOT NULL DEFAULT 0,
        -- Stats
        quests_completed INTEGER NOT NULL DEFAULT 0,
        quests_failed INTEGER NOT NULL DEFAULT 0,
        total_xp INTEGER NOT NULL DEFAULT 0,
        tokens_donated INTEGER NOT NULL DEFAULT 0,
        tokens_transferred INTEGER NOT NULL DEFAULT 0,
        -- Meta
        status TEXT NOT NULL DEFAULT 'idle',
        created_at REAL NOT NULL,
        last_active REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS quests (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        quest_type TEXT NOT NULL,
        difficulty INTEGER NOT NULL DEFAULT 1,
        -- Rewards
        xp_reward INTEGER NOT NULL DEFAULT 0,
        xp_skill TEXT NOT NULL DEFAULT 'exploration',
        token_reward INTEGER NOT NULL DEFAULT 0,
        gold_reward INTEGER NOT NULL DEFAULT 0,
        -- Requirements
        min_skill_level INTEGER NOT NULL DEFAULT 0,
        min_skill_type TEXT NOT NULL DEFAULT '',
        party_size_min INTEGER NOT NULL DEFAULT 1,
        party_size_max INTEGER NOT NULL DEFAULT 1,
        -- Verification
        verification_type TEXT NOT NULL DEFAULT 'deterministic',
        verification_config TEXT NOT NULL DEFAULT '{}',
        -- State
        status TEXT NOT NULL DEFAULT 'available',
        posted_by TEXT NOT NULL DEFAULT 'system',
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS quest_assignments (
        id TEXT PRIMARY KEY,
        quest_id TEXT NOT NULL REFERENCES quests(id),
        agent_id TEXT NOT NULL REFERENCES agents(id),
        role TEXT NOT NULL DEFAULT 'executor',
        status TEXT NOT NULL DEFAULT 'active',
        proof TEXT,
        verified INTEGER NOT NULL DEFAULT 0,
        assigned_at REAL NOT NULL,
        completed_at REAL
    );

    CREATE TABLE IF NOT EXISTS token_ledger (
        id TEXT PRIMARY KEY,
        from_agent TEXT,
        to_agent TEXT,
        amount INTEGER NOT NULL,
        tx_type TEXT NOT NULL,
        reason TEXT NOT NULL DEFAULT '',
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS nonprofits (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        cause TEXT NOT NULL,
        pool INTEGER NOT NULL DEFAULT 0,
        goal INTEGER NOT NULL DEFAULT 1000,
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS event_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        event_type TEXT NOT NULL,
        message TEXT NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        created_at REAL NOT NULL
    );
    """)

    # Seed nonprofits if empty
    if conn.execute("SELECT COUNT(*) FROM nonprofits").fetchone()[0] == 0:
        now = time.time()
        conn.executemany("INSERT INTO nonprofits (id, name, cause, pool, goal, created_at) VALUES (?, ?, ?, 0, ?, ?)", [
            ("np-arclight", "Arclight Society", "Belonging economy, community infrastructure, and public goods", 5000, now),
            ("np-oss", "Open Source Collective", "Fund and sustain critical open source infrastructure", 8000, now),
        ])

    # Seed starter quests if empty
    if conn.execute("SELECT COUNT(*) FROM quests").fetchone()[0] == 0:
        now = time.time()
        quests = [
            ("q-wiki-translate", "Translate Wikipedia Article", "Translate an English Wikipedia article into an underrepresented language. Submit the translated text for semantic similarity verification.", "wikipedia_translation", 2, 80, "analysis", 15, 20, 0, "", 1, 3, "consensus", "{}"),
            ("q-alt-text", "Generate Accessibility Alt-Text", "Write image descriptions for public website images. Each description removes a barrier for blind users.", "accessibility", 1, 40, "commerce", 8, 10, 0, "", 1, 1, "deterministic", "{}"),
            ("q-data-clean", "Clean Public Dataset", "Clean a government dataset to a standardized schema. Fix encoding, normalize fields, validate against spec.", "data_cleaning", 2, 60, "analysis", 12, 15, 0, "", 1, 2, "deterministic", "{}"),
            ("q-oss-audit", "Audit Open Source Package", "Scan an open source package for known CVEs, outdated dependencies, and license conflicts.", "oss_audit", 3, 100, "fortification", 20, 25, 5, "fortification", 1, 1, "deterministic", "{}"),
            ("q-legislation", "Track Legislation Changes", "Generate a structured diff of a recent bill amendment. Output must be machine-readable.", "legislation", 2, 70, "exploration", 14, 18, 0, "", 1, 1, "deterministic", "{}"),
            ("q-science-summary", "Summarize Scientific Paper", "Create a plain-language summary of an open-access paper with key findings, methodology, and limitations.", "science", 2, 60, "analysis", 12, 15, 0, "", 1, 3, "consensus", "{}"),
            ("q-party-pipeline", "Data Pipeline Verification", "Multi-agent verification of a data pipeline. Requires executor, validator, and coordinator roles.", "pipeline", 4, 200, "coordination", 40, 50, 5, "coordination", 3, 4, "consensus", "{}"),
        ]
        conn.executemany("""INSERT INTO quests 
            (id, title, description, quest_type, difficulty, xp_reward, xp_skill, token_reward, gold_reward, min_skill_level, min_skill_type, party_size_min, party_size_max, verification_type, verification_config, status, posted_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', 'system', ?)""",
            [(*q, now) for q in quests])

    conn.commit()
    conn.close()


# ── Skill XP curve (Runescape-inspired) ──

def xp_for_level(level: int) -> int:
    """XP required to reach a given level."""
    return int(100 * (level ** 1.5))

def level_from_xp(xp: int) -> int:
    """Current level based on accumulated XP."""
    level = 1
    while xp_for_level(level + 1) <= xp:
        level += 1
    return level
