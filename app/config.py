from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "DOCX2MD_"}

    max_file_size_mb: int = 50
    allowed_extensions: set[str] = {".docx"}
    image_folder_name: str = "images"
    temp_file_ttl_minutes: int = 30
    upload_dir: Path = Path("uploads")
    output_dir: Path = Path("outputs")
    image_format: str = "original"
    image_quality: int = 85
    log_level: str = "info"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
