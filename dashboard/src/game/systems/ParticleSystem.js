import Phaser from 'phaser';
import { PALETTE } from '../data/TilemapConfig.js';

/**
 * ParticleSystem — cherry blossoms and celebration effects.
 */
export default class ParticleSystem {
  constructor(scene) {
    this.scene = scene;
    this.createTextures();
  }

  createTextures() {
    // Petal texture (small pink ellipse)
    if (!this.scene.textures.exists('petal')) {
      const g = this.scene.make.graphics({ add: false });
      g.fillStyle(0xF5CCD6, 1);
      g.fillEllipse(3, 2, 6, 4);
      g.generateTexture('petal', 6, 4);
      g.destroy();
    }

    // Sparkle texture (small circle for quest complete)
    if (!this.scene.textures.exists('sparkle')) {
      const g = this.scene.make.graphics({ add: false });
      g.fillStyle(0xE8B84A, 1);
      g.fillCircle(3, 3, 3);
      g.generateTexture('sparkle', 6, 6);
      g.destroy();
    }

    // Glow texture (for beacon)
    if (!this.scene.textures.exists('glow')) {
      const g = this.scene.make.graphics({ add: false });
      g.fillGradientStyle(0xD4A843, 0xD4A843, 0xD4A843, 0xD4A843, 1, 1, 0, 0);
      g.fillCircle(32, 32, 32);
      g.generateTexture('glow', 64, 64);
      g.destroy();
    }
  }

  /**
   * Start ambient cherry blossom petals — always running.
   */
  startCherryBlossoms() {
    const petalColors = [0xF5CCD6, 0xE8A0B0, 0xC47A90];

    this.blossomEmitter = this.scene.add.particles(0, 0, 'petal', {
      x: { min: 0, max: 800 },
      y: -10,
      lifespan: { min: 5000, max: 8000 },
      speedX: { min: 10, max: 30 },
      speedY: { min: 15, max: 35 },
      angle: { min: 80, max: 100 },
      rotate: { min: 0, max: 360 },
      scale: { start: 0.8, end: 0.4 },
      alpha: { start: 0.5, end: 0 },
      tint: petalColors,
      frequency: 800,
      quantity: 1,
      blendMode: Phaser.BlendModes.NORMAL,
    });

    this.blossomEmitter.setDepth(5);
    return this.blossomEmitter;
  }

  /**
   * Quest complete — small gold sparkle burst at position.
   */
  questCompleteEffect(x, y) {
    const emitter = this.scene.add.particles(x, y, 'sparkle', {
      speed: { min: 30, max: 80 },
      angle: { min: 0, max: 360 },
      scale: { start: 1, end: 0 },
      alpha: { start: 1, end: 0 },
      lifespan: 800,
      quantity: 8,
      tint: [0xD4A843, 0xE8B84A, 0xF5CCD6],
      blendMode: Phaser.BlendModes.ADD,
      emitting: false,
    });

    emitter.setDepth(9998);
    emitter.explode();

    this.scene.time.delayedCall(1000, () => emitter.destroy());
  }

  /**
   * Level up — big petal burst from agent position.
   */
  levelUpEffect(x, y) {
    // Petal burst
    const emitter = this.scene.add.particles(x, y, 'petal', {
      speed: { min: 50, max: 120 },
      angle: { min: 0, max: 360 },
      scale: { start: 1.2, end: 0 },
      alpha: { start: 0.8, end: 0 },
      lifespan: 1500,
      quantity: 25,
      tint: [0xF5CCD6, 0xE8A0B0, 0xC47A90, 0xE8B84A],
      blendMode: Phaser.BlendModes.ADD,
      emitting: false,
    });

    emitter.setDepth(9998);
    emitter.explode();

    // Screen flash
    const flash = this.scene.add.rectangle(400, 225, 800, 450, 0xFFFFFF, 0.4).setDepth(9999);
    this.scene.tweens.add({
      targets: flash,
      alpha: 0,
      duration: 300,
      ease: 'Power2',
      onComplete: () => flash.destroy(),
    });

    this.scene.time.delayedCall(2000, () => emitter.destroy());
  }

  destroy() {
    if (this.blossomEmitter) {
      this.blossomEmitter.destroy();
    }
  }
}
