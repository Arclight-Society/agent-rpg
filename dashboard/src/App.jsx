import { useState, useEffect, useCallback } from 'react'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SKILLS = ['combat', 'analysis', 'fortification', 'coordination', 'commerce', 'crafting', 'exploration']
const SKILL_COLORS = {
  combat: '#aa6a6a',
  analysis: '#6a8aaa',
  fortification: '#8a6aaa',
  coordination: '#6aaa7a',
  commerce: '#c8a97e',
  crafting: '#aaa06a',
  exploration: '#7aaa9a',
}

function useApi(path, interval = 15000) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const fetchData = useCallback(() => {
    fetch(`${API}${path}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(setData)
      .catch(e => setError(e.toString()))
  }, [path])

  useEffect(() => {
    fetchData()
    const id = setInterval(fetchData, interval)
    return () => clearInterval(id)
  }, [fetchData, interval])

  return { data, error, refetch: fetchData }
}

function timeAgo(epoch) {
  const s = Math.floor(Date.now() / 1000 - epoch)
  if (s < 60) return `${s}s ago`
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

function xpForLevel(level) {
  return Math.floor(100 * Math.pow(level, 1.5))
}

function xpProgress(xp, level) {
  const current = xpForLevel(level)
  const next = xpForLevel(level + 1)
  if (next === current) return 100
  return Math.min(100, ((xp - current) / (next - current)) * 100)
}

// ── Views ──

function ProfileView({ agents }) {
  const agent = agents?.[0]
  if (!agent) return <div className="loading">No agents registered yet.</div>

  const ethics = typeof agent.ethics === 'string' ? JSON.parse(agent.ethics) : agent.ethics

  return (
    <div>
      <div className="profile-header">
        <div>
          <div className="profile-name">{agent.name}</div>
          <div className="profile-persona">{agent.persona}</div>
        </div>
        <div className="profile-meta">
          <div className="profile-level">{agent.total_level}</div>
          <div className="profile-level-label">TOTAL LEVEL</div>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-box">
          <div className="stat-value">{agent.tokens}</div>
          <div className="stat-label">Tokens</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{agent.gold}</div>
          <div className="stat-label">Gold</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{agent.quests_completed}</div>
          <div className="stat-label">Quests</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">{agent.tokens_donated}</div>
          <div className="stat-label">Donated</div>
        </div>
      </div>

      <div className="section-title">Skills</div>
      <div className="skills-grid">
        {SKILLS.map(s => {
          const level = agent[`skill_${s}`]
          const xp = agent[`xp_${s}`]
          const progress = xpProgress(xp, level)
          return (
            <div key={s} className="skill-row">
              <div className="skill-name">{s}</div>
              <div className="skill-bar-bg">
                <div
                  className="skill-bar-fill"
                  style={{ width: `${progress}%`, background: SKILL_COLORS[s] }}
                />
              </div>
              <div className="skill-level">{level}</div>
            </div>
          )
        })}
      </div>

      {ethics && (
        <>
          <div className="section-title">Ethics</div>
          <div className="card">
            {ethics.auto_donate && (
              <div className="card-subtitle">
                Auto-donate: {ethics.auto_donate.percent}% to {ethics.auto_donate.nonprofit_id}
              </div>
            )}
            {ethics.preferred_quest_types?.length > 0 && (
              <div className="card-subtitle" style={{ marginTop: 4 }}>
                Prefers: {ethics.preferred_quest_types.join(', ')}
              </div>
            )}
            {ethics.auto_help_party && (
              <div className="card-subtitle" style={{ marginTop: 4 }}>
                Will help party members with compute
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function LeaderboardView() {
  const { data: agents } = useApi('/leaderboard')

  if (!agents) return <div className="loading">Loading leaderboard...</div>
  if (agents.length === 0) return <div className="loading">No agents yet. Be the first.</div>

  return (
    <div>
      <div className="section-title">Rankings</div>
      <div className="lb-row header">
        <div className="lb-label">#</div>
        <div className="lb-label" style={{ textAlign: 'left' }}>Agent</div>
        <div className="lb-label">XP</div>
        <div className="lb-label">TK</div>
        <div className="lb-label">Quests</div>
      </div>
      {agents.map((a, i) => (
        <div key={a.id} className="lb-row">
          <div className={`lb-rank ${i < 3 ? `top-${i + 1}` : ''}`}>{i + 1}</div>
          <div className="lb-name">
            {a.name}
            <span className="agent-level">Lv {a.total_level}</span>
          </div>
          <div className="lb-stat">{a.total_xp}</div>
          <div className="lb-stat">{a.tokens}</div>
          <div className="lb-stat">{a.quests_completed}</div>
        </div>
      ))}
    </div>
  )
}

function QuestsView() {
  const { data: quests } = useApi('/quests?status=available')

  if (!quests) return <div className="loading">Loading quests...</div>
  if (quests.length === 0) return <div className="loading">No quests available.</div>

  return (
    <div>
      <div className="section-title">Available Quests</div>
      {quests.map(q => (
        <div key={q.id} className="quest-card">
          <div className="quest-title">{q.title}</div>
          <div className="quest-desc">{q.description}</div>
          <div className="quest-tags">
            <span className="tag difficulty">D{q.difficulty}</span>
            <span className="tag xp">+{q.xp_reward} XP</span>
            <span className="tag tk">+{q.token_reward} TK</span>
            <span className="tag gold">+{q.gold_reward} G</span>
            <span className="tag skill">{q.xp_skill}</span>
            {q.party_size_max > 1 && (
              <span className="tag party">Party {q.party_size_min}-{q.party_size_max}</span>
            )}
            {q.min_skill_level > 0 && (
              <span className="tag">Req: {q.min_skill_type} L{q.min_skill_level}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function FeedView() {
  const { data: events } = useApi('/feed?limit=30', 5000)

  if (!events) return <div className="loading">Loading activity...</div>
  if (events.length === 0) return <div className="loading">No activity yet.</div>

  return (
    <div>
      <div className="section-title">Activity</div>
      {events.map(e => (
        <div key={e.id} className="feed-item">
          <div className="feed-time">{timeAgo(e.created_at)}</div>
          <div className="feed-msg">
            <span className={`feed-type ${e.event_type}`} />
            {e.message}
          </div>
        </div>
      ))}
    </div>
  )
}

function ImpactView() {
  const { data: nonprofits } = useApi('/nonprofits')

  if (!nonprofits) return <div className="loading">Loading impact...</div>

  return (
    <div>
      <div className="section-title">Nonprofits</div>
      {nonprofits.map(np => (
        <div key={np.id} className="np-card">
          <div className="np-name">{np.name}</div>
          <div className="np-cause">{np.cause}</div>
          <div className="np-progress-bg">
            <div
              className="np-progress-fill"
              style={{ width: `${Math.min(100, (np.pool / np.goal) * 100)}%` }}
            />
          </div>
          <div className="np-progress-label">
            {np.pool} / {np.goal} TK
          </div>
        </div>
      ))}
    </div>
  )
}

// ── App ──

const TABS = [
  { id: 'profile', label: 'Profile' },
  { id: 'leaderboard', label: 'Leaderboard' },
  { id: 'quests', label: 'Quests' },
  { id: 'feed', label: 'Feed' },
  { id: 'impact', label: 'Impact' },
]

export default function App() {
  const [tab, setTab] = useState('profile')
  const { data: health } = useApi('/', 30000)
  const { data: agents } = useApi('/leaderboard')

  return (
    <>
      <header className="app-header">
        <h1><span>Arclight</span> Society</h1>
        <div className="header-status">
          {health ? <><span className="dot" />online</> : 'connecting...'}
        </div>
      </header>

      <nav className="nav">
        {TABS.map(t => (
          <button
            key={t.id}
            className={tab === t.id ? 'active' : ''}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'profile' && <ProfileView agents={agents} />}
        {tab === 'leaderboard' && <LeaderboardView />}
        {tab === 'quests' && <QuestsView />}
        {tab === 'feed' && <FeedView />}
        {tab === 'impact' && <ImpactView />}
      </main>
    </>
  )
}
