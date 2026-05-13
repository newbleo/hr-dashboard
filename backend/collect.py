import os
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from database import AsyncSessionLocal
from models import JobPosting
from scrapers import saramin, saramin_html, wanted, jumpit, peoplenjob


async def cleanup_old_postings():
    cutoff = datetime.utcnow() - timedelta(days=30)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(JobPosting).where(JobPosting.fetched_at < cutoff)
        )
        await session.commit()
        print(f"[정리] 30일 초과 공고 {result.rowcount}건 삭제")


async def collect_all():
    print("[수집 시작]")
    all_jobs = []

    # 사람인: API 키 있으면 API, 없으면 HTML 스크래핑
    if os.getenv("SARAMIN_API_KEY"):
        saramin_jobs = await saramin.fetch_jobs()
    else:
        saramin_jobs = await saramin_html.fetch_jobs()

    wanted_jobs = await wanted.fetch_jobs()
    jumpit_jobs = await jumpit.fetch_jobs()
    peoplenjob_jobs = await peoplenjob.fetch_jobs()

    all_jobs.extend(saramin_jobs)
    all_jobs.extend(wanted_jobs)
    all_jobs.extend(jumpit_jobs)
    all_jobs.extend(peoplenjob_jobs)

    print(
        f"[수집 완료] 사람인 {len(saramin_jobs)}건 | 원티드 {len(wanted_jobs)}건 | "
        f"점핏 {len(jumpit_jobs)}건 | 피플앤잡 {len(peoplenjob_jobs)}건"
    )

    saved = 0
    for job_data in all_jobs:
        if not job_data.get("external_id") or not job_data.get("title"):
            continue
        async with AsyncSessionLocal() as session:
            try:
                posting = JobPosting(**job_data)
                session.add(posting)
                await session.commit()
                saved += 1
            except IntegrityError:
                await session.rollback()
            except Exception as e:
                await session.rollback()
                print(f"[저장 오류] {e}")

    print(f"[DB 저장] 신규 {saved}건")
    await cleanup_old_postings()
    return saved
