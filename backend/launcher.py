"""PyInstaller entry point — runs the FastAPI server inside a frozen exe."""
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

# When frozen by PyInstaller, the bundle lives in sys._MEIPASS.
# We need the backend working directory to be next to the .exe so
# the SQLite DB and any data folders are persisted between runs.
if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    os.chdir(exe_dir)
    # Tell the app where to find the bundled frontend dist
    os.environ.setdefault("FRONTEND_DIST", str(exe_dir / "frontend_dist"))

import uvicorn


def open_browser():
    time.sleep(3)
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 60)
    print(" HMC Payroll Management System v2.0")
    print(" Server starting on http://localhost:8000")
    print(" Login: admin / Admin@1234")
    print(" Close this window to stop the server.")
    print("=" * 60)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
