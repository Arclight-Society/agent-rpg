import { useState, useEffect, useMemo } from 'react';

/**
 * CampusView — Pure React + CSS pixel art campus.
 * No Phaser. Mobile-first (375px). Dark navy aesthetic.
 *
 * Props:
 *   agents         — array of agent objects from API
 *   playerAgentId  — current player's agent ID
 *   profile        — player's agent profile (total_xp, total_level, name, etc.)
 *   nonprofits     — array of nonprofit objects
 *   autoQuest      — boolean, is auto-quest running
 *   restedCharges  — number of rested bonus charges
 *   questLog       — array of recent quest completions
 *   onBuildingClick — callback({ zone, questType, special })
 */

// ── Building definitions with zone metadata ──
const BUILDINGS = [
  { id: 'beacon',      img: '/assets/buildings/beacon.png',      label: 'Beacon',      x: 44, y: 3,  w: 12, h: 18, questType: null, special: 'beacon' },
  { id: 'archives',    img: '/assets/buildings/archives.png',    label: 'Archives',    x: 8,  y: 14, w: 16, h: 20, questType: 'alt_text' },
  { id: 'forge',       img: '/assets/buildings/forge.png',       label: 'Forge',       x: 74, y: 14, w: 16, h: 20, questType: 'crafting' },
  { id: 'greenhouse',  img: '/assets/buildings/greenhouse.png',  label: 'Greenhouse',  x: 4,  y: 50, w: 16, h: 18, questType: 'exploration' },
  { id: 'great_hall',  img: '/assets/buildings/great_hall.png',  label: 'Great Hall',  x: 34, y: 30, w: 32, h: 30, questType: null, special: 'hall' },
  { id: 'watchtower',  img: '/assets/buildings/watchtower.png',  label: 'Watchtower',  x: 80, y: 50, w: 14, h: 22, questType: 'fortification' },
  { id: 'commons',     img: '/assets/buildings/commons.png',     label: 'Commons',     x: 10, y: 76, w: 18, h: 16, questType: 'coordination' },
  { id: 'undercroft',  img: '/assets/buildings/undercroft.png',  label: 'Undercroft',  x: 70, y: 76, w: 18, h: 16, questType: 'combat' },
];

// ── Props: cherry trees, lanterns, fountain ──
const TREES = [
  { x: 2,  y: 38, w: 10 },
  { x: 28, y: 18, w: 8  },
  { x: 68, y: 40, w: 9  },
  { x: 88, y: 36, w: 8  },
  { x: 48, y: 68, w: 9  },
];

const LANTERNS = [
  { x: 30, y: 62 },
  { x: 68, y: 62 },
  { x: 22, y: 36 },
  { x: 76, y: 36 },
  { x: 50, y: 20 },
];

const FOUNTAIN = { x: 26, y: 82, w: 10 };

// ── Stage system: every 500 total XP = 1 stage ──
function getStage(totalXp) {
  return Math.floor((totalXp || 0) / 500) + 1;
}
function getStageProgress(totalXp) {
  return ((totalXp || 0) % 500) / 500;
}

// ── Active quest zone detection ──
function getActiveZone(questLog, autoQuest) {
  if (!autoQuest || !questLog || questLog.length === 0) return null;
  const recent = questLog[0];
  if (recent && recent.time > Date.now() - 15000) return 'archives'; // alt_text quests
  return autoQuest ? 'archives' : null;
}

// ── CSS keyframe injection (once) ──
let stylesInjected = false;
function injectStyles() {
  if (stylesInjected) return;
  stylesInjected = true;
  const style = document.createElement('style');
  style.textContent = `
    @keyframes campus-bob {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-4px); }
    }
    @keyframes campus-petal {
      0% {
        transform: translate(0, 0) rotate(0deg);
        opacity: 0;
      }
      10% { opacity: 0.8; }
      90% { opacity: 0.6; }
      100% {
        transform: translate(var(--petal-drift), calc(100cqh + 20px)) rotate(720deg);
        opacity: 0;
      }
    }
    @keyframes campus-glow-pulse {
      0%, 100% { opacity: 0.3; }
      50% { opacity: 0.6; }
    }
    @keyframes campus-beacon-pulse {
      0%, 100% { opacity: 0.15; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(1.15); }
    }
    @keyframes campus-spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    @keyframes campus-xp-bar-shine {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
    @keyframes campus-fade-in {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes campus-label-in {
      from { opacity: 0; transform: translate(-50%, 4px); }
      to { opacity: 1; transform: translate(-50%, 0); }
    }
  `;
  document.head.appendChild(style);
}


