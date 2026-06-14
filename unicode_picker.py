#!/usr/bin/env python3
"""
Unicode Picker - GTK3 special character picker with tray icon
Click a character to copy it to the clipboard.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio

import json
import locale
import os
import subprocess
import unicodedata
from pathlib import Path

HAS_INDICATOR = False
AppIndicator3 = None
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
    HAS_INDICATOR = True
except (ValueError, ImportError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3
        HAS_INDICATOR = True
    except (ValueError, ImportError):
        HAS_INDICATOR = False

CONFIG_DIR  = Path.home() / ".config" / "unicode-picker"
CONFIG_FILE = CONFIG_DIR / "config.json"
ICON_DIR    = CONFIG_DIR / "icons"
I18N_DIR    = Path(__file__).parent / "i18n"

DEFAULT_CONFIG = {"lang": "system", "recent": [], "max_recent": 24}


# ── Config & i18n ─────────────────────────────────────────────────────────────

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def detect_system_lang():
    try:
        loc = locale.getlocale()[0] or ""
    except Exception:
        loc = ""
    if not loc:
        loc = os.environ.get("LANG", "")
    return "de" if loc.lower().startswith("de") else "en"


def resolve_lang(setting):
    if setting == "system":
        return detect_system_lang()
    return setting


def load_i18n(lang):
    en = {}
    en_path = I18N_DIR / "en.json"
    if en_path.exists():
        with open(en_path) as f:
            en = json.load(f)
    if lang == "en":
        return en
    path = I18N_DIR / f"{lang}.json"
    if not path.exists():
        return en
    with open(path) as f:
        strings = json.load(f)
    for k, v in en.items():
        strings.setdefault(k, v)
    return strings


def t(strings, key, **kwargs):
    s = strings.get(key, key)
    for k, v in kwargs.items():
        s = s.replace("{" + k + "}", str(v))
    return s


# ── Character data ────────────────────────────────────────────────────────────
# Each category is a plain string of characters. Display names are derived
# from the Unicode standard name via unicodedata (always available, no
# per-character translation needed).

CATEGORIES = {
    "currency": "€£¥¢₹₽₿ƒ₩₪₫₴₦₲₵₸₺₼₡₧₨₭₮₯₰₱₳₶₷",

    "legal": "©®™℗№§¶†‡",

    "typography": (
        "„\u201c‚'«»‹›–—―…•·‧‰‱°′″‴¦‖¬"
        "¡¿‽№"
    ),

    "math": (
        "±×÷=≈≠≡<>≤≥√∞π∑∏∂∫∮∝"
        "∀∃∄∈∉∋⊂⊃⊆⊇∪∩∧∨¬⊕⊗⊥∥∠"
        "½¼¾⅓⅔⅕⅖⅗⅛⅜⅝⅞"
        "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"
        "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎"
    ),

    "arrows": (
        "→←↑↓↔↕⇒⇐⇔⇕↵⏎"
        "↩↪↫↬↰↱↲↳⇄⇆⇇⇉⇋⇌"
        "↻↺⟲⟳"
        "⇧⇩⇦⇨⇪"
        "➔➜➝➞➟➠➤➥➦➧➨"
        "↖↗↘↙⤴⤵⤶⤷"
    ),

    "lookalikes": (
        "∕⁄⧸⫻❘❙❚＼﹨"
        "❓❔﹖‽⁇⁈⁉"
        "∶ː˸"
        "‒–—―‐‑⁃"
        "ǃʔˀ"
        "ⅼⅠ𝙸"
    ),

    "whitespace": "\u00a0\u202f\u2009\u2002\u2003\u200b\u200c\u200d\u2060\ufeff",

    "greek": (
        "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
        "αβγδεζηθικλμνξοπρςστυφχψω"
        "ϑϕϖϰϱϵ"
    ),

    "latin_extended": (
        "ÀÁÂÃÄÅĀĂĄÆÇĆČĐÈÉÊËĒĖĘĚ"
        "ÌÍÎÏĪĮÑŃŇÒÓÔÕÖŌØŒ"
        "ŠŚŞŤÙÚÛÜŪŮŰŴÝŸŹŽ"
        "àáâãäåāăąæçćčđèéêëēėęě"
        "ìíîïīįñńňòóôõöōøœ"
        "ßšśşťùúûüūůűŵýÿźž"
        "ðþĐÞ"
    ),

    "symbols": (
        "★☆✦✧✩✪✫✬✭✮✯"
        "♠♣♥♦♤♧♡♢"
        "♔♕♖♗♘♙♚♛♜♝♞♟"
        "☀☁☂☃☄☽☾⛅⛆"
        "☎☏✉✏✒✂"
        "☑☒☐✓✔✗✘✚✱✲✳✴"
        "❄❅❆❤❥❦❧"
        "☮☯☢☣⚠⚡♻♲"
        "♀♂⚧"
        "♪♫♬♩"
        "✈⚓⚑⚐"
    ),

    "box_drawing": (
        "─│┌┐└┘├┤┬┴┼"
        "═║╔╗╚╝╠╣╦╩╬"
        "╭╮╯╰"
        "░▒▓█▀▄▌▐"
        "■□▢▣▤▥▦▧▨▩"
        "▲▼◀▶◆◇○●◯"
    ),
}

CATEGORY_ORDER = ["currency", "legal", "typography", "math", "arrows",
                  "lookalikes", "whitespace", "greek", "latin_extended",
                  "symbols", "box_drawing"]

CATEGORY_LABEL_KEYS = {
    "currency":       "tab_currency",
    "legal":          "tab_legal",
    "typography":     "tab_typography",
    "math":           "tab_math",
    "arrows":         "tab_arrows",
    "lookalikes":     "tab_lookalikes",
    "whitespace":     "tab_whitespace",
    "greek":          "tab_greek",
    "latin_extended": "tab_latin_extended",
    "symbols":        "tab_symbols",
    "box_drawing":    "tab_box_drawing",
}


def char_name(char):
    """Returns a human-readable name for a character via unicodedata,
    falling back to its codepoint if unavailable."""
    try:
        return unicodedata.name(char).title()
    except (ValueError, TypeError):
        return f"U+{ord(char):04X}"





# ── Helpers ───────────────────────────────────────────────────────────────────

def send_notification(title, body):
    try:
        subprocess.run(["notify-send", "-u", "low", "-t", "1500", title, body], check=False)
    except FileNotFoundError:
        pass


def ensure_tray_icon():
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    path = ICON_DIR / "unicode-picker.svg"
    if path.exists():
        return str(path)
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <rect x="2" y="2" width="44" height="44" rx="8" fill="#3a3a3a"/>
  <text x="24" y="33" text-anchor="middle" font-family="Sans" font-weight="bold"
        font-size="24" fill="#ffffff">Ω</text>
</svg>
"""
    path.write_text(svg)
    return str(path)


