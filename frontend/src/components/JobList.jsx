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

const LOCATIONS = [
  { key: '', label: '전체 지역' },
  { key: '서울', label: '서울' },
  { key: '경기', label: '경기/판교' },
  { key: '부산', label: '부산' },
  { key: '인천', label: '인천' },
  { key: '대구', label: '대구' },
  { key: '대전', label: '대전' },
]

const BOOKMARK_KEY = 'jarjupjup_bookmarks'

function useBookmarks() {
  const [bookmarks, setBookmarks] = useState(() => {
    try { return JSON.parse(localStorage.getItem(BOOKMARK_KEY) || '{}') }
    catch { return {} }
  })

  const toggle = (job, e) => {
    e.preventDefault()
    e.stopPropagation()
    setBookmarks(prev => {
      const next = { ...prev }
      if (next[job.id]) delete next[job.id]
      else next[job.id] = job
      localStorage.setItem(BOOKMARK_KEY, JSON.stringify(next))
      return next
    })
  }

  return {
    isBookmarked: (id) => !!bookmarks[id],
    toggle,
    list: Object.values(bookmarks),
    count: Object.keys(bookmarks).length,
  }
}

function timeAgo(isoString) {
  if (!isoString) return null
  const diff = Math.floor((Date.now() - new Date(isoString + 'Z').getTime()) / 60000)
  if (diff < 1) return '방금 전'
  if (diff < 60) return `${diff}분 전 업데이트`
  if (diff < 1440) return `${Math.floor(diff / 60)}시간 전 업데이트`
  return `${Math.floor(diff / 1440)}일 전 업데이트`
}

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

function ShareButton({ url }) {
  const [copied, setCopied] = useState(false)

  const handle = (e) => {
    e.preventDefault()
    e.stopPropagation()
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button className={`share-btn${copied ? ' copied' : ''}`} onClick={handle} title="링크 복사">
      {copied ? '✓' : '↗'}
    </button>
  )
}

function JobCard({ job, isBookmarked, onBookmark }) {
  return (
    <div className="job-card-wrap">
      <a href={job.url} target="_blank" rel="noreferrer" className="job-card-link">
        <div className="job-card">
          <span className={`badge badge-${job.source}`}>
            {SOURCE_LABEL[job.source] || job.source}
          </span>
          <div className="job-card-body">
            <span className="job-company">{job.company}</span>
            <span className="job-divider">·</span>
            <span className="job-title">{job.title}</span>
          </div>
          <div className="job-card-right">
            {job.location && <span className="meta-chip">📍 {job.location}</span>}
            {job.experience && <span className="meta-chip">💼 {job.experience}</span>}
            <DdayBadge deadline={job.deadline} />
          </div>
        </div>
      </a>
      <div className="card-actions">
        <ShareButton url={job.url} />
        <button
          className={`bookmark-btn${isBookmarked ? ' active' : ''}`}
          onClick={(e) => onBookmark(job, e)}
          title={isBookmarked ? '북마크 해제' : '북마크'}
        >
          {isBookmarked ? '♥' : '♡'}
        </button>
      </div>
    </div>
  )
}

