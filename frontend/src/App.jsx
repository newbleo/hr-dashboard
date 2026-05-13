import { Analytics } from '@vercel/analytics/react'
import JobList from './components/JobList.jsx'

export default function App() {
  return (
    <div>
      <header style={styles.header}>
        <div className="container" style={styles.headerInner}>
          <div style={styles.brand}>
            <h1 style={styles.logo}>잡줍줍 🧺</h1>
            <span style={styles.tagline}>HR 채용공고 한방에 줍줍</span>
          </div>
        </div>
      </header>
      <main className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
        <JobList />
      </main>
      <footer style={styles.footer}>
        <div className="container" style={styles.footerInner}>
          <span>만든 사람 <strong>밍수박사</strong></span>
          <a
            href="https://www.linkedin.com/in/minsooim"
            target="_blank"
            rel="noreferrer"
            style={styles.footerLink}
          >
            LinkedIn →
          </a>
        </div>
      </footer>
      <Analytics />
    </div>
  )
}

const styles = {
  header: {
    background: '#fff',
    borderBottom: '1px solid #eee',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  headerInner: {
    display: 'flex',
    alignItems: 'center',
    height: 56,
  },
  brand: {
    display: 'flex',
    alignItems: 'baseline',
    gap: 10,
  },
  logo: {
    fontSize: 20,
    fontWeight: 800,
    color: '#3f51b5',
    letterSpacing: '-0.5px',
  },
  tagline: {
    fontSize: 12,
    color: '#aaa',
    fontWeight: 400,
  },
  footer: {
    borderTop: '1px solid #eee',
    background: '#fff',
    padding: '20px 0',
    marginTop: 8,
  },
  footerInner: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    fontSize: 13,
    color: '#aaa',
  },
  footerLink: {
    color: '#3f51b5',
    textDecoration: 'none',
    fontWeight: 600,
  },
}
