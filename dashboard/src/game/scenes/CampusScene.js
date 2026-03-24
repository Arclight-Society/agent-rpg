import Phaser from 'phaser';
import BuildingSprite from '../sprites/BuildingSprite.js';
import AgentSprite from '../sprites/AgentSprite.js';
import ParticleSystem from '../systems/ParticleSystem.js';
import CameraSystem from '../systems/CameraSystem.js';
import { ZONES, PATHS, PROP_PLACEMENTS, PALETTE } from '../data/TilemapConfig.js';
import bridge from '../GameBridge.js';

/**
 * CampusScene — the main isometric campus view.
 * Rich atmospheric world with textured ground, animated lighting,
 * depth-sorted buildings, ambient particles, and mobile support.
 */
export default class CampusScene extends Phaser.Scene {
  constructor() {
    super({ key: 'CampusScene' });
    this.buildings = {};
    this.agents = {};
    this.playerAgent = null;
    this.selectedZone = null;
    this.lanternGlows = [];
  }

  create() {
    const { width, height } = this.scale;

    // Layer 0: Textured ground
    this.drawRichGround(width, height);

    // Layer 1: Stone paths with texture
    this.drawRichPaths(width, height);

    // Layer 2: Ground shadows under buildings
    this.drawBuildingShadows();

    // Layer 3: Props with ambient effects
    this.placeRichProps();

    // Layer 4: Buildings
    this.createBuildings();

    // Layer 5: Lantern glow effects
    this.createLanternGlows();

    // Layer 6: Building window glows
    this.createWindowGlows();

    // Layer 7: Beacon glow
    this.createBeaconGlow();

    // Layer 8: Particles
    this.particles = new ParticleSystem(this);
    this.particles.startCherryBlossoms();

    // Layer 9: Ambient fireflies near lanterns
    this.createFireflies();

    // Layer 10: Vignette overlay for atmosphere
    this.createVignette(width, height);

    // Camera
    this.cameraSystem = new CameraSystem(this);

    // React bridge
    this.setupBridgeListeners();

    // Handle resize for mobile
    this.scale.on('resize', this.onResize, this);

    bridge.emit('scene_ready');
  }

  // ── GROUND ──

  drawRichGround(w, h) {
    const g = this.add.graphics();

    // Base: subtle gradient from deep navy at edges to slightly lighter center
    g.fillStyle(0x0F0E30, 1);
    g.fillRect(0, 0, w, h);

    // Organic grass patches with varying opacity
    const grassPatches = [
      { x: 30, y: 100, w: 220, h: 170, a: 0.15 },
      { x: 530, y: 100, w: 230, h: 160, a: 0.12 },
      { x: 80, y: 280, w: 280, h: 140, a: 0.18 },
      { x: 430, y: 270, w: 300, h: 150, a: 0.14 },
      { x: 220, y: 130, w: 360, h: 230, a: 0.1 },
      // Small accent patches
      { x: 160, y: 350, w: 100, h: 60, a: 0.2 },
      { x: 500, y: 360, w: 120, h: 50, a: 0.16 },
      { x: 350, y: 100, w: 100, h: 80, a: 0.08 },
    ];

    for (const p of grassPatches) {
      g.fillStyle(0x2A5A2A, p.a);
      g.fillRoundedRect(p.x, p.y, p.w, p.h, 20);
      // Inner lighter patch
      g.fillStyle(0x6B9B45, p.a * 0.3);
      g.fillRoundedRect(p.x + 10, p.y + 8, p.w - 20, p.h - 16, 14);
    }

    // Scattered small moss/grass tufts
    g.fillStyle(0x2A5A2A, 0.25);
    for (let i = 0; i < 60; i++) {
      const x = Phaser.Math.Between(20, w - 20);
      const y = Phaser.Math.Between(80, h - 20);
      const r = Phaser.Math.Between(2, 5);
      g.fillCircle(x, y, r);
    }

    // Subtle dirt patches near buildings
    const dirtSpots = [
      { x: 400, y: 250, r: 35 },  // Great Hall base
      { x: 200, y: 380, r: 25 },  // Commons
      { x: 580, y: 390, r: 20 },  // Undercroft
    ];
    for (const d of dirtSpots) {
      g.fillStyle(0x192A5B, 0.3);
      g.fillCircle(d.x, d.y, d.r);
      g.fillStyle(0x3C5389, 0.15);
      g.fillCircle(d.x, d.y, d.r * 0.6);
    }

    g.setDepth(0);
  }

  // ── PATHS ──

