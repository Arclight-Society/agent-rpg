import Phaser from 'phaser';
import { ZONES, PALETTE } from '../data/TilemapConfig.js';
import bridge from '../GameBridge.js';

export default class BuildingSprite extends Phaser.GameObjects.Container {
  constructor(scene, zoneId) {
    const zone = ZONES[zoneId];
    super(scene, zone.x, zone.y);

    this.zoneId = zoneId;
    this.zone = zone;
    this.isSelected = false;

    // Building sprite (anchor bottom-center)
    const buildingKey = `building_${zoneId}`;
    this.sprite = scene.add.image(0, 0, buildingKey).setOrigin(0.5, 1);

    // Glow overlay (invisible until hover/select)
    this.glow = scene.add.image(0, 0, buildingKey)
      .setOrigin(0.5, 1)
      .setAlpha(0)
      .setBlendMode(Phaser.BlendModes.ADD);

    // Name label (hidden by default)
    this.label = scene.add.text(0, -this.sprite.height - 8, zone.label, {
      fontFamily: 'IBM Plex Mono',
      fontSize: '10px',
      color: '#DFD8EB',
      stroke: '#0A0B24',
      strokeThickness: 3,
      align: 'center',
    }).setOrigin(0.5, 1).setAlpha(0);

    this.add([this.sprite, this.glow, this.label]);

    // Interactive hit area (minimum 48x48 for mobile)
    const hitW = Math.max(this.sprite.width, 48);
    const hitH = Math.max(this.sprite.height, 48);
    this.setSize(hitW, hitH);
    this.setInteractive({ useHandCursor: true });

    // Undercroft special: dimmed with green glow
    if (zone.special === 'locked') {
      this.sprite.setAlpha(0.5);
      this.sprite.setTint(0x192A5B);
    }

    // Events
    this.on('pointerover', this.onHover, this);
    this.on('pointerout', this.onOut, this);
    this.on('pointerdown', this.onClick, this);

    // Depth sort by y position
    this.setDepth(zone.y);

    scene.add.existing(this);
  }

  onHover() {
    this.scene.tweens.add({
      targets: this.label,
      alpha: 1,
      duration: 200,
      ease: 'Power2',
    });
    this.scene.tweens.add({
      targets: this.glow,
      alpha: 0.3,
      duration: 200,
      ease: 'Power2',
    });
  }

  onOut() {
    if (!this.isSelected) {
      this.scene.tweens.add({
        targets: this.label,
        alpha: 0,
        duration: 200,
        ease: 'Power2',
      });
    }
    this.scene.tweens.add({
      targets: this.glow,
      alpha: this.isSelected ? 0.15 : 0,
      duration: 200,
      ease: 'Power2',
    });
  }

  onClick() {
    // Pulse animation
    this.scene.tweens.add({
      targets: this.glow,
      alpha: 0.6,
      duration: 100,
      yoyo: true,
      ease: 'Power2',
    });

    bridge.emit('building_clicked', {
      zone: this.zoneId,
      label: this.zone.label,
      questType: this.zone.questType,
      special: this.zone.special || null,
    });
  }

  setSelected(selected) {
    this.isSelected = selected;
    this.label.setAlpha(selected ? 1 : 0);
    this.glow.setAlpha(selected ? 0.15 : 0);
  }
}
