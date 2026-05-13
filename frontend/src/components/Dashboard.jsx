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

function bucketExperience(rawData) {
  const buckets = { '인턴': 0, '신입': 0, '3년이상': 0, '5년이상': 0, '경력무관': 0 }
  rawData.forEach(({ experience: exp, count }) => {
    const s = (exp || '').toLowerCase()
    if (s.includes('인턴')) {
      buckets['인턴'] += count
    } else if (s.includes('무관') || s.includes('관계없')) {
      buckets['경력무관'] += count
    } else if (s.includes('신입') && !s.includes('경력')) {
      buckets['신입'] += count
    } else {
      const m = s.match(/(\d+)/)
      if (m) {
        const y = parseInt(m[1])
        if (y >= 5) buckets['5년이상'] += count
        else if (y >= 3) buckets['3년이상'] += count
        else buckets['신입'] += count
      } else if (s.includes('신입')) {
        buckets['신입'] += count
      } else {
        buckets['경력무관'] += count
      }
    }
  })
  return Object.entries(buckets).map(([experience, count]) => ({ experience, count }))
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

  const expData = bucketExperience(stats.by_experience || [])
  const catData = (stats.by_category || []).map(d => ({ ...d, name: d.category }))

  return (
    <div>
      <div className="stat-row">
        <div className="card stat-card">
          <div className="stat-label">총 수집 공고</div>
          <div className="stat-value">{stats.total.toLocaleString()}건</div>
        </div>
        {stats.by_source.map(d => (
          <div className="card stat-card" key={d.source}>
            <div className="stat-label">{SOURCE_LABEL[d.source] || d.source}</div>
            <div className="stat-value" style={{ color: SOURCE_COLORS[d.source] }}>
              {d.count.toLocaleString()}건
            </div>
          </div>
        ))}
        <button onClick={handleCollect} disabled={collecting} className="collect-btn">
          {collecting ? '수집 중...' : '지금 수집'}
        </button>
      </div>

      <div className="charts-row">
        <div className="card chart-col-sm">
          <h3 className="chart-title">포털별 비율</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={false}>
                {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Pie>
              <Tooltip />
              <Legend iconSize={10} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card chart-col-lg">
          <h3 className="chart-title">직무별 공고 TOP 10</h3>
          {catData.length === 0 ? (
            <p style={{ color: '#aaa', fontSize: 13, marginTop: 16 }}>직무 데이터 수집 중...</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={catData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="category" width={100} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#3f51b5" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h3 className="chart-title">경력별 공고 분포</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={expData} margin={{ left: 0, right: 16 }}>
            <XAxis dataKey="experience" tick={{ fontSize: 13 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="count" fill="#7c4dff" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
