from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from collect import collect_all

scheduler = AsyncIOScheduler()


def start():
    scheduler.add_job(
        collect_all,
        trigger=IntervalTrigger(hours=6),
        id="collect_jobs",
        replace_existing=True,
    )
    scheduler.start()


def stop():
    scheduler.shutdown()