def char_display_label(char):
    """Returns a visible representation for whitespace/invisible characters."""
    invisible = {
        "\u00a0": "␣", "\u200b": "⌴", "\u200d": "⁝",
        "\u200c": "⁞", "\u2009": "␣", "\u2003": "␣",
    }
    return invisible.get(char, char)


# ── Character button widget ───────────────────────────────────────────────────

class CharButton(Gtk.Button):
    def __init__(self, char, name, on_pick):
        super().__init__(label=char_display_label(char))
        self.char = char
        self.set_tooltip_text(f"{name}\nU+{ord(char):04X}")
        self.get_style_context().add_class("char-button")
        label = self.get_child()
        if isinstance(label, Gtk.Label):
            label.set_attributes(None)
            label.set_markup(f'<span size="20000">{GLib.markup_escape_text(char_display_label(char))}</span>')
        self.connect("clicked", lambda _b: on_pick(char, name))


# ── Main window ───────────────────────────────────────────────────────────────

class UnicodePickerWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_default_size(560, 420)

        self.cfg = load_config()
        self.strings = load_i18n(resolve_lang(self.cfg.get("lang", "system")))
        s = self.strings

        self.set_title(t(s, "app_title"))

        # HeaderBar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = t(s, "app_title")
        self.set_titlebar(header)

        self._lang_options = [("de", "lang_de"), ("en", "lang_en"),
                               ("system", "lang_system")]
        self.lang_menu_btn = Gtk.MenuButton()
        self.lang_menu_btn.set_size_request(130, -1)
        self._lang_label = Gtk.Label()
        self.lang_menu_btn.add(self._lang_label)
        lang_menu = Gtk.Menu()
        group = []
        current_lang = self.cfg.get("lang", "system")
        for code, key in self._lang_options:
            item = Gtk.RadioMenuItem.new_with_label(group, t(s, key))
            group = item.get_group()
            if code == current_lang:
                item.set_active(True)
                self._lang_label.set_text(t(s, key))
            item.connect("activate", self._on_lang_menu_item, code)
            lang_menu.append(item)
        lang_menu.show_all()
        self.lang_menu_btn.set_popup(lang_menu)
        header.pack_end(self.lang_menu_btn)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        vbox.set_margin_start(8)
        vbox.set_margin_end(8)
        self.add(vbox)

        # Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(t(s, "search_placeholder"))
        self.search_entry.connect("search-changed", self._on_search_changed)
        vbox.pack_start(self.search_entry, False, False, 0)

        # Notebook
        self.notebook = Gtk.Notebook()
        vbox.pack_start(self.notebook, True, True, 0)

        self._flowboxes = {}

        # Recent tab
        self.recent_flow = self._make_flowbox()
        self._build_recent_tab()
        scroll = self._wrap_scroll(self.recent_flow)
        self.notebook.append_page(scroll, Gtk.Label(label=t(s, "tab_recent")))
        self._flowboxes["recent"] = self.recent_flow

        # Category tabs
        for cat in CATEGORY_ORDER:
            flow = self._make_flowbox()
            for char in CATEGORIES[cat]:
                btn = CharButton(char, char_name(char), self._on_pick)
                flow.add(btn)
            scroll = self._wrap_scroll(flow)
            self.notebook.append_page(scroll, Gtk.Label(label=t(s, CATEGORY_LABEL_KEYS[cat])))
            self._flowboxes[cat] = flow

        # Statusbar
        self.statusbar = Gtk.Statusbar()
        self.ctx = self.statusbar.get_context_id("main")
        vbox.pack_start(self.statusbar, False, False, 0)

        self.connect("delete-event", self._on_delete_event)

    def _make_flowbox(self):
        flow = Gtk.FlowBox()
        flow.set_valign(Gtk.Align.START)
        flow.set_max_children_per_line(16)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_row_spacing(4)
        flow.set_column_spacing(4)
        flow.set_homogeneous(True)
        return flow

    def _wrap_scroll(self, widget):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(widget)
        return scroll

    def _build_recent_tab(self):
        s = self.strings
        for child in self.recent_flow.get_children():
            self.recent_flow.remove(child)
        recent = self.cfg.get("recent", [])
        if not recent:
            label = Gtk.Label(label=t(s, "no_recent"))
            label.get_style_context().add_class("dim-label")
            label.set_margin_top(12)
            self.recent_flow.add(label)
        else:
            for entry in recent:
                char = entry.get("char")
                name = entry.get("name", "")
                btn = CharButton(char, name, self._on_pick)
                self.recent_flow.add(btn)
        self.recent_flow.show_all()

    def _on_pick(self, char, name):
        s = self.strings
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(char, -1)
        clipboard.store()

        self._add_to_recent(char, name)
        self._set_status(t(s, "status_copied", char=char_display_label(char)))
        send_notification(t(s, "notify_title"),
                          t(s, "notify_copied", char=char_display_label(char)))

    def _add_to_recent(self, char, name):
        recent = [e for e in self.cfg.get("recent", []) if e.get("char") != char]
        recent.insert(0, {"char": char, "name": name})
        max_recent = self.cfg.get("max_recent", 24)
        self.cfg["recent"] = recent[:max_recent]
        save_config(self.cfg)
        self._build_recent_tab()

    def _set_status(self, text):
        self.statusbar.pop(self.ctx)
        self.statusbar.push(self.ctx, text)

    def _on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        s = self.strings

        if not query:
            for cat, flow in self._flowboxes.items():
                flow.set_filter_func(None)
            return

        for cat, flow in self._flowboxes.items():
            if cat == "recent":
                continue

            def filter_func(child, q=query):
                widget = child.get_child()
                if not isinstance(widget, CharButton):
                    return False
                tooltip = (widget.get_tooltip_text() or "").lower()
                return q in tooltip or q in widget.char.lower()

            flow.set_filter_func(filter_func)

    def _on_delete_event(self, *_):
        self.hide()
        return True

    def _on_lang_menu_item(self, item, code):
        if not item.get_active(): return
        if code == self.cfg.get("lang"): return
        self.cfg["lang"] = code
        save_config(self.cfg)
        for c, key in self._lang_options:
            if c == code:
                self._lang_label.set_text(t(self.strings, key))
                break
        new_strings = load_i18n(resolve_lang(code))
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=t(new_strings, "restart_hint"),
        )
        dlg.run()
        dlg.destroy()


