import { useEffect, useState } from 'react'
import { getJobs } from '../api.js'

const SOURCE_LABEL = {
  saramin: '사람인',
  wanted: '원티드',
  jumpit: '점핏',
  peoplenjob: '피플앤잡',
}

const CATEGORIES = [
  { key: '', label: '전체' },
  { key: '채용담당', label: '채용담당' },
  { key: 'HRD', label: 'HRD/교육' },
  { key: '노무', label: '노무' },
  { key: '조직문화', label: '조직문화' },
  { key: '인사기획', label: '인사기획' },
  { key: '총무', label: '총무' },
]

function calcDday(deadline) {
  if (!deadline) return null
  const cleaned = deadline.replace(/[~\s]/g, '')
  if (/상시|채용시|수시|연중|없음/.test(cleaned)) return 'always'

  const m = cleaned.match(/(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})/)
  let d
  if (m) {
    d = new Date(parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]))
  } else {
    d = new Date(cleaned)
  }
  if (isNaN(d.getTime())) return null

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.ceil((d - today) / (1000 * 60 * 60 * 24))
}

function DdayBadge({ deadline }) {
  const dday = calcDday(deadline)
  if (dday === null) return null
  if (dday === 'always') return <span className="dday dday-always">상시</span>
  if (dday < 0) return <span className="dday dday-closed">마감</span>
  if (dday === 0) return <span className="dday dday-urgent">D-day</span>
  if (dday <= 3) return <span className="dday dday-urgent">D-{dday}</span>
  if (dday <= 7) return <span className="dday dday-warn">D-{dday}</span>
  return <span className="dday dday-normal">D-{dday}</span>
}

export default function JobList() {
  const [jobs, setJobs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)

  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState('')
  const [source, setSource] = useState('')
  const [sort, setSort] = useState('latest')

  const load = async (p, params) => {
    setLoading(true)
    try {
      const res = await getJobs({ page: p, size: 20, ...params })
      setJobs(res.data.items)
      setTotal(res.data.total)
      setPage(p)
    } finally {
      setLoading(false)
    }
  }

  const buildParams = (overrides = {}) => {
    const base = {
      sort,
      ...(keyword && { keyword }),
      ...(category && { category }),
      ...(source && { source }),
    }
    return { ...base, ...overrides }
  }

  useEffect(() => { load(1, {}) }, [])

  const handleSearch = () => load(1, buildParams())

  const handleCategory = (cat) => {
    setCategory(cat)
    load(1, buildParams({ category: cat }))
  }

  const handleSource = (s) => {
    setSource(s)
    load(1, buildParams({ source: s }))
  }

  const handleSort = (s) => {
    setSort(s)
    load(1, buildParams({ sort: s }))
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div>
      {/* 검색창 */}
      <div className="search-wrap">
        <input
          className="search-main"
          placeholder="회사명, 직무명으로 검색"
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
        />
        <button className="search-btn-main" onClick={handleSearch}>검색</button>
      </div>

      {/* 카테고리 탭 */}
      <div className="cat-tabs">
        {CATEGORIES.map(c => (
          <button
            key={c.key}
            className={`cat-tab${category === c.key ? ' active' : ''}`}
            onClick={() => handleCategory(c.key)}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* 필터 + 정렬 */}
      <div className="filter-bar">
        <div className="filter-left">
          <select className="filter-sm" value={source} onChange={e => handleSource(e.target.value)}>
            <option value="">전체 포털</option>
            <option value="saramin">사람인</option>
            <option value="wanted">원티드</option>
            <option value="jumpit">점핏</option>
            <option value="peoplenjob">피플앤잡</option>
          </select>
          <div className="sort-toggle">
            <button
              className={`sort-btn${sort === 'latest' ? ' active' : ''}`}
              onClick={() => handleSort('latest')}
            >최신순</button>
            <button
              className={`sort-btn${sort === 'deadline' ? ' active' : ''}`}
              onClick={() => handleSort('deadline')}
            >마감임박순</button>
          </div>
        </div>
        <span className="total-count">총 {total.toLocaleString()}건</span>
      </div>

      {/* 공고 목록 */}
      {loading ? (
        <div className="empty-state">불러오는 중...</div>
      ) : jobs.length === 0 ? (
        <div className="empty-state">검색 결과가 없어요.</div>
      ) : (
        <>
          <div className="job-grid">
            {jobs.map(job => (
              <a
                key={job.id}
                href={job.url}
                target="_blank"
                rel="noreferrer"
                className="job-card-link"
              >
                <div className="job-card">
                  <div className="job-card-top">
                    <span className={`badge badge-${job.source}`}>
                      {SOURCE_LABEL[job.source] || job.source}
                    </span>
                    <DdayBadge deadline={job.deadline} />
                  </div>
                  <div className="job-company">{job.company}</div>
                  <div className="job-title">{job.title}</div>
                  <div className="job-meta">
                    {job.location && <span className="meta-chip">📍 {job.location}</span>}
                    {job.experience && <span className="meta-chip">💼 {job.experience}</span>}
                    {job.salary && <span className="meta-chip">💰 {job.salary}</span>}
                  </div>
                </div>
              </a>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => load(page - 1, buildParams())}
                disabled={page === 1}
                className="page-btn"
              >이전</button>
              <span className="page-info">{page} / {totalPages}</span>
              <button
                onClick={() => load(page + 1, buildParams())}
                disabled={page === totalPages}
                className="page-btn"
              >다음</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
