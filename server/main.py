#!/usr/bin/env python3
"""
Remote Control Server — Desktop (aiohttp)
Serves the web UI AND WebSocket on a SINGLE port (8765).
"""

import json
import os
import socket
import sys

import pyautogui
from aiohttp import web

# ─── Safety & Speed ───
pyautogui.FAILSAFE = True
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
                dx, dy = data.get("dx", 0), data.get("dy", 0)
                x, y = pyautogui.position()
                pyautogui.moveTo(x + dx, y + dy)

            elif t == "mouse_to":
                pyautogui.moveTo(data["x"], data["y"])

            elif t == "mouse_click":
                pyautogui.click(button=data.get("button", "left"))

            elif t == "mouse_double_click":
                pyautogui.doubleClick(button=data.get("button", "left"))

            elif t == "mouse_right_click":
                pyautogui.rightClick()

            elif t == "mouse_down":
                pyautogui.mouseDown(button=data.get("button", "left"))

            elif t == "mouse_up":
                pyautogui.mouseUp(button=data.get("button", "left"))

            elif t == "mouse_scroll":
                pyautogui.scroll(data.get("clicks", 0))

            elif t == "mouse_drag":
                dx, dy = data.get("dx", 0), data.get("dy", 0)
                x, y = pyautogui.position()
                pyautogui.drag(x + dx, y + dy, duration=0, button=data.get("button", "left"))

            # ── Keyboard ──────────────────────────────────────────
            elif t == "key_press":
                pyautogui.press(data.get("key", ""))

            elif t == "key_type":
                pyautogui.write(data.get("text", ""), interval=0.01)

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
                w, h = pyautogui.size()
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
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


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
