import httpx
import re
from bs4 import BeautifulSoup
from typing import List, Dict

BASE_URL = "https://www.peoplenjob.com"
SEARCH_URL = f"{BASE_URL}/jobs"

HR_KEYWORDS = ["HR", "인사담당", "채용담당", "인재개발", "노무"]

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
            for page in range(1, 4):
                try:
                    resp = await client.get(SEARCH_URL, params={
                        "keyword": keyword,
                        "page": page,
                    })
                    if resp.status_code != 200:
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    cards = soup.select(".jd-card")

                    if not cards:
                        break

                    for card in cards:
                        parsed = _parse_card(card)
                        if parsed and parsed["external_id"] not in seen_ids:
                            seen_ids.add(parsed["external_id"])
                            results.append(parsed)

                    if len(cards) < 20:
                        break

                except Exception as e:
                    print(f"[피플앤잡] {keyword} p{page} 예외: {e}")
                    break

    return results


def _parse_card(card) -> Dict | None:
    try:
        title_el = card.select_one(".jd-card-title")
        company_el = card.select_one(".jd-card-company")
        location_el = card.select_one(".jd-card-meta-location-text")
        link_el = card.select_one("a[href]")

        if not title_el or not link_el:
            return None

        href = link_el.get("href", "")
        job_id = re.search(r"/jobs/(\d+)", href)
        ext_id = job_id.group(1) if job_id else href

        return {
            "source": "peoplenjob",
            "external_id": f"peoplenjob_{ext_id}",
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "",
            "location": location_el.get_text(strip=True) if location_el else "",
            "experience": "",
            "job_category": "HR/인사",
            "salary": "",
            "url": f"{BASE_URL}{href}" if href.startswith("/") else href,
            "deadline": "",
            "description": "",
        }
    except Exception:
        return None
