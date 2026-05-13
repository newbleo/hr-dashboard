import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Render 배포 시 /data 디스크 마운트 경로 사용, 로컬은 현재 디렉토리
_db_dir = "/data" if os.path.isdir("/data") else "."
DATABASE_URL = f"sqlite+aiosqlite:///{_db_dir}/hr_dashboard.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
