#!/usr/bin/env python3
"""Generate dist/plugin.js (Mora Bygg theme for Hermes Desktop) from the design source.

Reads colour tokens from mora-tokens.css (generated from Design/DESIGN.md) and
the self-hosted Source Sans 3 fonts from Design/fonts/. Never hand-edit
plugin.js: re-run this script after a design change.

    python3 -I build.py                  # -> dist/plugin.js
    python3 -I build.py --preview dark   # verification build: one palette in both modes
    ./install.sh                         # build + install into Hermes Desktop

Light = DESIGN.md v1 as written. Dark = derived here from the same tokens only
(ink, canvas, primary, status colours mixed in sRGB). DESIGN.md does not define
a dark mode yet; the derivation is listed in README.md so it can be promoted
into DESIGN.md (or rejected) by the design owner.
"""

import base64
import json
import os
import re
import sys
from pathlib import Path

DESIGN = Path(os.environ.get("MORA_DESIGN", Path.home() / "Mora Bygg" / "mb-Agentic" / "MoraBygg" / "Design"))
REPO = Path(__file__).resolve().parent

args = sys.argv[1:]
PREVIEW = None
if "--preview" in args:
    i = args.index("--preview")
    PREVIEW = args[i + 1]
    del args[i:i + 2]
    assert PREVIEW in ("light", "dark"), "--preview light|dark"
OUT = Path(args[0]) if args else REPO / "dist" / "plugin.js"

AA = 4.5
CONTROL = 3.0  # WCAG 1.4.11 non-text contrast (DESIGN.md: borderStrong >= 3:1)


# ── colour helpers ─────────────────────────────────────────────────────────

def tokens() -> dict:
    css = (DESIGN / "mora-tokens.css").read_text()
    return {k: v.lower() for k, v in re.findall(r"--color-([A-Za-z]+):\s*(#[0-9a-fA-F]{6})\s*;", css)}


def rgb(h: str):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a: str, b: str, w: float) -> str:
    """a moved w of the way toward b (sRGB)."""
    return "#" + "".join(f"{round(x * (1 - w) + y * w):02x}" for x, y in zip(rgb(a), rgb(b)))


def rgba(h: str, a: float) -> str:
    r, g, b = rgb(h)
    return f"rgba({r}, {g}, {b}, {a})"


