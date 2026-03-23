import Phaser from 'phaser';
import BuildingSprite from '../sprites/BuildingSprite.js';
import AgentSprite from '../sprites/AgentSprite.js';
import ParticleSystem from '../systems/ParticleSystem.js';
import CameraSystem from '../systems/CameraSystem.js';
import { ZONES, PATHS, PROP_PLACEMENTS, PALETTE } from '../data/TilemapConfig.js';
import bridge from '../GameBridge.js';

/**
 * CampusScene — the main isometric campus view.
 * Renders buildings, agents, props, paths, and particles.
 */
export default class CampusScene extends Phaser.Scene {
  constructor() {
    super({ key: 'CampusScene' });
    this.buildings = {};
    this.agents = {};
    this.playerAgent = null;
    this.selectedZone = null;
  }

  create() {
    // Ground
    this.drawGround();

    // Stone paths (draw before buildings for proper layering)
    this.drawPaths();

    // Props (behind buildings)
    this.placeProps();

    // Buildings
    this.createBuildings();

    // Beacon glow
    this.createBeaconGlow();

    // Particle system
    this.particles = new ParticleSystem(this);
    this.particles.startCherryBlossoms();

    // Camera system
    this.cameraSystem = new CameraSystem(this);

    // Listen for React events
    this.setupBridgeListeners();

    // Signal ready
    bridge.emit('scene_ready');
  }

  drawGround() {
    // Dark background with subtle ground patches
    const g = this.add.graphics();

    // Grass patches
    const grassAreas = [
      { x: 50, y: 120, w: 200, h: 150 },
      { x: 550, y: 120, w: 200, h: 150 },
      { x: 100, y: 300, w: 250, h: 120 },
      { x: 450, y: 300, w: 250, h: 120 },
      { x: 250, y: 150, w: 300, h: 200 },
    ];

    for (const area of grassAreas) {
      g.fillStyle(0x0F0E30, 0.6);
      g.fillRoundedRect(area.x, area.y, area.w, area.h, 12);
    }

    g.setDepth(0);
  }

  drawPaths() {
    const g = this.add.graphics();
    g.lineStyle(4, 0x4A5288, 0.5);

    for (const path of PATHS) {
      g.beginPath();
      g.moveTo(path.from.x, path.from.y);

      // Slight curve for organic feel
      const midX = (path.from.x + path.to.x) / 2;
      const midY = (path.from.y + path.to.y) / 2;
      const offset = (path.from.x - path.to.x) * 0.1;
      g.lineTo(path.to.x, path.to.y);
      g.strokePath();
    }

    // Cobblestone dots along paths
    g.fillStyle(0x3C5389, 0.3);
    for (const path of PATHS) {
      const steps = 8;
      for (let i = 1; i < steps; i++) {
        const t = i / steps;
        const x = Phaser.Math.Linear(path.from.x, path.to.x, t);
        const y = Phaser.Math.Linear(path.from.y, path.to.y, t);
        g.fillCircle(x + Phaser.Math.Between(-3, 3), y + Phaser.Math.Between(-2, 2), 2);
      }
    }

    g.setDepth(1);
  }

  placeProps() {
    for (const prop of PROP_PLACEMENTS) {
      const sprite = this.add.image(prop.x, prop.y, prop.key).setOrigin(0.5, 1);
      sprite.setDepth(prop.y);
    }
  }

  createBuildings() {
    for (const zoneId of Object.keys(ZONES)) {
      this.buildings[zoneId] = new BuildingSprite(this, zoneId);
    }
  }

  createBeaconGlow() {
    const beacon = ZONES.beacon;
    this.beaconGlow = this.add.image(beacon.x, beacon.y - 60, 'glow')
      .setOrigin(0.5)
      .setScale(1.5)
      .setAlpha(0.2)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0xD4A843)
      .setDepth(beacon.y - 1);

    // Pulsing animation
    this.tweens.add({
      targets: this.beaconGlow,
      alpha: { from: 0.15, to: 0.35 },
      scale: { from: 1.4, to: 1.7 },
      duration: 3000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });
  }

  updateBeaconGlow(intensity) {
    // intensity = 0-1 (tk_committed / goal)
    const minAlpha = 0.1;
    const maxAlpha = 0.6;
    const alpha = minAlpha + (maxAlpha - minAlpha) * intensity;

    this.tweens.killTweensOf(this.beaconGlow);
    this.beaconGlow.setAlpha(alpha);
    this.beaconGlow.setScale(1.2 + intensity * 0.8);

    this.tweens.add({
      targets: this.beaconGlow,
      alpha: { from: alpha * 0.7, to: alpha },
      scale: { from: 1.2 + intensity * 0.6, to: 1.2 + intensity * 1.0 },
      duration: 3000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });
  }

  setupBridgeListeners() {
    bridge.on('agents_updated', this.onAgentsUpdated, this);
    bridge.on('quest_started', this.onQuestStarted, this);
    bridge.on('quest_completed', this.onQuestCompleted, this);
    bridge.on('level_up', this.onLevelUp, this);
    bridge.on('nonprofits_updated', this.onNonprofitsUpdated, this);
  }

  onAgentsUpdated(agentList, playerAgentId) {
    // Create or update agent sprites
    const seen = new Set();

    for (const agentData of agentList) {
      seen.add(agentData.id);
      const isPlayer = agentData.id === playerAgentId;

      if (this.agents[agentData.id]) {
        // Update existing
        this.agents[agentData.id].updateFromData(agentData);
      } else {
        // Create new
        const sprite = new AgentSprite(this, agentData, isPlayer);
        this.agents[agentData.id] = sprite;

        if (isPlayer) {
          this.playerAgent = sprite;
          this.cameraSystem.startFollow(sprite);
        }
      }
    }

    // Remove agents no longer in list
    for (const id of Object.keys(this.agents)) {
      if (!seen.has(id)) {
        this.agents[id].destroy();
        delete this.agents[id];
      }
    }
  }

  onQuestStarted({ agentId, zone }) {
    const agent = this.agents[agentId];
    if (agent) {
      agent.walkTo(zone);
    }
  }

  onQuestCompleted({ agentId, xp }) {
    const agent = this.agents[agentId];
    if (agent) {
      agent.celebrate(xp);
      this.particles.questCompleteEffect(agent.x, agent.y - 20);
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
      const np = nonprofits[0]; // Arclight Society
      const intensity = Math.min(1, (np.tk_committed || 0) / (np.goal || 5000));
      this.updateBeaconGlow(intensity);
    }
  }

  selectBuilding(zoneId) {
    // Deselect previous
    if (this.selectedZone && this.buildings[this.selectedZone]) {
      this.buildings[this.selectedZone].setSelected(false);
    }
    // Select new
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

    if (this.particles) this.particles.destroy();
    if (this.cameraSystem) this.cameraSystem.destroy();
  }
}
