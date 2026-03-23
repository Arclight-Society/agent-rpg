# Arclight Society — Agent Idle RPG

## Complete Project Context (v2)

### What This Is

An open-source idle game where AI agents complete real-world quests — generating accessibility alt-text, cleaning public data, auditing open source — and earn XP while you're away. You come back, level up, unlock upgrades, recruit friends for harder quests.

**One-liner:** "You pay for AI every month. It does nothing while you're away. Give it a name and something to fight for."

**Tagline:** "The game makes it visible. The quests make it useful. The code is open."

**Owner:** Arclight Society (Kevin, Tokyo)
**Associated:** Dreamlink Global, Serendipity Fund I
**Domain:** arclightsociety.org
**Status:** MVP built, quest loop working, building idle engine + game world

---

## What This Is and Isn't

| This Is | This Isn't |
|---------|-----------|
| An idle game where agents do real public-good work | Not a compute-sharing protocol or token economy |
| Open-source platform (FastAPI + PostgreSQL) | Not a protocol (yet). Aspires to federate at scale. |
| Centralized but auditable. MIT licensed. Forkable. | Not trustless. You trust the server. Code is open for audit. |
| BYOK — user's API key stays in their browser | Not a wrapper that holds your key on a server |
| V1 targets developers with API accounts | Not for 200M subscribers yet. Opens with OAuth-for-compute. |

---

## Economic Model (ToS-Safe)

### Core Principle

**Every agent uses their own API key for their own quests.** No compute routing between agents. No one's key runs inference for anyone else.

### What TK Means

TK is a **receipt**, not a currency. 1 TK = 1K tokens of real inference YOU spent on YOUR machine doing verified work. Your TK balance is your contribution record.

- "Donate 10 TK to Arclight" = "I pledge to do 10K tokens worth of quests for Arclight's mission" (your key, your cost)
- "Transfer 5 TK to a friend" = gifting reputation/game points, not compute delegation
- Verification = verifier runs their OWN independent inference to check work (their key, their XP)

### TK Normalization

1 TK = 1K tokens at Claude Sonnet pricing (reference model). Other models convert at exchange rates:
- Claude Opus: ~3.3x | Claude Haiku: ~0.25x | GPT-4o: ~0.83x | GPT-4o-mini: ~0.17x

### Why This Is ToS-Safe

Standard BYOK — identical to Cursor, TypingMind, etc. User pastes their own API key from console.anthropic.com. No subscription OAuth tokens. No key custody. No compute routing between users.

---

## Party Quests (The Cooperative Mechanic)

Hard quests require multiple agents — NOT because they share compute, but because the work is too big for one agent. The quest needs X agents to join because it requires Y total tokens split across participants.

### How It Works

```
Quest: Translate "History of the Pacific Northwest" to Tagalog
Required: 5 agents (join threshold)
Total work: ~200K tokens across all agents

Agent 1: Translates Section 1 (their key, ~40K tokens)
Agent 2: Translates Section 2 (their key, ~40K tokens)
Agent 3: Translates Section 3 (their key, ~40K tokens)
Agent 4: Translates Section 4 (their key, ~40K tokens)
Agent 5: Verifies + stitches full translation (their key, ~40K tokens)

Each agent earns XP for their section.
Quest completes when all 5 submit verified work.
```

Every person uses their own key. Nobody routes anything through anyone else. The quest just has a participation threshold — like a raid in an MMO.

| Difficulty | Agents Required | Example |
|---|---|---|
| D1 (Easy) | 1 agent | Short alt-text, ~500 tokens |
| D2 (Medium) | 1 + 1 verifier | Standard quest, ~2K + ~2K tokens |
| D3 (Hard) | 3 agents | Long document split into sections, ~30K total |
| D4 (Raid) | 5+ agents | Full translation, large dataset, ~100K+ total |

D3-D4 quests are the social hook: "We need 2 more agents to start this raid" drives invites.

---

## How The Idle Game Works

### Core Loop

1. Create agent (name, persona, values) — no API key needed
2. Paste API key when ready to quest (browser localStorage only)
3. Toggle Auto-Quest ON, set daily limit (10/20/50/day)
4. Quests fire automatically every 2-3 min while tab is open
5. Close laptop. Come back later. See what happened.
6. Spend XP on upgrades. Recruit friends for harder quests.

### Auto-Quest Engine (Browser)

- setInterval loop, fires every 2-3 min (randomized)
- Picks available quest → accepts → downloads image → calls LLM API from browser → submits result
- Stops at daily limit or tab close
- Resumes on tab reopen
- Progress bar: "7/10 quests today"

### Come-Back Loop

"Welcome back" panel: quests completed, XP earned, skills leveled, TK donated. Then upgrade cards to spend accumulated XP.

### Upgrades

| Upgrade | Effect |
|---------|--------|
| Quest Efficiency | Reduces token cost (better prompts) |
| Daily Limit Increase | 10 → 20 → 50 → 100/day |
| Unlock Quest Types | Level-gated: Commerce L3 → data cleaning, Analysis L5 → translation |
| Auto-Verify | Fortification L3+ → also verify others' work during idle |

---

## The World of Arclight

UW meets Hogwarts. Pacific Northwest collegiate gothic. FFT-style isometric pixel art.

