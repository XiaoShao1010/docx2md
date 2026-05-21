import uuid

from fastapi import UploadFile, HTTPException

from app.config import settings


async def validate_docx(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{suffix}" not in settings.allowed_extensions:
        raise HTTPException(400, f"File type .{suffix} not allowed. Only .docx is accepted.")
    content = await file.read(1024)
    await file.seek(0)
    if not content[:4] == b"PK\x03\x04":
        raise HTTPException(400, "File is not a valid ZIP/DOCX format.")
    return file.filename


def generate_job_id() -> str:
    return uuid.uuid4().hex[:12]
