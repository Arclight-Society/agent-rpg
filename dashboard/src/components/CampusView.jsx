import { useEffect, useRef, useState } from 'react';
import { createGame, destroyGame } from '../game/PhaserGame.js';
import bridge from '../game/GameBridge.js';

/**
 * CampusView — React wrapper that mounts Phaser to a div.
 * Handles lifecycle, event bridging, and CSS fallback.
 *
 * Props:
 *   agents      — array of agent objects from API
 *   playerAgentId — current player's agent ID
 *   nonprofits  — array of nonprofit objects from API
 *   autoQuest   — boolean, is auto-quest active
 *   onBuildingClick — callback({ zone, label, questType, special })
 *   onAgentClick    — callback({ agentId })
 */
export default function CampusView({
  agents,
  playerAgentId,
  nonprofits,
  autoQuest,
  onBuildingClick,
  onAgentClick,
}) {
  const containerRef = useRef(null);
  const gameCreated = useRef(false);
  const [phaserFailed, setPhaserFailed] = useState(false);

  // Mount Phaser game
  useEffect(() => {
    if (gameCreated.current || !containerRef.current) return;

    try {
      const game = createGame(containerRef.current);
      gameCreated.current = true;

      // Listen for Phaser → React events
      bridge.on('building_clicked', (data) => {
        if (onBuildingClick) onBuildingClick(data);
      });

      bridge.on('agent_clicked', (data) => {
        if (onAgentClick) onAgentClick(data);
      });
    } catch (err) {
      console.error('Phaser failed to initialize:', err);
      setPhaserFailed(true);
    }

    return () => {
      gameCreated.current = false;
      destroyGame();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Push agent data to Phaser when it changes
  useEffect(() => {
    if (!gameCreated.current || !agents) return;
    bridge.emit('agents_updated', agents, playerAgentId);
  }, [agents, playerAgentId]);

  // Push nonprofit data to Phaser
  useEffect(() => {
    if (!gameCreated.current || !nonprofits) return;
    bridge.emit('nonprofits_updated', nonprofits);
  }, [nonprofits]);

  // CSS fallback if Phaser fails
  if (phaserFailed) {
    return <CSSFallbackCampus agents={agents} autoQuest={autoQuest} />;
  }

  return (
    <div
      ref={containerRef}
      id="campus-container"
      style={{
        width: '100%',
        maxWidth: 800,
        aspectRatio: '16/9',
        minHeight: 200,
        margin: '0 auto',
        borderRadius: 8,
        overflow: 'hidden',
        border: '1px solid #192A5B',
        touchAction: 'none', // Prevent browser scroll interference on mobile
        WebkitTouchCallout: 'none',
        WebkitUserSelect: 'none',
        userSelect: 'none',
      }}
    />
  );
}

/**
 * Minimal CSS fallback — shows if Phaser can't initialize.
 * Simplified version of the original CSS campus.
 */
function CSSFallbackCampus({ agents, autoQuest }) {
  return (
    <div style={{
      width: '100%',
      maxWidth: 800,
      aspectRatio: '16/9',
      background: '#0A0B24',
      borderRadius: 8,
      border: '1px solid #192A5B',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div style={{
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 10,
        color: '#646B92',
        textAlign: 'center',
      }}>
        <div style={{ marginBottom: 8, color: '#AAB2E2', fontSize: 12 }}>
          Arclight Campus
        </div>
        <div>{agents?.length || 0} agents online</div>
        <div style={{ marginTop: 4, color: autoQuest ? '#6B9B45' : '#646B92' }}>
          {autoQuest ? 'Auto-questing...' : 'Idle'}
        </div>
      </div>
    </div>
  );
}
