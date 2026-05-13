import os
import httpx
from typing import List, Dict

SARAMIN_API_URL = "https://oapi.saramin.co.kr/job-search"

HR_KEYWORDS = ["HR", "인사", "채용", "인재개발", "노무", "조직문화"]


async def fetch_jobs(keywords: List[str] = None) -> List[Dict]:
    api_key = os.getenv("SARAMIN_API_KEY", "")
    if not api_key:
        print("[사람인] API 키 없음 — .env에 SARAMIN_API_KEY 설정 필요")
        return []

    search_keywords = keywords or HR_KEYWORDS
    results = []

    async with httpx.AsyncClient(timeout=10) as client:
        for keyword in search_keywords:
            try:
                resp = await client.get(SARAMIN_API_URL, params={
                    "access-key": api_key,
                    "keywords": keyword,
                    "job_type": 1,
                    "count": 100,
                    "fields": "posting-timestamp,expiration-timestamp,keyword-code,sal-code",
                })
                if resp.status_code != 200:
                    print(f"[사람인] {keyword} 오류: {resp.status_code}")
                    continue

                data = resp.json()
                jobs = data.get("jobs", {}).get("job", [])
                for job in jobs:
                    results.append(_normalize(job))
            except Exception as e:
                print(f"[사람인] {keyword} 예외: {e}")

    return results


def _normalize(job: Dict) -> Dict:
    position = job.get("position", {})
    salary = job.get("salary", {})
    return {
        "source": "saramin",
        "external_id": f"saramin_{job.get('id', '')}",
        "title": position.get("title", ""),
        "company": job.get("company", {}).get("detail", {}).get("name", ""),
        "location": position.get("location", {}).get("name", ""),
        "experience": position.get("experience-level", {}).get("name", ""),
        "job_category": position.get("job-type", {}).get("name", ""),
        "salary": salary.get("name", ""),
        "url": job.get("url", ""),
        "deadline": job.get("expiration-date", ""),
        "description": position.get("title", ""),
    }
