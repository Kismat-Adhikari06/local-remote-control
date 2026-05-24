#!/usr/bin/env python3
"""
Remote Control Server — Desktop (aiohttp)
Serves the web UI AND WebSocket on a SINGLE port (8765).
Uses direct Windows API calls for lightning-fast mouse control.
"""

import json
import os
import socket
import sys
import time
import ctypes
from ctypes import wintypes

from aiohttp import web

# ─── Windows API Setup ─────────────────────────────────────────────
user32 = ctypes.windll.user32

# Mouse event flags
MOUSEEVENTF_MOVE       = 0x0001
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040
MOUSEEVENTF_WHEEL      = 0x0800
MOUSEEVENTF_ABSOLUTE   = 0x8000


def move_mouse(x: int, y: int) -> None:
    """Move cursor to absolute screen position."""
    user32.SetCursorPos(x, y)


def get_mouse_pos() -> tuple:
    """Get current cursor position."""
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def mouse_down(button: str = "left") -> None:
    if button == "left":
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    elif button == "right":
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)


def mouse_up(button: str = "left") -> None:
    if button == "left":
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == "right":
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


def click_mouse(button: str = "left") -> None:
    mouse_down(button)
    mouse_up(button)


def double_click(button: str = "left") -> None:
    click_mouse(button)
    click_mouse(button)


def scroll_wheel(clicks: int) -> None:
    """Scroll the mouse wheel. Positive = up, negative = down."""
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(clicks * 120), 0)


def get_screen_size() -> tuple:
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


# ─── Keyboard (still uses pyautogui — it's fast enough for key events) ───
import pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


# ─── WebSocket Command Handler ───
async def handle_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type != web.WSMsgType.TEXT:
            continue

        try:
            data = json.loads(msg.data)
            t = data.get("type", "")

            # ── Mouse ─────────────────────────────────────────────
            if t == "mouse_move":
                # Use relative MOUSEEVENTF_MOVE — single API call, no GetCursorPos needed
                dx, dy = data.get("dx", 0), data.get("dy", 0)
                user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)

            elif t == "mouse_to":
                move_mouse(data["x"], data["y"])

            elif t == "mouse_click":
                click_mouse(data.get("button", "left"))

            elif t == "mouse_double_click":
                double_click(data.get("button", "left"))

            elif t == "mouse_right_click":
                click_mouse("right")

            elif t == "mouse_down":
                mouse_down(data.get("button", "left"))

            elif t == "mouse_up":
                mouse_up(data.get("button", "left"))

            elif t == "mouse_scroll":
                scroll_wheel(data.get("clicks", 0))

            elif t == "mouse_drag":
                dx, dy = data.get("dx", 0), data.get("dy", 0)
                button = data.get("button", "left")
                mouse_down(button)
                # Use relative movement for smooth drag
                steps = max(abs(dx), abs(dy)) // 10 + 1
                for i in range(1, steps + 1):
                    user32.mouse_event(MOUSEEVENTF_MOVE, dx // steps, dy // steps, 0, 0)
                    time.sleep(0.001)
                mouse_up(button)

            # ── Keyboard ──────────────────────────────────────────
            elif t == "key_press":
                pyautogui.press(data.get("key", ""))

            elif t == "key_type":
                pyautogui.write(data.get("text", ""), interval=0.005)

            elif t == "hotkey":
                pyautogui.hotkey(*data.get("keys", []))

            elif t == "key_down":
                pyautogui.keyDown(data.get("key", ""))

            elif t == "key_up":
                pyautogui.keyUp(data.get("key", ""))

            # ── System / Info ─────────────────────────────────────
            elif t == "ping":
                await ws.send_json({"type": "pong"})

            elif t == "get_screen_size":
                w, h = get_screen_size()
                await ws.send_json({"type": "screen_size", "width": w, "height": h})

            else:
                await ws.send_json({"type": "error", "message": f"Unknown command: {t}"})

        except Exception as e:
            try:
                await ws.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass

    return ws


# ─── HTTP: Serve the web UI ───
async def serve_html(request):
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remote.html")
    return web.FileResponse(html_path)


# ─── Network ───
def get_local_ip() -> str:
    """Find the real local IP, excluding VPN adapters."""
    # Try to find a non-VPN, non-loopback IPv4 address
    try:
        # Preferred: connect to a public DNS to find the active interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        # Check if it's a known VPN range
        if ip.startswith("172.16.") or ip.startswith("10.8.") or ip.startswith("100."):
            # Likely a VPN — fall back to enumerating interfaces
            return get_real_local_ip()
        return ip
    except OSError:
        return get_real_local_ip()


def get_real_local_ip() -> str:
    """Fallback: enumerate all interfaces and pick the best non-VPN match."""
    try:
        hostname = socket.gethostname()
        for addr in socket.gethostbyname_ex(hostname)[2]:
            if addr.startswith("192.") or addr.startswith("10."):
                if not addr.startswith("10.8."):
                    return addr
        # Last resort: anything that's not loopback or VPN
        for addr in socket.gethostbyname_ex(hostname)[2]:
            if addr != "127.0.0.1" and not addr.startswith("172.16."):
                return addr
        return "127.0.0.1"
    except Exception:
        return "127.0.0.1"


def show_qr(data: str) -> None:
    import qrcode

    qr = qrcode.QRCode(border=2, box_size=10)
    qr.add_data(data)
    img = qr.make_image(fill_color="black", back_color="white")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remote_control_qr.png")
    img.save(path)
    print(f"  QR code saved as: {path}")
    try:
        os.startfile(path)
    except Exception:
        pass


# ─── Main ───
def main():
    port = 8765
    ip = get_local_ip()

    app = web.Application()
    app.router.add_get("/", serve_html)
    app.router.add_get("/remote.html", serve_html)
    app.router.add_get("/ws", handle_ws)

    print()
    print("=" * 56)
    print("       *** Remote Control Server ***")
    print("=" * 56)
    print()
    print(f"  Open on your phone browser:")
    print(f"      http://{ip}:{port}")
    print()
    print(f"  (Single port — works through firewalls)")
    print()

    show_qr(f"http://{ip}:{port}")

    print()
    print(f"  [1] Open http://{ip}:{port} on your phone")
    print(f"  [2] The page auto-connects")
    print(f"  [3] Press Ctrl+C to stop")
    print("=" * 56)
    print()

    try:
        web.run_app(app, host="0.0.0.0", port=port, print=lambda *a: None)
    except KeyboardInterrupt:
        print("\n  Server stopped.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
