import httpx
from typing import List, Dict

API_URL = "https://jumpit-api.saramin.co.kr/api/positions"

HR_KEYWORDS = ["인사", "채용", "HR", "노무", "조직문화"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://jumpit.saramin.co.kr/",
}


async def fetch_jobs() -> List[Dict]:
    results = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
        for keyword in HR_KEYWORDS:
            page = 1
            while True:
                try:
                    resp = await client.get(API_URL, params={
                        "keyword": keyword,
                        "sort": "rsp_rate",
                        "page": page,
                    })
                    if resp.status_code != 200:
                        break

                    data = resp.json()
                    result = data.get("result", {})
                    positions = result.get("positions", [])
                    total = result.get("totalCount", 0)

                    if not positions:
                        break

                    for pos in positions:
                        job_id = pos.get("id")
                        if job_id and job_id not in seen_ids:
                            seen_ids.add(job_id)
                            results.append(_normalize(pos))

                    if page * 20 >= total:
                        break
                    page += 1

                except Exception as e:
                    print(f"[점핏] {keyword} p{page} 예외: {e}")
                    break

    return results


def _normalize(pos: Dict) -> Dict:
    return {
        "source": "jumpit",
        "external_id": f"jumpit_{pos.get('id', '')}",
        "title": pos.get("title", ""),
        "company": pos.get("companyName", ""),
        "location": pos.get("locations", [""])[0] if pos.get("locations") else "",
        "experience": pos.get("minCareer", ""),
        "job_category": pos.get("jobCategory", ""),
        "salary": "",
        "url": f"https://jumpit.saramin.co.kr/position/{pos.get('id', '')}",
        "deadline": pos.get("closedAt", ""),
        "description": "",
    }
