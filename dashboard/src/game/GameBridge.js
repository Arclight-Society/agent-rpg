/**
 * GameBridge — EventEmitter shared between React and Phaser.
 * Single instance, imported by both sides.
 *
 * React → Phaser events:
 *   'quest_started'    { agentId, zone }     → agent walks to building
 *   'quest_completed'  { agentId, xp, zone } → celebration + XP popup
 *   'level_up'         { agentId, skill }     → flash + petal burst
 *   'agents_updated'   agents[]              → refresh all agent sprites
 *   'nonprofits_updated' nonprofits[]        → update Beacon glow
 *
 * Phaser → React events:
 *   'building_clicked' { zone, label }       → React opens relevant tab
 *   'agent_clicked'    { agentId }           → React shows agent profile
 *   'scene_ready'      {}                    → CampusScene is fully loaded
 */

import Phaser from 'phaser';

class GameBridge extends Phaser.Events.EventEmitter {
  constructor() {
    super();
    this._gameInstance = null;
  }

  setGameInstance(game) {
    this._gameInstance = game;
  }

  getGameInstance() {
    return this._gameInstance;
  }

  destroy() {
    this.removeAllListeners();
    if (this._gameInstance) {
      this._gameInstance.destroy(true);
      this._gameInstance = null;
    }
  }
}

// Singleton — shared between React and Phaser
const bridge = new GameBridge();
export default bridge;