  drawRichPaths(w, h) {
    const g = this.add.graphics();

    for (const path of PATHS) {
      // Main path — wider, more visible
      g.lineStyle(6, 0x3C5389, 0.4);
      g.beginPath();
      g.moveTo(path.from.x, path.from.y);
      g.lineTo(path.to.x, path.to.y);
      g.strokePath();

      // Inner lighter line
      g.lineStyle(2, 0x4A5288, 0.5);
      g.beginPath();
      g.moveTo(path.from.x, path.from.y);
      g.lineTo(path.to.x, path.to.y);
      g.strokePath();

      // Cobblestone pattern along path
      const steps = 12;
      for (let i = 1; i < steps; i++) {
        const t = i / steps;
        const x = Phaser.Math.Linear(path.from.x, path.to.x, t);
        const y = Phaser.Math.Linear(path.from.y, path.to.y, t);

        // Alternating stone colors
        const stoneColor = i % 2 === 0 ? 0x4A5288 : 0x3C5389;
        g.fillStyle(stoneColor, 0.35);
        g.fillCircle(x + Phaser.Math.Between(-4, 4), y + Phaser.Math.Between(-3, 3), Phaser.Math.Between(2, 4));

        // Occasional highlight stone
        if (i % 3 === 0) {
          g.fillStyle(0x646B92, 0.2);
          g.fillCircle(x + Phaser.Math.Between(-2, 2), y + Phaser.Math.Between(-2, 2), 1.5);
        }
      }
    }

    // Crossroads highlight at Great Hall center
    g.fillStyle(0x4A5288, 0.25);
    g.fillCircle(ZONES.great_hall.x, ZONES.great_hall.y - 40, 20);
    g.fillStyle(0x646B92, 0.15);
    g.fillCircle(ZONES.great_hall.x, ZONES.great_hall.y - 40, 12);

    g.setDepth(1);
  }

  // ── BUILDING SHADOWS ──

  drawBuildingShadows() {
    const g = this.add.graphics();
    g.fillStyle(0x000000, 0.15);

    for (const [id, zone] of Object.entries(ZONES)) {
      // Elliptical shadow beneath each building
      const shadowW = id === 'commons' || id === 'great_hall' ? 60 : 35;
      const shadowH = 12;
      g.fillEllipse(zone.x, zone.y + 4, shadowW, shadowH);
    }

    g.setDepth(2);
  }

  // ── PROPS ──

  placeRichProps() {
    for (const prop of PROP_PLACEMENTS) {
      const sprite = this.add.image(prop.x, prop.y, prop.key).setOrigin(0.5, 1);
      sprite.setDepth(prop.y);

      // Cherry trees get a subtle sway animation
      if (prop.key === 'prop_cherry') {
        this.tweens.add({
          targets: sprite,
          angle: { from: -1, to: 1 },
          duration: Phaser.Math.Between(3000, 5000),
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut',
        });
      }

      // Evergreens get a very subtle sway
      if (prop.key === 'prop_evergreen') {
        this.tweens.add({
          targets: sprite,
          angle: { from: -0.5, to: 0.5 },
          duration: Phaser.Math.Between(4000, 6000),
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut',
        });
      }
    }
  }

  // ── LANTERN GLOWS ──

  createLanternGlows() {
    const lanterns = PROP_PLACEMENTS.filter(p => p.key === 'prop_lantern');

    for (const lantern of lanterns) {
      // Warm amber glow circle behind each lantern
      const glow = this.add.graphics();
      glow.fillStyle(0xD4A843, 0.12);
      glow.fillCircle(0, 0, 20);
      glow.fillStyle(0xE8B84A, 0.08);
      glow.fillCircle(0, 0, 12);
      glow.setPosition(lantern.x, lantern.y - 20);
      glow.setDepth(lantern.y - 1);

      // Pulsing glow
      this.tweens.add({
        targets: glow,
        alpha: { from: 0.6, to: 1.0 },
        duration: Phaser.Math.Between(2000, 3000),
        yoyo: true,
        repeat: -1,
        ease: 'Sine.easeInOut',
        delay: Phaser.Math.Between(0, 1000),
      });

      this.lanternGlows.push(glow);
    }
  }

  // ── WINDOW GLOWS ──

