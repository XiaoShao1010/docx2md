from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    async with client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_index(client):
    async with client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_convert_basic(client):
    docx_path = FIXTURES / "sample_basic.docx"
    if not docx_path.exists():
        pytest.skip("sample_basic.docx not found")

    async with client:
        with open(docx_path, "rb") as f:
            resp = await client.post(
                "/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "md"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["download_url"]


@pytest.mark.asyncio
async def test_convert_invalid_extension(client):
    async with client:
        resp = await client.post(
            "/convert",
            files={"file": ("test.txt", b"not a docx", "text/plain")},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_convert_invalid_content(client):
    async with client:
        resp = await client.post(
            "/convert",
            files={"file": ("fake.docx", b"not a zip file", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_download_not_found(client):
    async with client:
        resp = await client.get("/download/nonexistent")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_after_convert(client):
    docx_path = FIXTURES / "sample_basic.docx"
    if not docx_path.exists():
        pytest.skip("sample_basic.docx not found")

    async with client:
        with open(docx_path, "rb") as f:
            resp = await client.post(
                "/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
        data = resp.json()
        dl_url = data["download_url"]

        resp2 = await client.get(dl_url)
        assert resp2.status_code == 200
        assert len(resp2.text) > 0
