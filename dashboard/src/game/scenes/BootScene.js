import Phaser from 'phaser';
import { BUILDINGS, AGENT_SHEETS, AGENT_SHEET_CONFIG, PROPS } from '../data/AssetManifest.js';
import { PALETTE } from '../data/TilemapConfig.js';

/**
 * BootScene — loads all assets with a styled progress bar,
 * then transitions to CampusScene.
 */
export default class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene' });
  }

  preload() {
    this.createLoadingBar();

    // Buildings
    for (const b of Object.values(BUILDINGS)) {
      this.load.image(b.key, b.path);
    }

    // Agent spritesheets (base + all 7 variants)
    for (const s of Object.values(AGENT_SHEETS)) {
      this.load.spritesheet(s.key, s.path, {
        frameWidth: AGENT_SHEET_CONFIG.frameWidth,
        frameHeight: AGENT_SHEET_CONFIG.frameHeight,
      });
    }

    // Props
    for (const p of Object.values(PROPS)) {
      this.load.image(p.key, p.path);
    }
  }

  createLoadingBar() {
    const { width, height } = this.scale;
    const cx = width / 2;
    const cy = height / 2;

    // Background
    this.cameras.main.setBackgroundColor(0x0A0B24);

    // "ARCLIGHT" text
    const title = this.add.text(cx, cy - 40, 'ARCLIGHT', {
      fontFamily: 'Cormorant Garamond, Georgia, serif',
      fontSize: '24px',
      color: '#DFD8EB',
      letterSpacing: 8,
    }).setOrigin(0.5);

    // Loading text
    const loadText = this.add.text(cx, cy + 40, 'Loading...', {
      fontFamily: 'IBM Plex Mono, monospace',
      fontSize: '10px',
      color: '#646B92',
    }).setOrigin(0.5);

    // Progress bar background
    const barBg = this.add.rectangle(cx, cy, 200, 6, 0x192A5B).setOrigin(0.5);

    // Progress bar fill
    const barFill = this.add.rectangle(cx - 100, cy, 0, 6, 0xC47A90).setOrigin(0, 0.5);

    // Update progress bar
    this.load.on('progress', (value) => {
      barFill.width = 200 * value;
      loadText.setText(`Loading... ${Math.round(value * 100)}%`);
    });

    this.load.on('complete', () => {
      loadText.setText('Ready');
      // Brief pause before transitioning
      this.time.delayedCall(300, () => {
        this.scene.start('CampusScene');
      });
    });
  }

  create() {
    // Scene transitions handled by load.on('complete') above
  }
}
