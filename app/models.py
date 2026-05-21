from pydantic import BaseModel


class ConversionResponse(BaseModel):
    job_id: str
    status: str
    filename: str | None = None
    image_count: int = 0
    footnote_count: int = 0
    toc_detected: bool = False
    warnings: list[str] = []
    download_url: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
