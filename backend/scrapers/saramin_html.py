import httpx
import re
from bs4 import BeautifulSoup
from typing import List, Dict

BASE_URL = "https://www.saramin.co.kr"
SEARCH_URL = f"{BASE_URL}/zf_user/search/recruit"

HR_KEYWORDS = ["HR", "인사담당", "채용담당", "인재개발", "노무사"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}


async def fetch_jobs() -> List[Dict]:
    results = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=15, headers=HEADERS, follow_redirects=True) as client:
        for keyword in HR_KEYWORDS:
            for page in range(1, 4):  # 최대 3페이지
                try:
                    resp = await client.get(SEARCH_URL, params={
                        "searchType": "search",
                        "searchword": keyword,
                        "recruitPage": page,
                        "recruitPageCount": 40,
                    })
                    if resp.status_code != 200:
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    items = soup.select(".item_recruit")

                    if not items:
                        break

                    for item in items:
                        parsed = _parse_item(item)
                        if parsed and parsed["external_id"] not in seen_ids:
                            seen_ids.add(parsed["external_id"])
                            results.append(parsed)

                except Exception as e:
                    print(f"[사람인] {keyword} p{page} 예외: {e}")
                    break

    return results


def _parse_item(item) -> Dict | None:
    try:
        title_el = item.select_one("h2.job_tit a")
        company_el = item.select_one("strong.corp_name")
        deadline_el = item.select_one("span.date")
        condition_spans = item.select("div.job_condition span")

        if not title_el:
            return None

        href = title_el.get("href", "")
        rec_idx = re.search(r"rec_idx=(\d+)", href)
        job_id = rec_idx.group(1) if rec_idx else href

        # job_condition 순서: 지역, 고용형태, 경력, 급여, 마감
        conditions = [s.get_text(strip=True) for s in condition_spans]
        location = conditions[0] if len(conditions) > 0 else ""
        experience = conditions[2] if len(conditions) > 2 else ""
        salary = conditions[3] if len(conditions) > 3 else ""

        return {
            "source": "saramin",
            "external_id": f"saramin_{job_id}",
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "",
            "location": location,
            "experience": experience,
            "job_category": "HR/인사",
            "salary": salary,
            "url": f"{BASE_URL}{href}" if href.startswith("/") else href,
            "deadline": deadline_el.get_text(strip=True) if deadline_el else "",
            "description": "",
        }
    except Exception:
        return None
