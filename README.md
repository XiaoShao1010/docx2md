# DOCX2MD — DOCX to Markdown Web Converter

A web service that converts Microsoft Word `.docx` files to Markdown format. Built with FastAPI and Docker.

## Features

- **Paragraphs & Headings** — H1-H6 heading levels
- **Inline Formatting** — Bold, italic, underline, strikethrough, superscript, subscript, code
- **Lists** — Ordered and unordered, including nested lists
- **Tables** — GFM (GitHub-Flavored Markdown) tables with alignment
- **Images** — Automatic extraction with markdown references
- **Hyperlinks** — `<a>` tag conversion to `[text](url)`
- **Headers & Footers** — Extracted from DOCX and placed in blockquotes
- **Footnotes & Endnotes** — Inline references and definition assembly
- **TOC Detection** — Detects Table of Contents entries
- **Style Mapping** — Maps Word styles to Markdown equivalents (customizable)
- **ZIP Packaging** — Optionally download `.md` + images as a zip file

## Quick Start

### Docker

```bash
docker-compose up --build
```

Then open http://localhost:8000 in your browser.

### Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the upload UI, or http://localhost:8000/docs for the Swagger API docs.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Web upload interface |
| `POST` | `/convert` | Upload and convert a `.docx` file |
| `GET` | `/download/{job_id}` | Download converted result |
| `GET` | `/health` | Health check |

### POST /convert

**Form fields:**
- `file` (required): `.docx` file (max 50MB)
- `output_format` (optional): `"md"` (default) or `"zip"`
- `include_headers_footers` (optional): `true` (default) or `false`
- `style_map` (optional): JSON string with custom style mappings

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "filename": "output.md",
  "image_count": 5,
  "footnote_count": 3,
  "toc_detected": true,
  "warnings": [],
  "download_url": "/download/abc123?format=md"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCX2MD_UPLOAD_DIR` | `uploads` | Uploaded files directory |
| `DOCX2MD_OUTPUT_DIR` | `outputs` | Converted output directory |
| `DOCX2MD_MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |
| `DOCX2MD_LOG_LEVEL` | `info` | Logging level |
| `DOCX2MD_TEMP_FILE_TTL_MINUTES` | `30` | How long to keep converted files |

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Project Structure

```
docx2md/
├── app/
│   ├── api/            # FastAPI routes and dependencies
│   ├── converter/      # DOCX to Markdown conversion engine
│   ├── templates/      # Jinja2 web UI template
│   └── utils/          # File utilities and sanitization
├── tests/
│   ├── fixtures/       # Sample .docx test files
│   ├── test_converter/ # Converter unit tests
│   └── test_api/       # API integration tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