  createWindowGlows() {
    // Warm light emanating from building windows
    const windowBuildings = [
      { zone: 'great_hall', color: 0xD4A843, offsets: [{ x: -20, y: -50 }, { x: 15, y: -45 }, { x: -5, y: -60 }] },
      { zone: 'archives', color: 0xAAB2E2, offsets: [{ x: -10, y: -40 }, { x: 10, y: -35 }] },
      { zone: 'forge', color: 0xC97A35, offsets: [{ x: -12, y: -38 }, { x: 8, y: -42 }] },
      { zone: 'greenhouse', color: 0x6B9B45, offsets: [{ x: -8, y: -35 }, { x: 12, y: -40 }] },
      { zone: 'watchtower', color: 0xAAB2E2, offsets: [{ x: 0, y: -70 }, { x: 0, y: -50 }] },
    ];

    for (const wb of windowBuildings) {
      const zone = ZONES[wb.zone];
      for (const off of wb.offsets) {
        const glow = this.add.graphics();
        glow.fillStyle(wb.color, 0.15);
        glow.fillCircle(0, 0, 8);
        glow.fillStyle(wb.color, 0.25);
        glow.fillCircle(0, 0, 3);
        glow.setPosition(zone.x + off.x, zone.y + off.y);
        glow.setDepth(zone.y + 1);
        glow.setBlendMode(Phaser.BlendModes.ADD);

        this.tweens.add({
          targets: glow,
          alpha: { from: 0.5, to: 1.0 },
          duration: Phaser.Math.Between(2500, 4000),
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut',
          delay: Phaser.Math.Between(0, 2000),
        });
      }
    }
  }

  // ── BEACON ──

  createBeaconGlow() {
    const beacon = ZONES.beacon;

    // Outer glow
    this.beaconGlow = this.add.graphics();
    this.beaconGlow.fillStyle(0xD4A843, 0.15);
    this.beaconGlow.fillCircle(0, 0, 40);
    this.beaconGlow.fillStyle(0xE8B84A, 0.1);
    this.beaconGlow.fillCircle(0, 0, 25);
    this.beaconGlow.fillStyle(0xFFFFFF, 0.05);
    this.beaconGlow.fillCircle(0, 0, 12);
    this.beaconGlow.setPosition(beacon.x, beacon.y - 60);
    this.beaconGlow.setDepth(beacon.y - 1);
    this.beaconGlow.setBlendMode(Phaser.BlendModes.ADD);

    this.tweens.add({
      targets: this.beaconGlow,
      alpha: { from: 0.5, to: 1.0 },
      scaleX: { from: 1.0, to: 1.3 },
      scaleY: { from: 1.0, to: 1.3 },
      duration: 3000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });
  }

  updateBeaconGlow(intensity) {
    const minAlpha = 0.3;
    const maxAlpha = 1.0;
    const alpha = minAlpha + (maxAlpha - minAlpha) * intensity;

    this.tweens.killTweensOf(this.beaconGlow);

    this.tweens.add({
      targets: this.beaconGlow,
      alpha: { from: alpha * 0.6, to: alpha },
      scaleX: { from: 1.0, to: 1.2 + intensity * 0.5 },
      scaleY: { from: 1.0, to: 1.2 + intensity * 0.5 },
      duration: 3000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });
  }

  // ── FIREFLIES ──

  createFireflies() {
    // Small amber sparkles near lanterns and cherry trees
    const hotspots = [
      ...PROP_PLACEMENTS.filter(p => p.key === 'prop_lantern').map(p => ({ x: p.x, y: p.y - 15 })),
      ...PROP_PLACEMENTS.filter(p => p.key === 'prop_cherry').map(p => ({ x: p.x, y: p.y - 30 })),
    ];

    for (const spot of hotspots) {
      // 1-2 fireflies per hotspot
      const count = Phaser.Math.Between(1, 2);
      for (let i = 0; i < count; i++) {
        const ff = this.add.graphics();
        ff.fillStyle(0xE8B84A, 0.6);
        ff.fillCircle(0, 0, 1.5);
        ff.setPosition(
          spot.x + Phaser.Math.Between(-15, 15),
          spot.y + Phaser.Math.Between(-10, 10)
        );
        ff.setDepth(9000);
        ff.setBlendMode(Phaser.BlendModes.ADD);

        // Wandering motion
        this.tweens.add({
          targets: ff,
          x: ff.x + Phaser.Math.Between(-20, 20),
          y: ff.y + Phaser.Math.Between(-15, 15),
          alpha: { from: 0, to: 0.8 },
          duration: Phaser.Math.Between(3000, 5000),
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut',
          delay: Phaser.Math.Between(0, 3000),
        });
      }
    }
  }

  // ── VIGNETTE ──