def lum(h: str) -> float:
    c = [v / 255 for v in rgb(h)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def font_b64(name: str) -> str:
    return base64.b64encode((DESIGN / "fonts" / name).read_bytes()).decode()


# ── palettes ───────────────────────────────────────────────────────────────

def light(t: dict) -> dict:
    """DESIGN.md v1, token for token."""
    return {
        "background": t["canvas"],
        "foreground": t["ink"],
        "card": t["surface"],
        "cardForeground": t["ink"],
        "muted": t["canvas"],
        "mutedForeground": t["textMuted"],
        "popover": t["surface"],
        "popoverForeground": t["ink"],
        "primary": t["primary"],
        "primaryForeground": t["onPrimary"],
        "secondary": t["primarySoft"],
        "secondaryForeground": t["primary"],
        "accent": t["primarySoft"],                # nav-item-active / selected row
        "accentForeground": t["primary"],
        "border": t["border"],
        "input": t["borderStrong"],                # control-border
        "ring": t["primary"],
        "midground": t["primary"],
        "midgroundForeground": t["onPrimary"],
        "composerRing": t["primary"],
        "destructive": t["danger"],
        "destructiveForeground": t["onPrimary"],
        "sidebarBackground": t["surface"],         # sidebar component: surface
        "sidebarBorder": t["border"],
        "userBubble": t["primarySoft"],
        "userBubbleBorder": t["border"],
    }


def dark_tokens(t: dict) -> dict:
    """Dark mode derived only from DESIGN.md tokens: ink becomes the canvas,
    canvas becomes the text, Mora-blå and status colours are lifted toward
    canvas until they clear AA on every dark surface."""
    ink, canvas = t["ink"], t["canvas"]
    d = {
        "bg": ink,                                  # hammer black
        "card": mix(ink, canvas, 0.05),
        "pop": mix(ink, canvas, 0.08),
        "text": canvas,
        "muted": mix(canvas, ink, 0.40),
        "border": mix(ink, canvas, 0.15),
        "control": mix(ink, canvas, 0.45),
        "primary": mix(t["primary"], canvas, 0.60),  # Mora-blå, lifted
        "ok": mix(t["ok"], canvas, 0.45),
        "warning": mix(t["warning"], canvas, 0.45),
        "danger": mix(t["danger"], canvas, 0.50),
    }
    d["accent"] = mix(ink, t["primary"], 0.45)       # selected state: Mora-blå tint
    return d


def dark(t: dict) -> dict:
    d = dark_tokens(t)
    return {
        "background": d["bg"],
        "foreground": d["text"],
        "card": d["card"],
        "cardForeground": d["text"],
        "muted": d["card"],
        "mutedForeground": d["muted"],
        "popover": d["pop"],
        "popoverForeground": d["text"],
        "primary": d["primary"],
        "primaryForeground": t["ink"],
        "secondary": d["card"],
        "secondaryForeground": d["text"],
        "accent": d["accent"],
        "accentForeground": d["text"],
        "border": d["border"],
        "input": d["control"],
        "ring": d["primary"],
        "midground": d["primary"],
        "midgroundForeground": t["ink"],
        "composerRing": d["primary"],
        "destructive": d["danger"],
        "destructiveForeground": t["ink"],
        "sidebarBackground": d["bg"],
        "sidebarBorder": d["border"],
        "userBubble": d["pop"],
        "userBubbleBorder": d["border"],
    }


def terminal(t: dict, mode: str) -> dict:
    if mode == "light":
        return {
            "foreground": t["ink"], "cursor": t["primary"], "selectionBackground": rgba(t["primary"], 0.2),
            "red": t["danger"], "brightRed": t["danger"], "green": t["ok"], "brightGreen": t["ok"],
            "yellow": t["warning"], "brightYellow": t["warning"], "blue": t["primary"], "brightBlue": t["primary"],
            "black": t["ink"], "brightBlack": t["textMuted"], "white": t["textSoft"], "brightWhite": t["ink"],
        }
    d = dark_tokens(t)
    return {
        "foreground": d["text"], "cursor": d["primary"], "selectionBackground": rgba(d["primary"], 0.3),
        "red": d["danger"], "brightRed": d["danger"], "green": d["ok"], "brightGreen": d["ok"],
        "yellow": d["warning"], "brightYellow": d["warning"], "blue": d["primary"], "brightBlue": d["primary"],
        "brightBlack": d["muted"], "white": d["text"], "brightWhite": t["surface"],
    }


# ── contrast gate ──────────────────────────────────────────────────────────

def check(name: str, c: dict) -> list:
    surfaces = {k: c[k] for k in ("background", "card", "popover", "sidebarBackground", "accent", "muted")}
    pairs = []
    for fg in ("foreground", "mutedForeground", "primary", "destructive"):
        for sk, sv in surfaces.items():
            if fg == "mutedForeground" and sk == "accent":
                continue  # muted text is not used on the selected fill
            pairs.append((f"{fg} on {sk}", c[fg], sv, AA))
    pairs += [
        ("accentForeground on accent", c["accentForeground"], c["accent"], AA),
        ("primaryForeground on primary", c["primaryForeground"], c["primary"], AA),
        ("destructiveForeground on destructive", c["destructiveForeground"], c["destructive"], AA),
        ("input (control) on background", c["input"], c["background"], CONTROL),
        ("input (control) on card", c["input"], c["card"], CONTROL),
    ]
    rows, fails = [], []
    for label, fg, bg, need in pairs:
        r = contrast(fg, bg)
        rows.append((r, f"{name}: {label} {r:.2f}"))
        if r < need:
            fails.append(f"{name}: {label} {r:.2f} < {need}")
    if fails:
        raise SystemExit("contrast gate failed:\n  " + "\n  ".join(fails))
    worst = min(rows)
    print(f"  {name}: {len(rows)} pairs pass, worst {worst[1].split(': ', 1)[1]}")
    return rows


# ── output ─────────────────────────────────────────────────────────────────

def custom_css(t: dict) -> str:
    d = dark_tokens(t)
    scope = ":root[data-hermes-theme='mora-bygg']"
    return f"""
@font-face {{
  font-family: 'Source Sans 3 Variable';
  font-style: normal;
  font-display: swap;
  font-weight: 200 900;
  src: url(data:font/woff2;base64,{font_b64('SourceSans3-Variable.woff2')}) format('woff2-variations');
}}
@font-face {{
  font-family: 'Source Sans 3 Variable';
  font-style: italic;
  font-display: swap;
  font-weight: 200 900;
  src: url(data:font/woff2;base64,{font_b64('SourceSans3-Variable-Italic.woff2')}) format('woff2-variations');
}}
/* Core mixes every surface toward its own grey (light #f3f3f3/#fcfcfc,
   dark #0d0d0e/#161618). Pin the mixes so the DESIGN.md tokens paint as-is.
   Status colours: core bends success toward the accent (Mora-blå would turn
   it teal) - pin ok/danger to the design tokens. No gradients (DESIGN.md). */
{scope} {{
  --theme-mix-chrome: 100% !important;
  --theme-mix-sidebar: 100% !important;
  --theme-mix-card: 100% !important;
  --theme-mix-elevated: 100% !important;
  --theme-mix-bubble: 100% !important;
  --ui-success: {t['ok']} !important;
  --ui-green: {t['ok']};
  --ui-red: {t['danger']};
  --ui-selection-background: {rgba(t['primary'], 0.2)} !important;
}}
{scope}[data-hermes-mode='dark'] {{
  --ui-success: {d['ok']} !important;
  --ui-green: {d['ok']};
  --ui-red: {d['danger']};
  --ui-selection-background: {rgba(d['primary'], 0.32)} !important;
}}
""".strip()


def build() -> str:
    t = tokens()
    lc, dc = light(t), dark(t)
    print("contrast (WCAG):")
    check("light", lc)
    check("dark", dc)

    lt, dt = terminal(t, "light"), terminal(t, "dark")
    if PREVIEW == "light":
        dc, dt = lc, lt
    elif PREVIEW == "dark":
        lc, lt = dc, dt

    theme = {
        "name": "mora-bygg",
        "label": "Mora Bygg",
        "description": "Mora Bygg design v1: Mora-blå för handling, bläck för text, ljust och mörkt läge",
        "colors": lc,
        "darkColors": dc,
        "typography": {
            "fontSans": ('"Source Sans 3 Variable", "Source Sans 3", "Segoe UI", -apple-system, '
                         'BlinkMacSystemFont, system-ui, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", emoji'),
            "fontMono": ('"JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace, '
                         '"Apple Color Emoji", "Segoe UI Emoji", emoji'),
        },
        "terminal": lt,
        "darkTerminal": dt,
        "customCSS": custom_css(t),
    }

    banner = "PREVIEW BUILD (" + PREVIEW + " only) - do not ship" if PREVIEW else "Do not edit by hand."
    return f"""// GENERATED by build.py from Mora Bygg Design/DESIGN.md v1. {banner}
import {{ PALETTE_AREA, THEMES_AREA, host, requestTheme }} from '@hermes/plugin-sdk'

const ID = 'mora-bygg-theme'
const THEME = {json.dumps(theme, indent=2, ensure_ascii=False)}

function activate() {{
  if (!requestTheme(THEME.name)) {{
    host.notifyError('Mora Bygg-temat kunde inte aktiveras.')
  }}
}}

export default {{
  id: ID,
  name: 'Mora Bygg Theme',
  register(ctx) {{
    ctx.register({{ id: 'mora-bygg', area: THEMES_AREA, data: THEME }})
    ctx.register({{
      id: 'activate',
      area: PALETTE_AREA,
      data: {{ id: 'mora-bygg-theme.activate', label: 'Mora Bygg: Aktivera tema', keywords: ['theme', 'tema', 'mora', 'bygg'], run: activate }}
    }})

    // Select it once on first install; afterwards the user's own pick wins.
    if (!ctx.storage.get('autoApplied', false)) {{
      ctx.storage.set('autoApplied', true)
      queueMicrotask(activate)
    }}
  }}
}}
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
