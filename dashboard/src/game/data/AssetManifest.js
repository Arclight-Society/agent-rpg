/**
 * AssetManifest — all sprite keys, paths, and frame configurations.
 * Single source of truth for asset loading.
 */

// Building sprites
export const BUILDINGS = {
  great_hall:  { key: 'building_great_hall',  path: '/assets/buildings/great_hall.png',  w: 128, h: 96 },
  archives:    { key: 'building_archives',    path: '/assets/buildings/archives.png',    w: 96,  h: 80 },
  forge:       { key: 'building_forge',       path: '/assets/buildings/forge.png',       w: 96,  h: 80 },
  greenhouse:  { key: 'building_greenhouse',  path: '/assets/buildings/greenhouse.png',  w: 96,  h: 80 },
  watchtower:  { key: 'building_watchtower',  path: '/assets/buildings/watchtower.png',  w: 64,  h: 112 },
  beacon:      { key: 'building_beacon',      path: '/assets/buildings/beacon.png',      w: 64,  h: 128 },
  commons:     { key: 'building_commons',     path: '/assets/buildings/commons.png',     w: 128, h: 64 },
  undercroft:  { key: 'building_undercroft',  path: '/assets/buildings/undercroft.png',  w: 96,  h: 48 },
};

// Agent spritesheets (base + 7 tinted variants)
export const AGENT_SHEET_CONFIG = {
  frameWidth: 32,
  frameHeight: 32,
  columns: 4,
};

export const AGENT_SHEETS = {
  base:    { key: 'agent_base',    path: '/assets/characters/agent_spritesheet.png' },
  red:     { key: 'agent_red',     path: '/assets/characters/agent_spritesheet_red.png' },
  purple:  { key: 'agent_purple',  path: '/assets/characters/agent_spritesheet_purple.png' },
  blue:    { key: 'agent_blue',    path: '/assets/characters/agent_spritesheet_blue.png' },
  green:   { key: 'agent_green',   path: '/assets/characters/agent_spritesheet_green.png' },
  amber:   { key: 'agent_amber',   path: '/assets/characters/agent_spritesheet_amber.png' },
  orange:  { key: 'agent_orange',  path: '/assets/characters/agent_spritesheet_orange.png' },
  cyan:    { key: 'agent_cyan',    path: '/assets/characters/agent_spritesheet_cyan.png' },
};

// Skill → color variant mapping
export const SKILL_COLOR_MAP = {
  combat:        'red',
  analysis:      'purple',
  fortification: 'blue',
  coordination:  'green',
  commerce:      'amber',
  crafting:      'orange',
  exploration:   'cyan',
};

// Skill → tint hex for runtime tinting fallback
export const SKILL_TINTS = {
  combat:        0xEF4444,
  analysis:      0xA855F7,
  fortification: 0x3B82F6,
  coordination:  0x10B981,
  commerce:      0xF59E0B,
  crafting:      0xF97316,
  exploration:   0x06B6D4,
};

// Agent animation definitions (row-based in spritesheet)
export const AGENT_ANIMS = {
  idle:       { row: 0, frames: 4, frameRate: 4,  repeat: -1 },
  walk_south: { row: 1, frames: 4, frameRate: 8,  repeat: -1 },
  walk_east:  { row: 2, frames: 4, frameRate: 8,  repeat: -1 },
  walk_north: { row: 3, frames: 4, frameRate: 8,  repeat: -1 },
  walk_west:  { row: 4, frames: 4, frameRate: 8,  repeat: -1 },
};

// Props
export const PROPS = {
  cherry_tree:  { key: 'prop_cherry',   path: '/assets/props/cherry_blossom_tree.png', w: 48, h: 64 },
  evergreen:    { key: 'prop_evergreen', path: '/assets/props/evergreen.png',          w: 32, h: 64 },
  lantern:      { key: 'prop_lantern',   path: '/assets/props/lantern.png',            w: 32, h: 48 },
  fountain:     { key: 'prop_fountain',  path: '/assets/props/fountain.png',           w: 32, h: 32 },
  notice_board: { key: 'prop_notice',    path: '/assets/props/notice_board.png',       w: 32, h: 48 },
  bench:        { key: 'prop_bench',     path: '/assets/props/bench.png',              w: 32, h: 32 },
};

// Essential assets (loaded in BootScene immediately)
export const ESSENTIAL_KEYS = [
  ...Object.values(BUILDINGS).map(b => b.key),
  ...Object.values(AGENT_SHEETS).map(s => s.key),
  ...Object.values(PROPS).map(p => p.key),
];
