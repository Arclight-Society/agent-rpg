# Phaser 3 Isometric Campus — Design Spec

**Date:** 2026-03-24
**Status:** Approved
**Scope:** Replace CSS campus view with Phaser 3 isometric game client embedded in React dashboard

---

## Overview

Embed a Phaser 3 canvas inside the existing React dashboard, replacing the CSS campus box. The canvas renders an isometric pixel art campus with 8 buildings, animated agents, props, and cherry blossom particles. Clicking a building updates the React dashboard below to show that zone's data.

## Architecture

```
React Dashboard (App.jsx)
  ├── Phaser Container <div> (replaces CSS campus)
  │     └── CampusScene (single Phaser scene)
  │           ├── Tilemap layer (isometric ground)
  │           ├── Building layer (8 sprites, clickable)
  │           ├── Props layer (trees, lanterns, fountain, benches)
  │           ├── Agent layer (character sprites, auto-animated)
  │           ├── Particle layer (cherry blossom petals)
  │           └── UI layer (hover labels, click highlights)
  ├── Dashboard tabs (skills, quests, leaderboard, etc.)
  └── Quest controls (API key, auto-quest toggle)
```

### Data Flow

- **React → Phaser**: Agent data, quest state, auto-quest status passed on mount and via polling (5s interval, matching existing dashboard polling)
- **Phaser → React**: Emits `building-click` event with zone ID. React updates active tab/filter to show that zone's quests and agents.
- **Phaser makes NO API calls.** React owns all data fetching.

### Communication

```js
// React → Phaser: update game state
game.events.emit('update-agents', agentList);
game.events.emit('update-quests', questState);
game.events.emit('agent-quest-start', { agentId, zone });
game.events.emit('agent-quest-complete', { agentId, xp });

// Phaser → React: building interaction
game.events.on('building-click', ({ zone }) => {
  setActiveTab('quests');
  setZoneFilter(zone);
});
```

## Scene: CampusScene

### No Tilemap — Screen-Space Placement

