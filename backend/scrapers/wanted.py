import httpx
from typing import List, Dict

WANTED_API_URL = "https://www.wanted.co.kr/api/v4/jobs"

# 6: 인사/총무, 8: 법무/특허/사무
HR_GROUP_IDS = [6, 8]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.wanted.co.kr/",
}


async def fetch_jobs() -> List[Dict]:
    results = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        for group_id in HR_GROUP_IDS:
            try:
                offset = 0
                max_pages = 10  # 페이지당 100건, 최대 1000건
                for _ in range(max_pages):
                    resp = await client.get(WANTED_API_URL, params={
                        "country": "kr",
                        "job_sort": "job.latest_order",
                        "job_group_id": group_id,
                        "limit": 100,
                        "offset": offset,
                    })
                    if resp.status_code != 200:
                        print(f"[원티드] group_id={group_id} 오류: {resp.status_code}")
                        break

                    data = resp.json()
                    jobs = data.get("data", [])
                    if not jobs:
                        break

                    for job in jobs:
                        job_id = job.get("id")
                        if job_id and job_id not in seen_ids:
                            seen_ids.add(job_id)
                            results.append(_normalize(job))

                    if len(jobs) < 100:
                        break
                    offset += 100

            except Exception as e:
                print(f"[원티드] group_id={group_id} 예외: {e}")

    return results


def _normalize(job: Dict) -> Dict:
    company = job.get("company", {})
    return {
        "source": "wanted",
        "external_id": f"wanted_{job.get('id', '')}",
        "title": job.get("position", ""),
        "company": company.get("name", ""),
        "location": job.get("address", {}).get("location", ""),
        "experience": "",
        "job_category": "",
        "salary": "",
        "url": f"https://www.wanted.co.kr/wd/{job.get('id', '')}",
        "deadline": job.get("due_time", ""),
        "description": job.get("description", "")[:500] if job.get("description") else "",
    }