export default function JobList() {
  const [jobs, setJobs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [warming, setWarming] = useState(false)
  const [warmingCount, setWarmingCount] = useState(0)
  const [lastUpdated, setLastUpdated] = useState(null)

  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState('')
  const [source, setSource] = useState('')
  const [location, setLocation] = useState('')
  const [sort, setSort] = useState('latest')
  const [showBookmarks, setShowBookmarks] = useState(false)

  const { isBookmarked, toggle, list: bookmarkList, count: bookmarkCount } = useBookmarks()

  const MAX_RETRIES = 4
  const RETRY_DELAY = 15000

  const load = async (p, params, retry = 0) => {
    if (retry === 0) {
      setLoading(true)
      setWarming(false)
      setError(false)
      setWarmingCount(0)
    }
    try {
      const res = await getJobs({ page: p, size: 30, ...params })
      setJobs(res.data.items)
      setTotal(res.data.total)
      setPage(p)
      if (res.data.items.length > 0) setLastUpdated(res.data.items[0].fetched_at)
      setLoading(false)
      setWarming(false)
    } catch {
      if (retry < MAX_RETRIES) {
        setWarming(true)
        setWarmingCount(retry + 1)
        setTimeout(() => load(p, params, retry + 1), RETRY_DELAY)
      } else {
        setLoading(false)
        setWarming(false)
        setError(true)
      }
    }
  }

  const buildParams = (overrides = {}) => {
    const base = {
      sort,
      ...(keyword && { keyword }),
      ...(category && { category }),
      ...(source && { source }),
      ...(location && { location }),
    }
    return { ...base, ...overrides }
  }

  useEffect(() => { load(1, {}) }, [])

  const handleSearch = () => {
    setShowBookmarks(false)
    load(1, buildParams())
  }

  const handleCategory = (cat) => {
    setCategory(cat)
    setShowBookmarks(false)
    load(1, buildParams({ category: cat }))
  }

  const handleSource = (s) => {
    setSource(s)
    load(1, buildParams({ source: s }))
  }

  const handleLocation = (l) => {
    setLocation(l)
    load(1, buildParams({ location: l }))
  }

  const handleSort = (s) => {
    setSort(s)
    load(1, buildParams({ sort: s }))
  }

  const displayedJobs = showBookmarks ? bookmarkList : jobs
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
            className={`cat-tab${!showBookmarks && category === c.key ? ' active' : ''}`}
            onClick={() => handleCategory(c.key)}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* 필터 + 정렬 */}
      <div className="filter-bar">
        <div className="filter-left">
          <select className="filter-sm" value={source} onChange={e => handleSource(e.target.value)} disabled={showBookmarks}>
            <option value="">전체 포털</option>
            <option value="saramin">사람인</option>
            <option value="wanted">원티드</option>
            <option value="jumpit">점핏</option>
            <option value="peoplenjob">피플앤잡</option>
          </select>
          <select className="filter-sm" value={location} onChange={e => handleLocation(e.target.value)} disabled={showBookmarks}>
            {LOCATIONS.map(l => <option key={l.key} value={l.key}>{l.label}</option>)}
          </select>
          <div className="sort-toggle">
            <button className={`sort-btn${sort === 'latest' ? ' active' : ''}`} onClick={() => handleSort('latest')} disabled={showBookmarks}>최신순</button>
            <button className={`sort-btn${sort === 'deadline' ? ' active' : ''}`} onClick={() => handleSort('deadline')} disabled={showBookmarks}>마감임박순</button>
          </div>
          <button className={`bookmark-toggle${showBookmarks ? ' active' : ''}`} onClick={() => setShowBookmarks(s => !s)}>
            {showBookmarks ? '♥' : '♡'} 관심공고{bookmarkCount > 0 && ` ${bookmarkCount}`}
          </button>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="total-count">
            {showBookmarks ? `북마크 ${bookmarkList.length}건` : `총 ${total.toLocaleString()}건`}
          </div>
          {lastUpdated && !showBookmarks && (
            <div className="update-time">{timeAgo(lastUpdated)}</div>
          )}
        </div>
      </div>

      {/* 공고 목록 */}
      {!showBookmarks && loading ? (
        <div className="empty-state">
          {warming ? (
            <>
              서버 깨우는 중... ☕<br />
              <span style={{ fontSize: 13, color: '#bbb' }}>
                Render 무료 서버라 최대 60초 걸릴 수 있어요 ({warmingCount * 15}초 경과)
              </span>
            </>
          ) : '불러오는 중...'}
        </div>
      ) : !showBookmarks && error ? (
        <div className="empty-state">
          서버에 연결할 수 없어요.<br />
          <span style={{ fontSize: 13, color: '#bbb' }}>잠시 후 새로고침 해주세요.</span>
        </div>
      ) : displayedJobs.length === 0 ? (
        <div className="empty-state">
          {showBookmarks ? '아직 북마크한 공고가 없어요. ♡를 눌러 저장해보세요.' : '검색 결과가 없어요.'}
        </div>
      ) : (
        <>
          <div className="job-grid">
            {displayedJobs.map(job => (
              <JobCard
                key={job.id}
                job={job}
                isBookmarked={isBookmarked(job.id)}
                onBookmark={toggle}
              />
            ))}
          </div>

          {!showBookmarks && totalPages > 1 && (
            <div className="pagination">
              <button onClick={() => load(page - 1, buildParams())} disabled={page === 1} className="page-btn">이전</button>
              <span className="page-info">{page} / {totalPages}</span>
              <button onClick={() => load(page + 1, buildParams())} disabled={page === totalPages} className="page-btn">다음</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
