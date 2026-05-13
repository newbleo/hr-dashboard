import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { getStats, triggerCollect } from '../api.js'

const SOURCE_COLORS = {
  saramin: '#4caf50',
  wanted: '#2196f3',
  jumpit: '#ff5722',
  peoplenjob: '#9c27b0',
}

const SOURCE_LABEL = {
  saramin: '사람인',
  wanted: '원티드',
  jumpit: '점핏',
  peoplenjob: '피플앤잡',
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [collecting, setCollecting] = useState(false)

  const load = async () => {
    try {
      const res = await getStats()
      setStats(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleCollect = async () => {
    setCollecting(true)
    try {
      await triggerCollect()
      await load()
    } finally {
      setCollecting(false)
    }
  }

  if (loading) return <p style={{ textAlign: 'center', marginTop: 80 }}>불러오는 중...</p>
  if (!stats) return null

  const pieData = stats.by_source.map(d => ({
    name: SOURCE_LABEL[d.source] || d.source,
    value: d.count,
    color: SOURCE_COLORS[d.source] || '#999',
  }))

  return (
    <div>
      <div style={styles.topRow}>
        <div className="card" style={styles.statCard}>
          <div style={styles.statLabel}>총 수집 공고</div>
          <div style={styles.statValue}>{stats.total.toLocaleString()}건</div>
        </div>
        {stats.by_source.map(d => (
          <div className="card" style={styles.statCard} key={d.source}>
            <div style={styles.statLabel}>{SOURCE_LABEL[d.source] || d.source}</div>
            <div style={{ ...styles.statValue, color: SOURCE_COLORS[d.source] }}>
              {d.count.toLocaleString()}건
            </div>
          </div>
        ))}
        <button onClick={handleCollect} disabled={collecting} style={styles.collectBtn}>
          {collecting ? '수집 중...' : '지금 수집'}
        </button>
      </div>

      <div style={styles.chartsRow}>
        <div className="card" style={{ flex: 1 }}>
          <h3 style={styles.chartTitle}>포털별 비율</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ flex: 2 }}>
          <h3 style={styles.chartTitle}>지역별 공고 TOP 10</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={stats.by_location} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="location" width={80} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3f51b5" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ marginTop: 24 }}>
        <h3 style={styles.chartTitle}>경력별 공고 분포</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={stats.by_experience}>
            <XAxis dataKey="experience" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#7c4dff" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

const styles = {
  topRow: { display: 'flex', gap: 16, alignItems: 'center', marginBottom: 24, flexWrap: 'wrap' },
  statCard: { flex: 1, minWidth: 140 },
  statLabel: { fontSize: 13, color: '#888', marginBottom: 8 },
  statValue: { fontSize: 28, fontWeight: 700, color: '#1a1a2e' },
  chartsRow: { display: 'flex', gap: 24, flexWrap: 'wrap' },
  chartTitle: { fontSize: 15, fontWeight: 600, marginBottom: 16, color: '#333' },
  collectBtn: {
    padding: '12px 24px',
    background: '#3f51b5',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 14,
    whiteSpace: 'nowrap',
  },
}
