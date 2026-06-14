# Unicode Picker

A GTK3 special character picker with system tray icon. Click a character to copy it straight to the clipboard — no more memorizing alt-codes for ©, €, –, → and friends.

![Status: Linux-only](https://img.shields.io/badge/platform-Linux-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Features

- **One-click copy** — click any character to copy it to the clipboard, with a brief desktop notification
- **Categories** — Currency, Copyright & Legal, Typography, Math, Arrows, Look-alikes (visually similar characters such as ∕ ⁄ ❓ ‽), and Whitespace/Invisible characters
- **Recently used** — quick access to your last copied characters, also shown in the tray menu
- **Search** — filter by character or name across all categories
- **System tray** — stays available via AppIndicator, with recent characters one click away
- **Multi-language** — English and German, switchable in the app with system language auto-detection

## Requirements

System packages (Debian/Ubuntu/Mint):

```
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 libnotify-bin
```

If `gir1.2-ayatanaappindicator3-0.1` is unavailable, the classic `gir1.2-appindicator3-0.1` is used as a fallback. Without either, the app runs as a normal window (use `--no-tray` to force this).

## Installation

```
git clone https://github.com/NoCoderGHG/unicode-picker.git
cd unicode-picker
python3 unicode_picker.py
```

No pip dependencies. No virtual environment needed.

## Configuration

Language preference and recently used characters are stored in `~/.config/unicode-picker/config.json`.

## License

MIT — see [LICENSE](LICENSE).
