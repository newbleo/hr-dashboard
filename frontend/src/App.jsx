import { useState } from 'react'
import Dashboard from './components/Dashboard.jsx'
import JobList from './components/JobList.jsx'

const TABS = ['대시보드', '채용공고']

export default function App() {
  const [tab, setTab] = useState(0)

  return (
    <div>
      <header style={styles.header}>
        <div className="container" style={styles.headerInner}>
          <h1 style={styles.logo}>잡줍줍 🧺</h1>
          <span style={styles.tagline} className="tagline-hide">채용공고 한방에 줍줍</span>
          <nav style={styles.nav}>
            {TABS.map((t, i) => (
              <button
                key={t}
                onClick={() => setTab(i)}
                style={{ ...styles.navBtn, ...(tab === i ? styles.navBtnActive : {}) }}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="container" style={{ paddingTop: 32, paddingBottom: 48 }}>
        {tab === 0 && <Dashboard />}
        {tab === 1 && <JobList />}
      </main>
    </div>
  )
}

const styles = {
  header: {
    background: '#fff',
    borderBottom: '1px solid #e8eaf6',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  headerInner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: 64,
  },
  logo: {
    fontSize: 20,
    fontWeight: 800,
    color: '#3f51b5',
    letterSpacing: '-0.5px',
  },
  tagline: {
    fontSize: 12,
    color: '#999',
    marginLeft: 8,
    fontWeight: 400,
  },
  nav: { display: 'flex', gap: 8 },
  navBtn: {
    padding: '8px 20px',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500,
    background: 'transparent',
    color: '#666',
  },
  navBtnActive: {
    background: '#e8eaf6',
    color: '#3f51b5',
  },
}