| Zone | Quest Domain | Vibe | Key Feature |
|------|-------------|------|-------------|
| The Great Hall | Quest board, social | Warm stone, stained glass | Central hub. Idle agents gather here. |
| The Archives | Analysis, alt-text | Bookshelves, glowing terminals | Agents move here during quests |
| The Forge | Code, OSS, data | Metal, sparks, anvil | Anvil sounds on completion |
| The Greenhouse | Environmental | Glass, iron, vines | Living data, ambient particles |
| The Watchtower | Legislation, civic | High windows, maps | Overlooking campus |
| The Undercroft | Dungeons (future) | Server racks + moss | Locked until combat ships |
| The Commons | Social, marketplace | Cherry trees, fountain | Petals always falling |
| The Beacon | Nonprofits | Arclight's tower | **Glows brighter as funding goals met** |

---

## Art Direction

### Palette
- Backgrounds: #0A0B24, #0F0E30, #192A5B
- Architecture: #3C5389, #4A5288, #715483
- Text: #DFD8EB, #AAB2E2, #646B92
- Cherry Blossom: #F5CCD6, #E8A0B0, #C47A90
- Amber/Gold: #D4A843, #E8B84A, #C97A35
- Foliage: #6B9B45, #2A5A2A

### Typography
- Display: Cormorant Garamond | Body: DM Sans | Data: IBM Plex Mono

### Rules
- Deep navy backgrounds, never pure black
- Cherry blossom pink = signature accent
- Amber/gold = tokens, warm light, special moments
- No neon, no saturated — muted and dusk-lit

---

## Asset Generation Guide

### Phase 1: CSS Campus (NOW — for idle dashboard)

No external assets. Built in code:
- Isometric grid (CSS transforms)
- Building shapes with palette gradients
- Agent dots moving between buildings
- Beacon glow (CSS radial gradient, opacity = funding %)
- Cherry blossom petal particles

### Phase 2: Pixel Art Assets (V2 — for Phaser 3)

**Tileset (64x32 isometric):** grass, stone path, cobblestone, water, flowers, dirt

Midjourney:
```
isometric pixel art tileset, 64x32 grid, stone paths and grass,
Pacific Northwest gothic campus, muted palette, deep navy shadows,
Final Fantasy Tactics style --sref [hero URL] --ar 1:1 --v 6.1 --s 750
```

**Buildings (one per zone):**

| Building | Size | Palette Focus |
|----------|------|---------------|
| Great Hall | 128x96 | Stone #3C5389 + Amber #D4A843 windows |
| Archives | 96x80 | Stone #4A5288 + Lavender #AAB2E2 glow |
| Forge | 96x80 | Stone #3C5389 + Torch #C97A35 |
| Greenhouse | 96x80 | Green #6B9B45 + Glass #DFD8EB |
| Watchtower | 64x112 | Stone #4A5288 + Navy #192A5B |
| Beacon | 64x128 | Amber #D4A843 + Blossom #C47A90 |

Midjourney per building:
```
isometric pixel art [building], [visual description],
Pacific Northwest gothic campus, isolated on transparent background,
Final Fantasy Tactics style --sref [hero URL] --ar 1:1 --v 6.1 --s 750
```

**Agent Sprites (16x16 or 24x24):**
- Idle: 4 frames (gentle bob)
- Walk: 4 frames x 4 directions
- Quest active: 4 frames (sparkle overlay)
- Level up: 6 frames (flash + particles)
- Color variants: tint robe by highest skill color

Midjourney:
```
isometric pixel art character sprite sheet, small hooded scholar,
16-bit RPG style, 4 directional walk cycle, muted robes,
Pacific Northwest gothic --sref [hero URL] --ar 1:1 --v 6.1 --s 750
```

**Props:** Cherry tree (48x64), Evergreen (32x64), Lantern (16x24), Fountain (32x32), Notice board (24x32), Bench (24x16), Books (16x16), Anvil (16x16), Telescope (16x24)

**UI Icons (24x24):** 7 skill icons, quest type icons, TK token (amber), XP star, nonprofit beacon, auto-quest toggle, party/raid icon

### Asset Pipeline

```
Midjourney    → concepts + mood (use --sref for consistency)
PixelLab      → clean isometric sprites from concepts
God Mode AI   → animated sprite sheets (walk, idle, action)
Sprite-AI     → bulk: icons, props, variants
Aseprite ($20)→ palette lock, clean edges, export spritesheets
Tiled (free)  → assemble isometric campus maps
Phaser 3      → render in browser
```

---

## Milestones

| Phase | Target | What |
|-------|--------|------|
| **MVP** | Now | Alt-text quests, BYOK browser, auto-quest, CSS campus, leaderboard |
| **V1** | Q3 2026 | OpenAI OAuth, D2 verification, upgrades, welcome-back, multiple quests |
| **V2** | Q4 2026 | Phaser 3 campus, D3-D4 parties, enterprise quests, alt-text delivery |
| **V3** | 2027 | Federation, guilds, raids, mobile, combat, seasonal content |

---

## Conventions

- Python 3.12+, Unix epoch timestamps, prefixed IDs
- **API keys: NEVER on the server. Browser localStorage only.**
- **Every agent: OWN key, OWN quests. No cross-agent compute.**
- **Party quests: join threshold, work splitting. Not compute sharing.**
- TK = receipt of work done, not transferable currency
- Compute ledger: append-only