Buildings and props are placed using screen-space pixel coordinates on a 400x400 canvas, NOT an isometric tilemap grid. The ground is a single pre-rendered or painted background (dark navy #0A0B24 base with stone path lines drawn as simple graphics). This avoids the complexity of isometric tile math and keeps the campus feeling hand-crafted.

**Ground rendering:**
- Canvas fill: #0A0B24
- Stone paths: drawn as 3-4px wide lines (#4A5288) connecting buildings to center (hub-and-spoke)
- Grass patches: small clusters of green pixels (#2A5A2A, #6B9B45) scattered around edges
- Cobblestone areas: small rectangles under each building foundation

This is simpler than a tilemap, renders faster, and the individual tile PNGs remain available for a future tilemap-based V2 if needed.

### Buildings (8 sprites)

Radial layout — Great Hall at center, others arranged around it. Positions are screen-space pixel coordinates (anchor = bottom-center of sprite):

| Building | Screen Position (x, y) | Size | Click Action |
|----------|----------------------|------|-------------|
| Great Hall | (200, 220) | 128x96 | Show: all quests (clear zone filter) |
| Archives | (80, 140) | 96x80 | Filter: alt_text quests |
| Forge | (320, 140) | 96x80 | Filter: alt_text quests |
| Greenhouse | (60, 230) | 96x80 | Filter: alt_text quests |
| Watchtower | (340, 230) | 64x112 | Filter: alt_text quests |
| Beacon | (200, 80) | 64x128 | Show: nonprofit funding progress |
| Commons | (90, 330) | 128x64 | Filter: alt_text quests |
| Undercroft | (200, 370) | 96x48 | Show: locked (future dungeons) |

**Note on quest filtering:** The server currently only has one quest type (`alt_text`). All building click filters resolve to the same query for now. When new quest types ship (translation, data cleaning, etc.), update the zone-to-quest-type mapping in `constants.js`:

```js
// constants.js — update as quest types are added
export const ZONE_QUEST_MAP = {
  great_hall: null,        // show all (clear filter)
  archives:  'alt_text',   // → future: 'analysis'
  forge:     'alt_text',   // → future: 'code_review'
  greenhouse:'alt_text',   // → future: 'environmental'
  watchtower:'alt_text',   // → future: 'legislation'
  beacon:    null,         // special: nonprofit view
  commons:   'alt_text',   // → future: 'social'
  undercroft: null,        // special: locked
};
```

Stone paths connect each building to the Great Hall (hub-and-spoke), drawn as Phaser Graphics lines.

### Building Interactions

- **Hit areas**: Each building has an invisible interactive rectangle larger than its sprite (minimum 48x48px at base resolution) to ensure mobile tap targets are usable even for smaller buildings like Undercroft.
- **Hover** (desktop): Building name label fades in above the building. Subtle brightness increase (tint shift).
- **Click/tap**: Brief glow pulse animation. Emits `building-click` event to React. Visual indicator (e.g., subtle outline) shows which building is selected.
- **Undercroft special**: Dimmed, slight green glow. Click shows "Coming soon — dungeons" in React panel.
- **Commons/Beacon**: Commons click filters quests. Beacon click shows nonprofit funding panel (not quest filter).

### Beacon Special Effect

- Data source: React passes nonprofit data via `game.events.emit('update-nonprofits', nonprofits)`. Use the first nonprofit (Arclight Society, np-1) for the Beacon glow.
- Glow intensity = `nonprofits[0].tk_committed / nonprofits[0].goal`
- Implemented as: amber-tinted circle sprite with `blendMode: Phaser.BlendModes.ADD`, alpha animated between `0.2 + (0.6 * intensity)` and `0.4 + (0.6 * intensity)`
- Animates slowly (pulsing glow, 3s tween cycle)
- At 0%: dim, barely visible. At 100%: bright amber radiating outward

### Props (Decorative)

Scattered across campus for atmosphere:

- Cherry blossom trees (4-6): flanking Commons, along paths
- Evergreens (3-4): campus edges, near Watchtower
- Lanterns (6-8): along stone paths, warm amber glow sprites
- Fountain (1): near Commons area
- Notice board (1): near Great Hall entrance
- Benches (3-4): along paths

Props are non-interactive. Depth-sorted with buildings and agents.

### Agents

- **My agent**: Load the pre-tinted spritesheet PNG matching the agent's highest skill color (e.g., `agent_spritesheet_purple.png` for analysis). Use `variants.json` `skill_color_map` to look up which variant file to use. No runtime tinting needed.
- **Other agents**: Same approach — load the appropriate pre-tinted spritesheet for each agent's top skill. Rendered at slightly lower alpha (0.8) to visually distinguish from my agent.
- **Idle behavior**: Agents at their current zone play idle animation (4 frames, 4 FPS bob)
- **Quest movement**: When auto-quest fires, agent plays walk animation along path from current zone to quest zone, then switches to idle at destination
- **Quest complete**: Particle burst (amber sparkles) at agent position, +XP text floats up and fades

### Agent Placement

- Agents cluster near their current zone's building
- Slight random offset so they don't stack perfectly
- My agent is always rendered on top (highest depth) with a subtle glow/indicator

### Particles

- **Cherry blossom petals**: Phaser particle emitter, continuous, covers outdoor areas
  - Texture: generate a 4x4 pink circle at runtime via `this.make.graphics()` → `generateTexture('petal', 4, 4)`
  - Pink palette colors (#F5CCD6, #E8A0B0, #C47A90) — randomize tint per particle
  - Slow drift downward + slight horizontal sway
  - ~15-20 particles visible at any time
  - Alpha: 0.3-0.6, lifespan: 4000-6000ms
- **Quest complete sparkles**: Burst emitter, amber (#D4A843, #E8B84A), 10-15 particles, fast fade

## Canvas & Sizing

- **Aspect ratio**: 1:1 square
- **Base resolution**: 400x400 (renders the full campus)
- **Scaling**: `Phaser.Scale.FIT` — fills container width, maintains ratio
- **Rendering**: `pixelArt: true` in Phaser config (nearest-neighbor scaling, no bilinear blur)
- **Round pixels**: `roundPixels: true` for crisp pixel art at all scale factors
- **Container**: Replaces the existing CSS campus `<div>` in Dashboard component
- **Mobile (375px)**: Canvas renders at 375x375, buildings ~40-60px wide, tappable
- **Desktop**: Canvas up to ~600x600, capped by dashboard layout max-width

## File Structure

```
agent-rpg/
├── dashboard/
│   ├── public/
│   │   └── assets/              # Copy of game assets (served as static files by Vite)
│   │       ├── buildings/       # 8 building PNGs
│   │       ├── characters/      # Spritesheets + variants + JSON
│   │       ├── tiles/           # Tileset PNG + JSON (reserved for future)
│   │       ├── props/           # 6 prop PNGs
│   │       └── ui/              # Icon atlas + individual PNGs
│   ├── src/
│   │   ├── App.jsx              # Modified: mount Phaser, handle events
│   │   ├── game/
│   │   │   ├── config.js        # Phaser game config (pixelArt: true, scale, parent)
│   │   │   ├── CampusScene.js   # Main scene (buildings, agents, particles, ground)
│   │   │   └── constants.js     # Zone positions, palette, animation defs, quest map
│   │   └── ...
│   └── package.json             # Add phaser dependency
├── assets/                      # Source assets (generated by PixelLab)
```

**Asset serving strategy:** Copy assets into `dashboard/public/assets/` so Vite serves them as static files. Phaser loads them via `this.load.image('great_hall', '/assets/buildings/great_hall.png')`. The source-of-truth originals stay in the root `assets/` directory.

### React Lifecycle

- Game instance created in a `useEffect` with cleanup: `return () => game.destroy(true)`
- Use a `useRef` to track if game is already created (prevents React 18 StrictMode double-mount)
- Game ref stored for event communication
- Event listeners cleaned up in the same `useEffect` cleanup

```jsx
const gameRef = useRef(null);
const containerRef = useRef(null);

useEffect(() => {
  if (gameRef.current) return; // prevent StrictMode double-init
  const game = new Phaser.Game({ ...config, parent: containerRef.current });
  gameRef.current = game;

  game.events.on('building-click', handleBuildingClick);

  return () => {
    game.events.off('building-click', handleBuildingClick);
    game.destroy(true);
    gameRef.current = null;
  };
}, []);
```

## Dependencies

- `phaser`: ^3.80.0 (latest stable)
- No other new dependencies

## Integration with React

### Mounting

```jsx
// In Dashboard component, replace <Campus /> with:
<div id="phaser-campus" style={{ width: '100%', aspectRatio: '1/1', maxWidth: 600 }} />
```

Phaser game instance created on Dashboard mount, destroyed on unmount. Game reference stored in React ref for event communication.

### Zone Filter Sync

When Phaser emits `building-click`:
1. React sets `activeZone` state
2. Quest list filters to that zone's quest types
3. Agent list filters to agents currently at that zone
4. A "clear filter" option returns to showing all

### Existing Dashboard Changes

- Remove `Campus` component (CSS version, lines ~366-460)
- Add Phaser mount point in its place
- Add `activeZone` state and zone-based filtering to quest/agent lists
- Pass game state updates to Phaser via bridge

## Out of Scope (Future)

- Combat system
- Inventory / items
- Player-controlled movement (click-to-walk)
- Camera controls (zoom/pan)
- Building interiors
- Sound effects / music
- WebSocket real-time updates (currently polling)
- Multiple map areas
- Day/night cycle
