"""Simple in-memory job store for tracking conversion status."""

import time
import threading
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Job:
    job_id: str
    status: str = "pending"  # pending, processing, completed, failed
    filename: str | None = None
    image_count: int = 0
    footnote_count: int = 0
    toc_detected: bool = False
    toc_generated: bool = False
    math_formula_count: int = 0
    warnings: list[str] = field(default_factory=list)
    output_path: Path | None = None
    created_at: float = field(default_factory=time.time)
    error: str | None = None


class JobStore:
    """Thread-safe in-memory job store."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str) -> Job:
        job = Job(job_id=job_id)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs):
        with self._lock:
            if job := self._jobs.get(job_id):
                for key, value in kwargs.items():
                    setattr(job, key, value)

    def remove(self, job_id: str):
        with self._lock:
            self._jobs.pop(job_id, None)

    def cleanup_expired(self, ttl_seconds: int = 3600):
        now = time.time()
        with self._lock:
            expired = [
                jid for jid, job in self._jobs.items()
                if now - job.created_at > ttl_seconds
            ]
            for jid in expired:
                del self._jobs[jid]


job_store = JobStore()