export default function CampusView({
  agents,
  playerAgentId,
  profile,
  nonprofits,
  autoQuest,
  restedCharges = 0,
  questLog = [],
  onBuildingClick,
}) {
  const [hoveredBuilding, setHoveredBuilding] = useState(null);
  const [tappedBuilding, setTappedBuilding] = useState(null);

  // Inject CSS keyframes on mount
  useEffect(() => { injectStyles(); }, []);

  // Clear tapped label after delay
  useEffect(() => {
    if (!tappedBuilding) return;
    const t = setTimeout(() => setTappedBuilding(null), 2000);
    return () => clearTimeout(t);
  }, [tappedBuilding]);

  const totalXp = profile?.total_xp || 0;
  const totalLevel = profile?.total_level || 1;
  const agentName = profile?.name || 'Agent';
  const stage = getStage(totalXp);
  const stageProgress = getStageProgress(totalXp);
  const activeZone = getActiveZone(questLog, autoQuest);

  // Agent position — near the active building or great hall
  const agentBuilding = useMemo(() => {
    if (activeZone) {
      return BUILDINGS.find(b => b.id === activeZone) || BUILDINGS.find(b => b.id === 'great_hall');
    }
    return BUILDINGS.find(b => b.id === 'great_hall');
  }, [activeZone]);

  // Cherry blossom petals
  const petals = useMemo(() => {
    return Array.from({ length: 10 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 8,
      duration: 6 + Math.random() * 6,
      size: 3 + Math.random() * 4,
      drift: (Math.random() - 0.5) * 60,
    }));
  }, []);

  // Recent XP gain
  const recentXp = questLog.length > 0 && questLog[0].time > Date.now() - 8000
    ? questLog[0] : null;

  return (
    <div
      style={{
        width: '100%',
        maxWidth: 800,
        aspectRatio: '4 / 3',
        margin: '0 auto',
        position: 'relative',
        background: '#0A0B24',
        borderRadius: 10,
        overflow: 'hidden',
        border: '1px solid #192A5B',
        containerType: 'size',
        touchAction: 'manipulation',
        WebkitUserSelect: 'none',
        userSelect: 'none',
      }}
    >
      {/* ── Ground gradient ── */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'linear-gradient(180deg, #0A0B24 0%, #0D0F2E 40%, #111438 70%, #141836 100%)',
      }} />

      {/* ── Grid paths (subtle) ── */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `
          linear-gradient(rgba(100,107,146,0.06) 1px, transparent 1px),
          linear-gradient(90deg, rgba(100,107,146,0.06) 1px, transparent 1px)
        `,
        backgroundSize: '10% 10%',
      }} />

      {/* ── Cherry blossom petals ── */}
      {petals.map(p => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.left}%`,
            top: '-8px',
            width: p.size,
            height: p.size,
            borderRadius: '50% 0 50% 50%',
            background: `hsl(${340 + Math.random() * 20}, 60%, ${70 + Math.random() * 15}%)`,
            opacity: 0,
            animation: `campus-petal ${p.duration}s ${p.delay}s infinite ease-in`,
            '--petal-drift': `${p.drift}px`,
            pointerEvents: 'none',
            zIndex: 50,
          }}
        />
      ))}

      {/* ── Lantern glow spots ── */}
      {LANTERNS.map((l, i) => (
        <div key={`glow-${i}`} style={{
          position: 'absolute',
          left: `${l.x - 3}%`,
          top: `${l.y - 4}%`,
          width: '8%',
          height: '10%',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,180,80,0.25) 0%, transparent 70%)',
          animation: `campus-glow-pulse ${3 + i * 0.4}s ease-in-out infinite`,
          pointerEvents: 'none',
          zIndex: 1,
        }} />
      ))}

      {/* ── Beacon amber pulse ── */}
      <div style={{
        position: 'absolute',
        left: '42%',
        top: '0%',
        width: '16%',
        height: '20%',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(245,158,11,0.3) 0%, transparent 70%)',
        animation: 'campus-beacon-pulse 3s ease-in-out infinite',
        pointerEvents: 'none',
        zIndex: 1,
      }} />

      {/* ── Cherry blossom trees ── */}
      {TREES.map((t, i) => (
        <img
          key={`tree-${i}`}
          src="/assets/props/cherry_blossom_tree.png"
          alt=""
          style={{
            position: 'absolute',
            left: `${t.x}%`,
            top: `${t.y}%`,
            width: `${t.w}%`,
            imageRendering: 'pixelated',
            pointerEvents: 'none',
            zIndex: 4,
          }}
        />
      ))}

      {/* ── Lantern sprites ── */}
      {LANTERNS.map((l, i) => (
        <img
          key={`lantern-${i}`}
          src="/assets/props/lantern.png"
          alt=""
          style={{
            position: 'absolute',
            left: `${l.x}%`,
            top: `${l.y}%`,
            width: '3%',
            imageRendering: 'pixelated',
            pointerEvents: 'none',
            zIndex: 5,
          }}
        />
      ))}

      {/* ── Fountain ── */}
      <img
        src="/assets/props/fountain.png"
        alt=""
        style={{
          position: 'absolute',
          left: `${FOUNTAIN.x}%`,
          top: `${FOUNTAIN.y}%`,
          width: `${FOUNTAIN.w}%`,
          imageRendering: 'pixelated',
          pointerEvents: 'none',
          zIndex: 5,
        }}
      />

      {/* ── Buildings ── */}
      {BUILDINGS.map(b => {
        const isActive = activeZone === b.id;
        const isHovered = hoveredBuilding === b.id;
        const isTapped = tappedBuilding === b.id;
        const showLabel = isHovered || isTapped;

        return (
          <div
            key={b.id}
            style={{
              position: 'absolute',
              left: `${b.x}%`,
              top: `${b.y}%`,
              width: `${b.w}%`,
              cursor: 'pointer',
              zIndex: b.id === 'great_hall' ? 8 : 6,
            }}
            onClick={() => {
              setTappedBuilding(b.id);
              if (onBuildingClick) {
                onBuildingClick({
                  zone: b.id,
                  questType: b.questType,
                  special: b.special || null,
                });
              }
            }}
            onMouseEnter={() => setHoveredBuilding(b.id)}
            onMouseLeave={() => setHoveredBuilding(null)}
          >
            <img
              src={b.img}
              alt={b.label}
              style={{
                width: '100%',
                imageRendering: 'pixelated',
                filter: isHovered ? 'brightness(1.2)' : 'none',
                transition: 'filter 0.2s',
              }}
            />

            {/* Auto-quest spinner on active building */}
            {isActive && autoQuest && (
              <div style={{
                position: 'absolute',
                top: -4,
                right: -4,
                width: 14,
                height: 14,
                border: '2px solid transparent',
                borderTopColor: '#F59E0B',
                borderRightColor: '#F59E0B',
                borderRadius: '50%',
                animation: 'campus-spin 1s linear infinite',
                zIndex: 20,
              }} />
            )}

            {/* Building label on tap/hover */}
            {showLabel && (
              <div style={{
                position: 'absolute',
                bottom: '100%',
                left: '50%',
                transform: 'translateX(-50%)',
                marginBottom: 4,
                padding: '3px 8px',
                background: 'rgba(10,11,36,0.9)',
                border: '1px solid #2A2F5A',
                borderRadius: 4,
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 9,
                color: '#AAB2E2',
                whiteSpace: 'nowrap',
                animation: 'campus-label-in 0.2s ease-out',
                zIndex: 30,
                letterSpacing: 0.5,
              }}>
                {b.label}
              </div>
            )}
          </div>
        );
      })}

      {/* ── Player Agent Sprite ── */}
      {agentBuilding && (
        <img
          src="/assets/characters/base_south.png"
          alt="Your agent"
          style={{
            position: 'absolute',
            left: `${agentBuilding.x + agentBuilding.w / 2 - 2.5}%`,
            top: `${agentBuilding.y + agentBuilding.h - 2}%`,
            width: '5%',
            imageRendering: 'pixelated',
            animation: 'campus-bob 2s ease-in-out infinite',
            zIndex: 10,
            pointerEvents: 'none',
            transition: 'left 1s ease, top 1s ease',
          }}
        />
      )}

      {/* ── HUD: Top-left — Agent name + level ── */}
      <div style={{
        position: 'absolute',
        top: 8,
        left: 8,
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        zIndex: 40,
        pointerEvents: 'none',
      }}>
        <div style={{
          padding: '4px 10px',
          background: 'rgba(10,11,36,0.85)',
          border: '1px solid #2A2F5A',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}>
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 10,
            fontWeight: 600,
            color: '#E2E8F0',
            letterSpacing: 0.5,
          }}>
            {agentName}
          </span>
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 9,
            fontWeight: 700,
            color: '#0A0B24',
            background: 'linear-gradient(135deg, #C084FC, #A855F7)',
            borderRadius: 4,
            padding: '1px 5px',
            letterSpacing: 0.5,
          }}>
            L{totalLevel}
          </span>
        </div>

        {/* Rested indicator */}
        {restedCharges > 0 && (
          <div style={{
            padding: '4px 8px',
            background: 'rgba(245,158,11,0.15)',
            border: '1px solid rgba(245,158,11,0.4)',
            borderRadius: 6,
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 9,
            fontWeight: 600,
            color: '#F59E0B',
          }}>
            ⚡ {restedCharges}
          </div>
        )}
      </div>

      {/* ── HUD: Top-right — Stage counter ── */}
      <div style={{
        position: 'absolute',
        top: 8,
        right: 8,
        zIndex: 40,
        pointerEvents: 'none',
      }}>
        <div style={{
          padding: '4px 10px',
          background: 'rgba(10,11,36,0.85)',
          border: '1px solid #2A2F5A',
          borderRadius: 6,
          textAlign: 'center',
        }}>
          <div style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 8,
            fontWeight: 600,
            color: '#646B92',
            letterSpacing: 2,
            textTransform: 'uppercase',
            marginBottom: 1,
          }}>
            STAGE
          </div>
          <div style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 16,
            fontWeight: 700,
            color: '#E2E8F0',
            lineHeight: 1,
          }}>
            {stage}
          </div>
        </div>
      </div>

      {/* ── HUD: Bottom — XP progress bar ── */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 40,
        pointerEvents: 'none',
        padding: '0 0',
      }}>
        {/* Recent XP gain toast */}
        {recentXp && (
          <div style={{
            textAlign: 'center',
            marginBottom: 6,
            animation: 'campus-fade-in 0.4s ease-out',
          }}>
            <span style={{
              display: 'inline-block',
              padding: '3px 12px',
              background: 'rgba(10,11,36,0.85)',
              border: '1px solid #2A2F5A',
              borderRadius: 6,
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 10,
              fontWeight: 600,
              color: recentXp.rested ? '#F59E0B' : '#6B9B45',
            }}>
              +{recentXp.xp} XP{recentXp.rested ? ' (rested)' : ''}
            </span>
          </div>
        )}

        {/* XP bar container */}
        <div style={{
          background: 'rgba(10,11,36,0.9)',
          borderTop: '1px solid #192A5B',
          padding: '6px 12px 8px',
        }}>
          {/* Stage label + XP numbers */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 3,
          }}>
            <span style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 8,
              color: '#646B92',
              letterSpacing: 1,
            }}>
              STAGE {stage}
            </span>
            <span style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 8,
              color: '#646B92',
            }}>
              {totalXp % 500} / 500 XP
            </span>
          </div>

          {/* Progress bar */}
          <div style={{
            width: '100%',
            height: 6,
            background: '#1A1D3A',
            borderRadius: 3,
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${stageProgress * 100}%`,
              height: '100%',
              borderRadius: 3,
              background: 'linear-gradient(90deg, #7C3AED, #A855F7, #C084FC)',
              backgroundSize: '200% 100%',
              animation: stageProgress > 0 ? 'campus-xp-bar-shine 3s linear infinite' : 'none',
              transition: 'width 0.6s ease-out',
            }} />
          </div>
        </div>
      </div>

      {/* ── Auto-quest indicator ── */}
      {autoQuest && (
        <div style={{
          position: 'absolute',
          bottom: 32,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 40,
          pointerEvents: 'none',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '3px 10px',
            background: 'rgba(107,155,69,0.15)',
            border: '1px solid rgba(107,155,69,0.35)',
            borderRadius: 20,
          }}>
            <div style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: '#6B9B45',
              animation: 'campus-glow-pulse 1.5s ease-in-out infinite',
            }} />
            <span style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 8,
              color: '#6B9B45',
              letterSpacing: 1,
              fontWeight: 600,
            }}>
              AUTO-QUESTING
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