# ── Tray icon ─────────────────────────────────────────────────────────────────

class TrayIcon:
    def __init__(self, window, strings):
        self.window  = window
        self.strings = strings

        icon_path = ensure_tray_icon()
        self.indicator = AppIndicator3.Indicator.new(
            "unicode-picker", icon_path,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title(t(strings, "app_title"))

        self.menu = Gtk.Menu()
        self.indicator.set_menu(self.menu)
        self.rebuild_menu()

    def rebuild_menu(self):
        s = self.strings
        for child in self.menu.get_children():
            self.menu.remove(child)

        item_open = Gtk.MenuItem(label=t(s, "tray_open"))
        item_open.connect("activate", self._on_open)
        self.menu.append(item_open)

        self.menu.append(Gtk.SeparatorMenuItem())

        header = Gtk.MenuItem(label=t(s, "tray_recent_header"))
        header.set_sensitive(False)
        self.menu.append(header)

        recent = self.window.cfg.get("recent", [])
        if not recent:
            it = Gtk.MenuItem(label=t(s, "tray_no_recent"))
            it.set_sensitive(False)
            self.menu.append(it)
        else:
            for entry in recent[:8]:
                char = entry.get("char")
                name = entry.get("name", "")
                label = f"{char_display_label(char)}  {name}"
                it = Gtk.MenuItem(label=label)
                it.connect("activate", self._on_pick_recent, char, name)
                self.menu.append(it)

        self.menu.append(Gtk.SeparatorMenuItem())

        item_quit = Gtk.MenuItem(label=t(s, "tray_quit"))
        item_quit.connect("activate", lambda _i: Gtk.main_quit())
        self.menu.append(item_quit)

        self.menu.show_all()

    def _on_open(self, _item):
        self.window.show_all()
        self.window.present()

    def _on_pick_recent(self, _item, char, name):
        self.window._on_pick(char, name)
        self.rebuild_menu()


def main():
    win = UnicodePickerWindow()

    no_tray = "--no-tray" in __import__("sys").argv
    if HAS_INDICATOR and not no_tray:
        tray = TrayIcon(win, win.strings)
        orig_add = win._add_to_recent
        def add_and_refresh(char, name):
            orig_add(char, name)
            tray.rebuild_menu()
        win._add_to_recent = add_and_refresh
    else:
        win.connect("destroy", Gtk.main_quit)

    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
