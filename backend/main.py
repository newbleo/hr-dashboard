import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from dotenv import load_dotenv

from database import init_db, get_db
from models import JobPosting
from collect import collect_all
import scheduler as job_scheduler

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    job_scheduler.start()
    asyncio.create_task(collect_all())  # 포트 열고 난 뒤 백그라운드 수집
    yield
    job_scheduler.stop()


app = FastAPI(title="HR Dashboard API", lifespan=lifespan)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/jobs")
async def get_jobs(
    source: str | None = None,
    keyword: str | None = None,
    location: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(JobPosting).order_by(desc(JobPosting.fetched_at))

    if source:
        stmt = stmt.where(JobPosting.source == source)
    if keyword:
        stmt = stmt.where(
            JobPosting.title.ilike(f"%{keyword}%") |
            JobPosting.company.ilike(f"%{keyword}%")
        )
    if location:
        stmt = stmt.where(JobPosting.location.ilike(f"%{location}%"))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [_serialize(r) for r in rows],
    }


@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(JobPosting))).scalar_one()

    by_source = (await db.execute(
        select(JobPosting.source, func.count()).group_by(JobPosting.source)
    )).all()

    by_location = (await db.execute(
        select(JobPosting.location, func.count())
        .where(JobPosting.location != None, JobPosting.location != "")
        .group_by(JobPosting.location)
        .order_by(desc(func.count()))
        .limit(10)
    )).all()

    by_experience = (await db.execute(
        select(JobPosting.experience, func.count())
        .where(JobPosting.experience != None, JobPosting.experience != "")
        .group_by(JobPosting.experience)
        .order_by(desc(func.count()))
    )).all()

    by_category = (await db.execute(
        select(JobPosting.job_category, func.count())
        .where(JobPosting.job_category != None, JobPosting.job_category != "")
        .group_by(JobPosting.job_category)
        .order_by(desc(func.count()))
        .limit(10)
    )).all()

    return {
        "total": total,
        "by_source": [{"source": s, "count": c} for s, c in by_source],
        "by_experience": [{"experience": e, "count": c} for e, c in by_experience],
        "by_category": [{"category": cat, "count": c} for cat, c in by_category],
    }


@app.post("/api/collect")
async def trigger_collect():
    saved = await collect_all()
    return {"saved": saved}


def _serialize(job: JobPosting) -> dict:
    return {
        "id": job.id,
        "source": job.source,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "experience": job.experience,
        "salary": job.salary,
        "url": job.url,
        "deadline": job.deadline,
        "fetched_at": job.fetched_at.isoformat() if job.fetched_at else None,
    }
