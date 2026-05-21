"""Standalone entry point for PyInstaller-packaged executable.

Starts the uvicorn server and opens the browser automatically.
"""

import multiprocessing
import threading
import time
import webbrowser

import uvicorn
from app.main import app


def open_browser(url: str, delay: float = 1.5):
    time.sleep(delay)
    webbrowser.open(url)


def main():
    multiprocessing.freeze_support()

    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}"

    print(f"  DOCX2MD v1.0.0")
    print(f"  Starting server at {url}")
    print(f"  Press Ctrl+C to stop")
    print()

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
