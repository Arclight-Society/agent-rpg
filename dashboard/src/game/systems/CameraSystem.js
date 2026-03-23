import { CAMERA } from '../data/TilemapConfig.js';

/**
 * CameraSystem — smooth follow, zoom, bounds.
 */
export default class CameraSystem {
  constructor(scene) {
    this.scene = scene;
    this.camera = scene.cameras.main;
    this.followTarget = null;
    this.isDragging = false;

    // Set camera bounds to canvas size
    this.camera.setBounds(0, 0, 800, 450);

    // Setup zoom controls
    this.setupZoom();
    this.setupDrag();
  }

  /**
   * Follow a game object with smooth lerp.
   */
  startFollow(target) {
    this.followTarget = target;
    this.camera.startFollow(target, true, CAMERA.lerpX, CAMERA.lerpY);
  }

  stopFollow() {
    this.followTarget = null;
    this.camera.stopFollow();
  }

  setupZoom() {
    // Desktop: scroll wheel zoom
    this.scene.input.on('wheel', (_pointer, _gameObjects, _dx, dy) => {
      const zoom = this.camera.zoom;
      const newZoom = Phaser.Math.Clamp(
        zoom - dy * 0.001,
        CAMERA.minZoom,
        CAMERA.maxZoom
      );
      this.camera.setZoom(newZoom);
    });

    // Mobile: pinch zoom
    this.scene.input.on('pointermove', (pointer) => {
      if (this.scene.input.pointer1.isDown && this.scene.input.pointer2.isDown) {
        const p1 = this.scene.input.pointer1;
        const p2 = this.scene.input.pointer2;

        const dist = Phaser.Math.Distance.Between(p1.x, p1.y, p2.x, p2.y);
        const prevDist = Phaser.Math.Distance.Between(
          p1.x - p1.velocity.x, p1.y - p1.velocity.y,
          p2.x - p2.velocity.x, p2.y - p2.velocity.y
        );

        if (prevDist > 0) {
          const zoom = this.camera.zoom * (dist / prevDist);
          this.camera.setZoom(Phaser.Math.Clamp(zoom, CAMERA.minZoom, CAMERA.maxZoom));
        }
      }
    });
  }

  setupDrag() {
    // Pan camera by dragging (when not following)
    this.scene.input.on('pointerdown', () => {
      this.isDragging = true;
    });

    this.scene.input.on('pointerup', () => {
      this.isDragging = false;
    });

    this.scene.input.on('pointermove', (pointer) => {
      if (!pointer.isDown || !this.isDragging) return;
      // Only drag if single touch (not pinch)
      if (this.scene.input.pointer2?.isDown) return;

      // Temporarily stop follow during drag
      if (this.followTarget) {
        this.camera.stopFollow();
      }

      this.camera.scrollX -= (pointer.x - pointer.prevPosition.x) / this.camera.zoom;
      this.camera.scrollY -= (pointer.y - pointer.prevPosition.y) / this.camera.zoom;
    });

    this.scene.input.on('pointerup', () => {
      // Resume follow after drag
      if (this.followTarget) {
        this.scene.time.delayedCall(1000, () => {
          if (this.followTarget) {
            this.camera.startFollow(this.followTarget, true, CAMERA.lerpX, CAMERA.lerpY);
          }
        });
      }
    });
  }

  resetZoom() {
    this.camera.setZoom(CAMERA.defaultZoom);
  }

  destroy() {
    this.scene.input.removeAllListeners();
  }
}
