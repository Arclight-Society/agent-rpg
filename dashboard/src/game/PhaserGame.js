import Phaser from 'phaser';
import BootScene from './scenes/BootScene.js';
import CampusScene from './scenes/CampusScene.js';
import bridge from './GameBridge.js';

/**
 * PhaserGame — game instance config + scene registration.
 * Call createGame(parentElement) to start, destroyGame() to clean up.
 */

const config = {
  type: Phaser.AUTO,
  width: 800,
  height: 450,
  pixelArt: true,
  roundPixels: true,
  antialias: false,
  transparent: false,
  backgroundColor: '#0A0B24',
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_HORIZONTALLY,
    expandParent: true,
  },
  scene: [BootScene, CampusScene],
  input: {
    activePointers: 3, // Support pinch zoom + drag on mobile
    touch: { capture: true },
  },
  render: {
    pixelArt: true,
    roundPixels: true,
    antialias: false,
  },
  fps: {
    target: 30, // Save battery on mobile
    forceSetTimeOut: false,
  },
};

export function createGame(parentElement) {
  if (bridge.getGameInstance()) {
    return bridge.getGameInstance();
  }

  const game = new Phaser.Game({
    ...config,
    parent: parentElement,
  });

  bridge.setGameInstance(game);
  return game;
}

export function destroyGame() {
  bridge.destroy();
}

export { config };
