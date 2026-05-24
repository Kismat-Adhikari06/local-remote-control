"""
Remote Control — System Tray Application
Runs the server in the background with a system tray icon.
No terminal needed — just double-click and go.
"""

"""
Remote Control — System Tray Application
Runs the server in the background with a system tray icon.
No terminal needed — just double-click and go.
"""

import asyncio
import base64
import os
import subprocess
import sys
import threading

import pystray
from PIL import Image, ImageDraw

from aiohttp import web

from main import (
    PORT,
    create_app,
    get_local_ip,
    setup_mdns,
    cleanup_mdns,
    show_qr,
    qr_path,
)


class RemoteControlApp:
    """Manages the server lifecycle and system tray icon."""

    def __init__(self):
        self.ip = get_local_ip()
        self.port = 8765
        self.zc = None
        self.mdns_info = None
        self.mdns_url = f"http://remote-control.local:{self.port}"
        self.runner = None
        self.loop = None
        self._icon = None

    # ── Icon Generation ──────────────────────────────────────────

    @staticmethod
    def create_icon_image() -> Image.Image:
        """Generate a 64x64 tray icon (mouse cursor silhouette)."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        draw.ellipse([2, 2, 62, 62], fill=(240, 194, 127, 200))

        # Mouse pointer shape
        draw.polygon([(20, 12), (44, 36), (36, 38), (44, 52), (38, 54),
                       (30, 40), (22, 46), (20, 12)],
                      fill=(17, 17, 17, 220))

        return img

    # ── Server Lifecycle ─────────────────────────────────────────

    def start_server(self, loop):
        """Start the aiohttp server on the given event loop."""
        asyncio.set_event_loop(loop)
        self.loop = loop

        app = create_app()

        async def _start():
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", self.port)
            await site.start()
            self.runner = runner

        loop.run_until_complete(_start())
        loop.run_forever()

    def stop_server(self):
        """Shut down the server and mDNS."""
        if self.loop and self.runner:
            async def _stop():
                await self.runner.cleanup()
            asyncio.run_coroutine_threadsafe(_stop(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)

        cleanup_mdns(self.zc, self.mdns_info)

    # ── Auto-Start ──────────────────────────────────────────────

    @staticmethod
    def _startup_shortcut_path() -> str:
        """Path to the startup folder shortcut."""
        startup = os.path.join(
            os.path.expanduser("~"),
            "AppData", "Roaming", "Microsoft", "Windows", "Start Menu",
            "Programs", "Startup",
        )
        return os.path.join(startup, "Remote Control.lnk")

    @staticmethod
    def is_auto_start_enabled() -> bool:
        """Check if the app is in the Windows startup folder."""
        return os.path.exists(RemoteControlApp._startup_shortcut_path())

    @staticmethod
    def toggle_auto_start() -> bool:
        """Toggle whether the app starts with Windows. Returns new state."""
        shortcut_path = RemoteControlApp._startup_shortcut_path()
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            return False
        else:
            exe_path = (
                sys.argv[0] if getattr(sys, 'frozen', False)
                else sys.executable
            )
            work_dir = os.path.dirname(os.path.abspath(exe_path))

            # Build a PowerShell script to create the shortcut
            # PowerShell script to create a .lnk shortcut.
            # Using -EncodedCommand so path quoting is safe.
            ps_script = (
                "$ws = New-Object -ComObject WScript.Shell; "
                f"$s = $ws.CreateShortcut('{shortcut_path}'); "
                f"$s.TargetPath = '{exe_path}'; "
                f"$s.WorkingDirectory = '{work_dir}'; "
                "$s.Description = 'Remote Control - control your PC from your phone'; "
                "$s.Save()"
            )
            encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
            subprocess.run(
                ["powershell", "-NoProfile", "-EncodedCommand", encoded],
                capture_output=True,
            )
            return True

    # ── UI Actions ───────────────────────────────────────────────

    def show_qr_image(self):
        """Open the QR code image in the default image viewer."""
        path = qr_path()
        if os.path.exists(path):
            os.startfile(path)

    def open_browser(self):
        """Open the server URL in the default browser."""
        import webbrowser
        webbrowser.open(f"http://{self.ip}:{self.port}")

    def toggle_auto_start_action(self):
        """Toggle auto-start and update the tray menu (no restart needed)."""
        self.toggle_auto_start()
        # Swap the menu at runtime — pystray supports this without stop/restart
        self._icon.menu = self._build_menu()

    def quit_app(self):
        """Clean shutdown and exit."""
        self.stop_server()
        if self._icon:
            self._icon.stop()
        sys.exit(0)

    # ── Menu ─────────────────────────────────────────────────────

    def _build_menu(self):
        """Build the tray menu (so it can be swapped at runtime)."""
        auto_start_label = (
            "Disable auto-start" if self.is_auto_start_enabled()
            else "Start with Windows"
        )
        return pystray.Menu(
            pystray.MenuItem("Show QR Code", self.show_qr_image, default=True),
            pystray.MenuItem(f"Open http://{self.ip}:{self.port}", self.open_browser),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"IP: {self.ip}  |  mDNS: remote-control.local",
                None,
                enabled=False,
            ),
            pystray.MenuItem(auto_start_label, self.toggle_auto_start_action),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app),
        )

    # ─── Main ────────────────────────────────────────────────────

    def run(self):
        """Initialize everything and show the tray icon."""
        # mDNS
        self.zc, self.mdns_info, self.mdns_url = setup_mdns(self.ip, self.port)

        # Generate and open QR code
        show_qr(f"http://{self.ip}:{self.port}")

        # Start server in a background thread
        server_loop = asyncio.new_event_loop()
        t = threading.Thread(target=self.start_server, args=(server_loop,), daemon=True)
        t.start()

        # Show the tray icon (blocking call)
        icon_img = self.create_icon_image()
        self._icon = pystray.Icon(
            "remote-control",
            icon_img,
            "Remote Control",
            self._build_menu(),
        )
        self._icon.run()


if __name__ == "__main__":
    app = RemoteControlApp()
    app.run()