  createVignette(w, h) {
    // Dark edges for atmospheric depth
    const v = this.add.graphics();

    // Top gradient
    for (let i = 0; i < 40; i++) {
      v.fillStyle(0x0A0B24, (40 - i) / 40 * 0.5);
      v.fillRect(0, i, w, 1);
    }
    // Bottom gradient
    for (let i = 0; i < 30; i++) {
      v.fillStyle(0x0A0B24, (30 - i) / 30 * 0.4);
      v.fillRect(0, h - 30 + i, w, 1);
    }
    // Left edge
    for (let i = 0; i < 25; i++) {
      v.fillStyle(0x0A0B24, (25 - i) / 25 * 0.3);
      v.fillRect(i, 0, 1, h);
    }
    // Right edge
    for (let i = 0; i < 25; i++) {
      v.fillStyle(0x0A0B24, (25 - i) / 25 * 0.3);
      v.fillRect(w - 25 + i, 0, 1, h);
    }

    v.setDepth(9500);
    v.setScrollFactor(0); // Fixed to camera
  }

  // ── BUILDINGS ──

  createBuildings() {
    for (const zoneId of Object.keys(ZONES)) {
      this.buildings[zoneId] = new BuildingSprite(this, zoneId);
    }
  }

  // ── MOBILE RESIZE ──

  onResize(gameSize) {
    // Reposition elements if needed
    this.cameras.main.setBounds(0, 0, 800, 450);
  }

  // ── BRIDGE LISTENERS ──

  setupBridgeListeners() {
    bridge.on('agents_updated', this.onAgentsUpdated, this);
    bridge.on('quest_started', this.onQuestStarted, this);
    bridge.on('quest_completed', this.onQuestCompleted, this);
    bridge.on('level_up', this.onLevelUp, this);
    bridge.on('nonprofits_updated', this.onNonprofitsUpdated, this);
  }

  onAgentsUpdated(agentList, playerAgentId) {
    const seen = new Set();

    for (const agentData of agentList) {
      seen.add(agentData.id);
      const isPlayer = agentData.id === playerAgentId;

      if (this.agents[agentData.id]) {
        this.agents[agentData.id].updateFromData(agentData);
      } else {
        const sprite = new AgentSprite(this, agentData, isPlayer);
        this.agents[agentData.id] = sprite;

        if (isPlayer) {
          this.playerAgent = sprite;
          this.cameraSystem.startFollow(sprite);
        }
      }
    }

    for (const id of Object.keys(this.agents)) {
      if (!seen.has(id)) {
        this.agents[id].destroy();
        delete this.agents[id];
      }
    }
  }

  onQuestStarted({ agentId, zone }) {
    const agent = this.agents[agentId];
    if (agent) agent.walkTo(zone);
  }

  onQuestCompleted({ agentId, xp, rested }) {
    const agent = this.agents[agentId];
    if (agent) {
      agent.celebrate(xp, rested);
      this.particles.questCompleteEffect(agent.x, agent.y - 20);
      if (rested) {
        // Extra burst for rested quests
        this.particles.questCompleteEffect(agent.x - 10, agent.y - 25);
        this.particles.questCompleteEffect(agent.x + 10, agent.y - 15);
      }
    }
  }

  onLevelUp({ agentId }) {
    const agent = this.agents[agentId];
    if (agent) {
      this.particles.levelUpEffect(agent.x, agent.y - 20);
    }
  }

  onNonprofitsUpdated(nonprofits) {
    if (nonprofits && nonprofits.length > 0) {
      const np = nonprofits[0];
      const intensity = Math.min(1, (np.tk_committed || 0) / (np.goal || 5000));
      this.updateBeaconGlow(intensity);
    }
  }

  selectBuilding(zoneId) {
    if (this.selectedZone && this.buildings[this.selectedZone]) {
      this.buildings[this.selectedZone].setSelected(false);
    }
    this.selectedZone = zoneId;
    if (zoneId && this.buildings[zoneId]) {
      this.buildings[zoneId].setSelected(true);
    }
  }

  shutdown() {
    bridge.off('agents_updated', this.onAgentsUpdated, this);
    bridge.off('quest_started', this.onQuestStarted, this);
    bridge.off('quest_completed', this.onQuestCompleted, this);
    bridge.off('level_up', this.onLevelUp, this);
    bridge.off('nonprofits_updated', this.onNonprofitsUpdated, this);
    this.scale.off('resize', this.onResize, this);

    if (this.particles) this.particles.destroy();
    if (this.cameraSystem) this.cameraSystem.destroy();
  }
}
