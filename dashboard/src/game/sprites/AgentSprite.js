import Phaser from 'phaser';
import { SKILL_COLOR_MAP, AGENT_ANIMS } from '../data/AssetManifest.js';
import { ZONES, WALK_SPEED, PALETTE } from '../data/TilemapConfig.js';
import bridge from '../GameBridge.js';

// States
const IDLE = 'idle';
const WALKING = 'walking';
const QUESTING = 'questing';
const CELEBRATING = 'celebrating';

export default class AgentSprite extends Phaser.GameObjects.Container {
  constructor(scene, agentData, isPlayer = false) {
    const startZone = ZONES.great_hall;
    super(scene, startZone.x + Phaser.Math.Between(-20, 20), startZone.y - 10 + Phaser.Math.Between(-10, 10));

    this.agentId = agentData.id;
    this.agentName = agentData.name;
    this.isPlayer = isPlayer;
    this.state = IDLE;
    this.currentZone = 'great_hall';
    this.targetPos = null;
    this.path = [];
    this.pathIndex = 0;

    // Pick spritesheet based on highest skill
    const sheetKey = this.getSheetKey(agentData);
    this.sprite = scene.add.sprite(0, 0, sheetKey).setOrigin(0.5, 1);

    // Name label
    this.nameLabel = scene.add.text(0, -38, agentData.name, {
      fontFamily: 'IBM Plex Mono',
      fontSize: '8px',
      color: isPlayer ? '#F5CCD6' : '#AAB2E2',
      stroke: '#0A0B24',
      strokeThickness: 2,
      align: 'center',
    }).setOrigin(0.5, 1);

    // Player glow indicator
    this.playerGlow = null;
    if (isPlayer) {
      this.playerGlow = scene.add.ellipse(0, -2, 24, 8, PALETTE.blossomDark, 0.3);
      this.add(this.playerGlow);
    }

    this.add([this.sprite, this.nameLabel]);

    // Non-player agents are slightly transparent
    if (!isPlayer) {
      this.setAlpha(0.8);
    }

    // Make clickable
    this.sprite.setInteractive({ useHandCursor: true });
    this.sprite.on('pointerdown', () => {
      bridge.emit('agent_clicked', { agentId: this.agentId });
    });

    // Create animations for this sheet
    this.createAnimations(scene, sheetKey);

    // Start idle
    this.playIdle();

    // Depth sort
    this.setDepth(this.y);

    scene.add.existing(this);
  }

  getSheetKey(agentData) {
    // Find highest skill
    const skills = ['combat', 'analysis', 'fortification', 'coordination', 'commerce', 'crafting', 'exploration'];
    let maxSkill = 'analysis';
    let maxXp = 0;
    for (const skill of skills) {
      const xp = agentData[`xp_${skill}`] || 0;
      if (xp > maxXp) {
        maxXp = xp;
        maxSkill = skill;
      }
    }
    const color = SKILL_COLOR_MAP[maxSkill] || 'base';
    return `agent_${color}`;
  }

  createAnimations(scene, sheetKey) {
    // Only create if not already registered
    for (const [animName, config] of Object.entries(AGENT_ANIMS)) {
      const key = `${sheetKey}_${animName}`;
      if (!scene.anims.exists(key)) {
        const startFrame = config.row * 4;
        scene.anims.create({
          key,
          frames: scene.anims.generateFrameNumbers(sheetKey, {
            start: startFrame,
            end: startFrame + config.frames - 1,
          }),
          frameRate: config.frameRate,
          repeat: config.repeat,
        });
      }
    }
    this._sheetKey = sheetKey;
  }

  playIdle() {
    this.state = IDLE;
    const key = `${this._sheetKey}_idle`;
    if (this.sprite.anims) {
      this.sprite.play(key, true);
    }
  }

  walkTo(zone) {
    const target = ZONES[zone];
    if (!target) return;

    this.state = WALKING;
    this.currentZone = zone;
    const targetX = target.x + Phaser.Math.Between(-15, 15);
    const targetY = target.y - 10 + Phaser.Math.Between(-8, 8);

    // Determine walk direction
    const dx = targetX - this.x;
    const dy = targetY - this.y;
    let dir = 'south';
    if (Math.abs(dx) > Math.abs(dy)) {
      dir = dx > 0 ? 'east' : 'west';
    } else {
      dir = dy > 0 ? 'south' : 'north';
    }

    const animKey = `${this._sheetKey}_walk_${dir}`;
    this.sprite.play(animKey, true);

    // Tween to target
    const dist = Phaser.Math.Distance.Between(this.x, this.y, targetX, targetY);
    const duration = (dist / WALK_SPEED) * 1000;

    this.scene.tweens.add({
      targets: this,
      x: targetX,
      y: targetY,
      duration: Math.max(duration, 500),
      ease: 'Power1',
      onUpdate: () => {
        this.setDepth(this.y);
      },
      onComplete: () => {
        this.playIdle();
      },
    });
  }

  celebrate(xp, rested = false) {
    this.state = CELEBRATING;

    // Flash white (brighter for rested)
    this.sprite.setTintFill(rested ? 0xE8B84A : 0xFFFFFF);
    this.scene.time.delayedCall(rested ? 200 : 100, () => {
      this.sprite.clearTint();
    });

    // XP floating text
    const xpLabel = rested ? `⚡ +${xp} XP (2x)` : `+${xp} XP`;
    const xpColor = rested ? '#E8B84A' : '#DFD8EB';
    const xpText = this.scene.add.text(this.x, this.y - 40, xpLabel, {
      fontFamily: 'IBM Plex Mono',
      fontSize: rested ? '14px' : '12px',
      fontStyle: 'bold',
      color: xpColor,
      stroke: '#0A0B24',
      strokeThickness: 3,
    }).setOrigin(0.5, 1).setDepth(9999);

    this.scene.tweens.add({
      targets: xpText,
      y: xpText.y - 30,
      alpha: 0,
      duration: 1500,
      ease: 'Power2',
      onComplete: () => xpText.destroy(),
    });

    // Return to idle after celebration
    this.scene.time.delayedCall(800, () => {
      this.playIdle();
    });
  }

  updateFromData(agentData) {
    this.agentName = agentData.name;
    this.nameLabel.setText(agentData.name);
  }
}
