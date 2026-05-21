import shutil
import time
import logging

from app.config import settings

logger = logging.getLogger("docx2md")


def cleanup_expired_files():
    now = time.time()
    ttl = settings.temp_file_ttl_minutes * 60
    for directory in (settings.upload_dir, settings.output_dir):
        if not directory.exists():
            continue
        for item in directory.iterdir():
            try:
                if item.is_dir():
                    if now - item.stat().st_mtime > ttl:
                        shutil.rmtree(item)
                        logger.info("Cleaned up expired directory: %s", item)
                elif now - item.stat().st_mtime > ttl:
                    item.unlink()
                    logger.info("Cleaned up expired file: %s", item)
            except OSError:
                pass
