# 🖱️ Local Remote Control

Control your Windows laptop from your phone — mouse, keyboard, gestures, and hotkeys — all over WiFi.

```
┌─────────────────────────────────────┐
│           Phone (browser)           │
│  ┌─────────────────────────────┐    │
│  │         Touchpad            │    │
│  │   Drag to move · Tap click  │    │
│  │   2 fingers scroll          │    │
│  │   3 fingers: swipe/tap      │    │
│  └─────────────────────────────┘    │
│  [Left] [Right] [Double] [Drag]    │
│  [Scroll Up] [Scroll Down]         │
│  [____type something____] [Send]   │
│  Ctrl+C Ctrl+V Alt+Tab Win+D ...   │
└──────────────┬──────────────────────┘
               │  WebSocket over WiFi
               ▼
┌─────────────────────────────────────┐
│     Laptop (Windows Server)         │
│  ⚡ Direct Win32 API for mouse      │
│  ⌨️ pyautogui for keyboard          │
│  📡 Single port: HTTP + WebSocket   │
└─────────────────────────────────────┘
```

---

## ✨ Features

### 🖱️ Mouse Control
| Feature | How |
|---------|-----|
| **Move cursor** | Drag 1 finger on the touchpad |
| **Left click** | Tap 1 finger |
| **Right click** | Tap the "Right" button |
| **Double click** | Tap the "Double" button |
| **Drag & drop** | Toggle "Drag" button, then move |
| **Scroll** | Drag 2 fingers vertically |

### ⌨️ Keyboard
- **Type text** — type in the input box and tap Send
- **Hotkey chips** — tap Ctrl+C, Ctrl+V, Alt+Tab, Win+D, etc.
- **Custom hotkeys** — any combo you want (just add a chip)

### 🖐️ 3-Finger Gestures (like a laptop trackpad)
| Gesture | Action |
|---------|--------|
| 👆👆👆 **Swipe Right** | Switch to next window (`Alt+Tab`) |
| 👆👆👆 **Swipe Left** | Switch to previous window (`Shift+Alt+Tab`) |
| 👆👆👆 **Swipe Up** | Task View (`Win+Tab`) |
| 👆👆👆 **Swipe Down** | Show Desktop (`Win+D`) |
| 👆👆👆 **Tap** | Windows Search (`Win+S`) |

### 📡 Network
- **Single port** — HTTP (web UI) + WebSocket live on port **8765**
- **QR code** auto-generated on startup — scan and go
- **VPN-aware** — detects and avoids VPN IPs (Cloudflare WARP, etc.)
- **Auto-connects** — page detects the server on the same port it was loaded from

---

## 🚀 Quick Start

### Requirements
- **Python 3.8+** on Windows
- Your phone and laptop on the **same WiFi network**

### 1. Install

```bash
cd server
pip install -r requirements.txt
```

### 2. Run

```bash
cd server
python main.py
```

### 3. Connect

You'll see:
```
========================================================
           *** Remote Control Server ***
========================================================

  Open on your phone browser:
      http://192.168.1.42:8765

  QR code saved as: remote_control_qr.png
```

**Option A:** Scan the QR code that pops up  
**Option B:** Type `http://YOUR-IP:8765` in your phone browser  
**Option C:** Bookmark it for next time (no scanning needed)

---

## 🏗️ Architecture

```
server/
├── main.py          ← Python server (aiohttp)
│                      Serves remote.html via HTTP
│                      Handles commands via WebSocket
│                      Uses Win32 API (mouse) + pyautogui (keyboard)
│
├── remote.html      ← Mobile web UI
│                      Touchpad, buttons, keyboard, gestures
│                      All logic in a single file for simplicity
│
├── requirements.txt ← Python dependencies
│
.gitignore           ← Prevents 'nul' file issues on Windows
```

### Server (`main.py`)
Built with **aiohttp** — both HTTP and WebSocket on one port. No firewall headaches.

- **Mouse:** Direct Windows API via `ctypes` (`user32.SetCursorPos`, `mouse_event`) — ~10x faster than pyautogui
- **Keyboard:** `pyautogui` (fast enough for key events, handles complex hotkeys well)
- **Network:** Smart IP detection that skips VPN adapters (172.16.x.x, 10.8.x.x)

### Web UI (`remote.html`)
A single-file mobile web app. No frameworks, no build step.

- **Event-driven movement** — sends cursor data immediately when touch changes (throttled to ~8ms)
- **Sensitivity locked at 4.0×** — always fast, no slider to fiddle with
- **Touch gesture detection** — tracks finger count in real-time for 1-finger move, 2-finger scroll, 3-finger swipe/tap

---

## 📜 Changelog

| Version | Changes |
|---------|---------|
| **v5** | Fixed 3-finger gestures: Alt+Tab (window switching), prevented unwanted click after gesture, added 3-finger tap (Win+S) |
| **v4** | Event-driven movement (lower latency), fixed sensitivity to 4.0×, added 3-finger swipe gestures, removed slider |
| **v3** | Windows API direct mouse (10x faster), throttling, sensitivity slider, VPN detection fix |
| **v2** | Migrated to aiohttp — single port for HTTP + WebSocket, no firewall issues |
| **v1** | Initial version — WebSocket server + web UI on separate ports |

---

## 🔮 Roadmap

- [ ] **mDNS Auto-Discovery** — laptop advertises itself on the network, phone finds it automatically
- [ ] **Windows System Tray App** — single `.exe` that sits in the tray, auto-starts with Windows
- [ ] **Media Controls** — Play/Pause, Next/Prev Track, Volume Up/Down, Mute
- [ ] **Native Mobile App** — Flutter/React Native app, auto-connects, no browser needed
- [ ] **Multiple Computer Support** — picker UI when multiple laptops are detected

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Server framework | `aiohttp` (Python async HTTP + WebSocket) |
| Mouse control | Windows `user32.dll` via `ctypes` |
| Keyboard control | `pyautogui` |
| Web UI | Vanilla HTML/CSS/JS — single file, no deps |
| QR code | `qrcode[pil]` |
| Gesture detection | Custom JS touch event tracking |

---

## 🤝 Contributing

This is a personal project by [Kismat Adhikari](https://github.com/Kismat-Adhikari06). Feel free to fork, open issues, or send PRs!

---

<p align="center">
  <sub>Built with ❤️ using Python + JavaScript</sub>
</p>
