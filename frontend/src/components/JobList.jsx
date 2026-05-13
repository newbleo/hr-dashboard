import { useEffect, useState } from 'react'
import { getJobs } from '../api.js'

const SOURCE_LABEL = { saramin: '사람인', wanted: '원티드', jumpit: '점핏', peoplenjob: '피플앤잡' }

export default function JobList() {
  const [jobs, setJobs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)

  const [filters, setFilters] = useState({ source: '', keyword: '', location: '' })
  const [applied, setApplied] = useState({ source: '', keyword: '', location: '' })

  const load = async (p = 1, f = applied) => {
    setLoading(true)
    try {
      const params = { page: p, size: 20, ...Object.fromEntries(Object.entries(f).filter(([, v]) => v)) }
      const res = await getJobs(params)
      setJobs(res.data.items)
      setTotal(res.data.total)
      setPage(p)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleSearch = () => {
    setApplied(filters)
    load(1, filters)
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div>
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={styles.filterRow}>
          <select
            value={filters.source}
            onChange={e => setFilters(f => ({ ...f, source: e.target.value }))}
            style={styles.select}
          >
            <option value="">전체 포털</option>
            <option value="saramin">사람인</option>
            <option value="wanted">원티드</option>
            <option value="jumpit">점핏</option>
            <option value="peoplenjob">피플앤잡</option>
          </select>
          <input
            placeholder="키워드 (직무명, 회사명)"
            value={filters.keyword}
            onChange={e => setFilters(f => ({ ...f, keyword: e.target.value }))}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            style={styles.input}
          />
          <input
            placeholder="지역"
            value={filters.location}
            onChange={e => setFilters(f => ({ ...f, location: e.target.value }))}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            style={{ ...styles.input, maxWidth: 160 }}
          />
          <button onClick={handleSearch} style={styles.searchBtn}>검색</button>
        </div>
        <div style={{ fontSize: 13, color: '#888', marginTop: 12 }}>총 {total.toLocaleString()}건</div>
      </div>

      {loading ? (
        <p style={{ textAlign: 'center', marginTop: 60 }}>불러오는 중...</p>
      ) : (
        <>
          <div style={styles.grid}>
            {jobs.map(job => (
              <a key={job.id} href={job.url} target="_blank" rel="noreferrer" style={styles.cardLink}>
                <div className="card" style={styles.jobCard}>
                  <div style={styles.jobTop}>
                    <span className={`badge badge-${job.source}`}>{SOURCE_LABEL[job.source]}</span>
                    {job.deadline && (
                      <span style={styles.deadline}>~{job.deadline}</span>
                    )}
                  </div>
                  <div style={styles.jobTitle}>{job.title}</div>
                  <div style={styles.company}>{job.company}</div>
                  <div style={styles.meta}>
                    {job.location && <span>📍 {job.location}</span>}
                    {job.experience && <span>💼 {job.experience}</span>}
                    {job.salary && <span>💰 {job.salary}</span>}
                  </div>
                </div>
              </a>
            ))}
          </div>

          {totalPages > 1 && (
            <div style={styles.pagination}>
              <button onClick={() => load(page - 1)} disabled={page === 1} style={styles.pageBtn}>이전</button>
              <span style={{ fontSize: 14 }}>{page} / {totalPages}</span>
              <button onClick={() => load(page + 1)} disabled={page === totalPages} style={styles.pageBtn}>다음</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

const styles = {
  filterRow: { display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' },
  select: { padding: '10px 14px', border: '1px solid #ddd', borderRadius: 8, fontSize: 14 },
  input: { flex: 1, padding: '10px 14px', border: '1px solid #ddd', borderRadius: 8, fontSize: 14 },
  searchBtn: {
    padding: '10px 24px', background: '#3f51b5', color: '#fff',
    border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: 14,
  },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 },
  cardLink: { textDecoration: 'none', color: 'inherit' },
  jobCard: { transition: 'box-shadow 0.15s', cursor: 'pointer' },
  jobTop: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  deadline: { fontSize: 12, color: '#e53935' },
  jobTitle: { fontSize: 15, fontWeight: 600, marginBottom: 6, lineHeight: 1.4 },
  company: { fontSize: 13, color: '#555', marginBottom: 12 },
  meta: { display: 'flex', gap: 12, fontSize: 12, color: '#777', flexWrap: 'wrap' },
  pagination: { display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 20, marginTop: 40 },
  pageBtn: {
    padding: '8px 20px', border: '1px solid #ddd', borderRadius: 8,
    cursor: 'pointer', background: '#fff', fontSize: 14,
  },
}
