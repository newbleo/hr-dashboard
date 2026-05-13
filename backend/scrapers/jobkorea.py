import httpx
from bs4 import BeautifulSoup
from typing import List, Dict

SEARCH_URL = "https://www.jobkorea.co.kr/Search/"

HR_KEYWORDS = [
    "인사담당자", "HR", "채용담당", "인재개발",
    "인사총무", "조직문화", "인사기획", "HRD", "노무",
    "HRBP", "인사팀", "총무", "채용매니저",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def fetch_jobs() -> List[Dict]:
    results = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=15, headers=HEADERS, follow_redirects=True) as client:
        for keyword in HR_KEYWORDS:
            for page in range(1, 4):  # 최대 3페이지
                try:
                    resp = await client.get(SEARCH_URL, params={
                        "stext": keyword,
                        "tabType": "recruit",
                        "Page_No": page,
                    })
                    if resp.status_code != 200:
                        print(f"[잡코리아] {keyword} 오류: {resp.status_code}")
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    job_items = soup.select("div.list-post .post-item")

                    if not job_items:
                        break

                    for item in job_items:
                        normalized = _parse_item(item)
                        if normalized and normalized["external_id"] not in seen_ids:
                            seen_ids.add(normalized["external_id"])
                            results.append(normalized)

                except Exception as e:
                    print(f"[잡코리아] {keyword} p{page} 예외: {e}")
                    break

    return results


def _parse_item(item) -> Dict | None:
    try:
        title_el = item.select_one(".title")
        company_el = item.select_one(".name")
        location_el = item.select_one(".loc")
        exp_el = item.select_one(".exp")
        deadline_el = item.select_one(".date")
        link_el = item.select_one("a.post-url")

        if not title_el or not link_el:
            return None

        href = link_el.get("href", "")
        job_id = href.split("_")[-1] if "_" in href else href

        return {
            "source": "jobkorea",
            "external_id": f"jobkorea_{job_id}",
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "",
            "location": location_el.get_text(strip=True) if location_el else "",
            "experience": exp_el.get_text(strip=True) if exp_el else "",
            "job_category": "HR/인사",
            "salary": "",
            "url": f"https://www.jobkorea.co.kr{href}" if href.startswith("/") else href,
            "deadline": deadline_el.get_text(strip=True) if deadline_el else "",
            "description": "",
        }
    except Exception:
        return None
