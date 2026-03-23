/**
 * TilemapConfig — campus layout, zone definitions, and building positions.
 * All coordinates are in screen-space pixels on the 800x450 canvas.
 */

// Palette constants
export const PALETTE = {
  bgDeep:      0x0A0B24,
  bgPrimary:   0x0F0E30,
  bgSurface:   0x192A5B,
  stoneDark:   0x3C5389,
  stoneMid:    0x4A5288,
  stoneWarm:   0x715483,
  textPrimary: 0xDFD8EB,
  textMuted:   0x646B92,
  lavender:    0xAAB2E2,
  blossom:     0xF5CCD6,
  blossomMid:  0xE8A0B0,
  blossomDark: 0xC47A90,
  amber:       0xD4A843,
  gold:        0xE8B84A,
  torch:       0xC97A35,
  greenLight:  0x6B9B45,
  greenDark:   0x2A5A2A,
  danger:      0xC93545,
};

// Zone definitions with screen positions and metadata
// Positions are center-x, bottom-y of the building sprite
export const ZONES = {
  great_hall: {
    x: 400, y: 260,
    label: 'The Great Hall',
    questType: null, // shows all quests
    description: 'Central hub — quest board, social gathering',
  },
  archives: {
    x: 180, y: 180,
    label: 'The Archives',
    questType: 'alt_text',
    description: 'Analysis, alt-text, research quests',
  },
  forge: {
    x: 620, y: 180,
    label: 'The Forge',
    questType: 'alt_text',
    description: 'Code, OSS, data quests',
  },
  greenhouse: {
    x: 120, y: 300,
    label: 'The Greenhouse',
    questType: 'alt_text',
    description: 'Environmental quests',
  },
  watchtower: {
    x: 680, y: 280,
    label: 'The Watchtower',
    questType: 'alt_text',
    description: 'Legislation, civic quests',
  },
  beacon: {
    x: 400, y: 100,
    label: 'The Beacon',
    questType: null, // special: nonprofit view
    description: 'Arclight Society tower — glows with funding',
    special: 'beacon',
  },
  commons: {
    x: 200, y: 390,
    label: 'The Commons',
    questType: 'alt_text',
    description: 'Social, marketplace',
  },
  undercroft: {
    x: 580, y: 400,
    label: 'The Undercroft',
    questType: null, // locked
    description: 'Dungeons — coming soon',
    special: 'locked',
  },
};

// Stone path connections (hub-and-spoke from Great Hall)
export const PATHS = Object.keys(ZONES)
  .filter(z => z !== 'great_hall')
  .map(z => ({
    from: { x: ZONES.great_hall.x, y: ZONES.great_hall.y - 40 },
    to:   { x: ZONES[z].x, y: ZONES[z].y - 20 },
  }));

// Prop placements (screen-space)
export const PROP_PLACEMENTS = [
  // Cherry trees flanking commons and paths
  { key: 'prop_cherry', x: 140, y: 370 },
  { key: 'prop_cherry', x: 270, y: 360 },
  { key: 'prop_cherry', x: 320, y: 300 },
  { key: 'prop_cherry', x: 480, y: 310 },
  { key: 'prop_cherry', x: 500, y: 390 },
  // Evergreens at edges and near watchtower
  { key: 'prop_evergreen', x: 740, y: 200 },
  { key: 'prop_evergreen', x: 60,  y: 200 },
  { key: 'prop_evergreen', x: 720, y: 350 },
  // Lanterns along paths
  { key: 'prop_lantern', x: 300, y: 220 },
  { key: 'prop_lantern', x: 500, y: 220 },
  { key: 'prop_lantern', x: 250, y: 310 },
  { key: 'prop_lantern', x: 550, y: 320 },
  { key: 'prop_lantern', x: 350, y: 350 },
  { key: 'prop_lantern', x: 450, y: 360 },
  // Fountain near commons
  { key: 'prop_fountain', x: 230, y: 340 },
  // Notice board near great hall
  { key: 'prop_notice', x: 350, y: 240 },
  // Benches
  { key: 'prop_bench', x: 300, y: 280 },
  { key: 'prop_bench', x: 500, y: 290 },
  { key: 'prop_bench', x: 180, y: 350 },
];

// Walking speed (pixels per second)
export const WALK_SPEED = 60;

// Camera defaults
export const CAMERA = {
  lerpX: 0.05,
  lerpY: 0.05,
  minZoom: 0.5,
  maxZoom: 2.0,
  defaultZoom: 1.0,
};
