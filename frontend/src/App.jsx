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
}
