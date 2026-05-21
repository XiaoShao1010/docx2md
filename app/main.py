import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger("docx2md")


async def periodic_cleanup(interval_seconds: int = 600):
    """Periodically clean up expired upload/output files."""
    from app.utils.file_utils import cleanup_expired_files
    from app.api.job_store import job_store
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            cleanup_expired_files()
            job_store.cleanup_expired(ttl_seconds=settings.temp_file_ttl_minutes * 60)
        except Exception:
            logger.exception("Cleanup task failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    cleanup_task.cancel()


app = FastAPI(title="DOCX2MD", version="1.0.0", lifespan=lifespan)
app.include_router(router)
