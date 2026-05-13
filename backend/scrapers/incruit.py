import httpx
from bs4 import BeautifulSoup
from typing import List, Dict

SEARCH_URL = "https://search.incruit.com/list/search.asp"

HR_KEYWORDS = [
    "HR", "인사담당", "채용담당", "인재개발", "노무",
    "인사총무", "조직문화", "인사기획", "HRD", "HRBP",
    "인사팀", "총무", "채용매니저",
]

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
                        "col": "job",
                        "query": keyword,
                        "page": page,
                    })
                    if resp.status_code != 200:
                        print(f"[인크루트] {keyword} 오류: {resp.status_code}")
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    items = soup.select(".joblist_area .job_info_wrap") or soup.select(".job_list li")

                    if not items:
                        items = soup.select("[class*='job_item']") or soup.select(".list_wrap li")

                    if not items:
                        break

                    for item in items:
                        parsed = _parse_item(item)
                        if parsed and parsed["external_id"] not in seen_ids:
                            seen_ids.add(parsed["external_id"])
                            results.append(parsed)

                except Exception as e:
                    print(f"[인크루트] {keyword} p{page} 예외: {e}")
                    break

    return results


def _parse_item(item) -> Dict | None:
    try:
        title_el = item.select_one(".job_tit a, .tit a, a.tit")
        company_el = item.select_one(".corp_name a, .company a, .corp a")
        location_el = item.select_one(".work_place, .location, .loc")
        exp_el = item.select_one(".exp, .career, .experience")
        deadline_el = item.select_one(".date, .deadline, .limit_date")

        if not title_el:
            return None

        href = title_el.get("href", "")
        job_id = href.split("jobno=")[-1].split("&")[0] if "jobno=" in href else href.split("/")[-1]

        return {
            "source": "incruit",
            "external_id": f"incruit_{job_id}",
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "",
            "location": location_el.get_text(strip=True) if location_el else "",
            "experience": exp_el.get_text(strip=True) if exp_el else "",
            "job_category": "HR/인사",
            "salary": "",
            "url": href if href.startswith("http") else f"https://search.incruit.com{href}",
            "deadline": deadline_el.get_text(strip=True) if deadline_el else "",
            "description": "",
        }
    except Exception:
        return None
