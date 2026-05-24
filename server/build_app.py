"""
Build the Remote Control Windows App using PyInstaller.
Run:  python build_app.py

This creates RemoteControl.exe in the dist/ folder — a single-file
executable with no external dependencies needed on the target machine.
"""

import os
import sys
import shutil
import subprocess

# Make sure PyInstaller is installed
try:
    import PyInstaller
except ImportError:
    print("PyInstaller not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    import PyInstaller


def build():
    """Build RemoteControl.exe using PyInstaller."""
    # Clean previous builds
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

    # Paths
    server_dir = os.path.dirname(os.path.abspath(__file__))
    tray_app = os.path.join(server_dir, "tray_app.py")
    html_file = os.path.join(server_dir, "remote.html")

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                # Single .exe
        "--noconsole",              # No terminal window
        "--name", "RemoteControl",
        # Include the web UI file
        "--add-data", f"{html_file};.",
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "aiohttp",
        "--hidden-import", "aiohttp.web_runner",
        "--hidden-import", "aiohttp.http_parser",
        "--hidden-import", "aiohttp.http_websocket",
        "--hidden-import", "multidict",
        "--hidden-import", "yarl",
        "--hidden-import", "async_timeout",
        "--hidden-import", "frozenlist",
        "--hidden-import", "aiosignal",
        "--hidden-import", "zeroconf",
        "--hidden-import", "pyautogui",
        "--hidden-import", "pyscreeze",
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "qrcode",
        "--collect-all", "aiohttp",
        tray_app,
    ]

    print("=" * 60)
    print("  Building Remote Control App...")
    print("=" * 60)
    print()
    print(f"  Source: {tray_app}")
    print(f"  Output: RemoteControl.exe")
    print()

    # Run PyInstaller (using subprocess for path safety)
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.join(server_dir, "dist", "RemoteControl.exe")
        print()
        print("=" * 60)
        print("  Build successful!")
        print(f"  Your app is at: {exe_path}")
        print(f"  Size: {os.path.getsize(exe_path) / 1024 / 1024:.0f} MB")
        print()
        print("  Double-click RemoteControl.exe to run.")
        print("  Right-click the tray icon to show QR or quit.")
        print("=" * 60)
    else:
        print()
        print(f"Build failed with exit code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()


if __name__ == "__main__":
    build()
