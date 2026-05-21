import json
import logging
import sys
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

from app.config import settings
from app.models import ConversionResponse
from app.converter.core import convert_docx
from app.api.dependencies import validate_docx, generate_job_id
from app.api.job_store import job_store, Job

logger = logging.getLogger("docx2md")

router = APIRouter()


def _get_template_path() -> Path:
    """Get the template path, handling PyInstaller bundled mode."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "app" / "templates" / "index.html"
    return Path(__file__).parent.parent / "templates" / "index.html"


@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/")
async def index():
    return HTMLResponse(_get_template_path().read_text(encoding="utf-8"))


@router.post("/convert")
async def convert(
    file: UploadFile = File(...),
    include_headers_footers: bool = Form(default=True),
    output_format: str = Form(default="md"),
    style_map: str | None = Form(default=None),
):
    """Upload a DOCX file and convert it to Markdown."""
    filename = await validate_docx(file)

    job_id = generate_job_id()
    job = job_store.create(job_id)
    job.status = "processing"
    job.filename = Path(filename).stem + ".md"

    upload_dir = settings.upload_dir / job_id
    output_dir = settings.output_dir / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    docx_path = upload_dir / filename
    try:
        content = await file.read()
        docx_path.write_bytes(content)

        custom_style = None
        if style_map:
            try:
                custom_style = json.loads(style_map)
            except json.JSONDecodeError:
                raise HTTPException(400, "Invalid style_map JSON")

        output_path, conv_result = convert_docx(
            docx_path=docx_path,
            output_dir=output_dir,
            output_format=output_format,
            include_headers_footers=include_headers_footers,
            custom_style_map=custom_style,
        )

        job.status = "completed"
        job.image_count = conv_result.image_count
        job.footnote_count = conv_result.footnote_count
        job.toc_detected = conv_result.toc_detected
        job.warnings = conv_result.warnings
        job.output_path = output_path

        return ConversionResponse(
            job_id=job_id,
            status="completed",
            filename=job.filename,
            image_count=job.image_count,
            footnote_count=job.footnote_count,
            toc_detected=job.toc_detected,
            warnings=job.warnings,
            download_url=f"/download/{job_id}?format={output_format}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Conversion failed for job %s", job_id)
        job.status = "failed"
        job.error = str(e)
        raise HTTPException(500, f"Conversion failed: {e}")


@router.get("/download/{job_id}")
async def download(job_id: str, format: str = "md"):
    """Download a converted file by job ID."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found or expired")
    if job.status == "failed":
        raise HTTPException(410, f"Conversion failed: {job.error}")
    if job.status != "completed":
        raise HTTPException(202, "Conversion still in progress")
    if job.output_path is None or not job.output_path.exists():
        raise HTTPException(410, "Output file no longer available")

    output_path = job.output_path
    if output_path.suffix == ".zip":
        media_type = "application/zip"
        dl_name = "result.zip"
    else:
        media_type = "text/markdown; charset=utf-8"
        dl_name = "output.md"

    return FileResponse(
        path=str(output_path),
        media_type=media_type,
        filename=dl_name,
    )
