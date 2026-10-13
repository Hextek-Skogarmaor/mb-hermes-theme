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


def dark_tokens(t: dict, plus: bool = False) -> dict:
    """Dark mode derived only from DESIGN.md tokens: ink becomes the canvas,
    canvas becomes the text, Mora-blå and status colours are lifted toward
    canvas until they clear AA on every dark surface.

    plus=True: "midnight Mora-blå" - ink tinted 20 % toward primary, sidebar
    10 %, so the blue reads as atmosphere and not only as an accent."""
    ink, canvas, primary = t["ink"], t["canvas"], t["primary"]
    bg = mix(ink, primary, 0.20) if plus else ink
    card_w, pop_w = (0.06, 0.10) if plus else (0.05, 0.08)
    d = {
        "bg": bg,
        "sidebar": mix(ink, primary, 0.10) if plus else ink,
        "card": mix(bg, canvas, card_w),
        "pop": mix(bg, canvas, pop_w),
        "text": canvas,
        "muted": mix(canvas, bg, 0.35 if plus else 0.40),
        "border": mix(bg, canvas, 0.15),
        "control": mix(bg, canvas, 0.45),
        "primary": mix(primary, canvas, 0.60),       # Mora-blå, lifted
        "ok": mix(t["ok"], canvas, 0.45),
        "warning": mix(t["warning"], canvas, 0.45),
        "danger": mix(t["danger"], canvas, 0.55 if plus else 0.50),
    }
    d["accent"] = mix(bg, primary, 0.45)             # selected state: Mora-blå tint
    return d


def dark(t: dict, plus: bool = False) -> dict:
    d = dark_tokens(t, plus)
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
        "sidebarBackground": d["sidebar"],
        "sidebarBorder": d["border"],
        "userBubble": d["pop"],
        "userBubbleBorder": d["border"],
    }


def terminal(t: dict, mode: str, plus: bool = False) -> dict:
    if mode == "light":
        return {
            "foreground": t["ink"], "cursor": t["primary"], "selectionBackground": rgba(t["primary"], 0.2),
            "red": t["danger"], "brightRed": t["danger"], "green": t["ok"], "brightGreen": t["ok"],
            "yellow": t["warning"], "brightYellow": t["warning"], "blue": t["primary"], "brightBlue": t["primary"],
            "black": t["ink"], "brightBlack": t["textMuted"], "white": t["textSoft"], "brightWhite": t["ink"],
        }
    d = dark_tokens(t, plus)
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


# ── Plus: gradients ────────────────────────────────────────────────────────
#
# DESIGN.md v1 says "no gradients". Plus is an explicit, opt-in departure that
# Jerry asked for: same tokens, more atmosphere. Every gradient stop is a token
# mix, and the gate below checks text against the lightest/darkest stop.

def plus_stops(t: dict) -> dict:
    canvas, primary, surface = t["canvas"], t["primary"], t["surface"]
    d = dark_tokens(t, plus=True)
    return {
        "light": {
            "glow": (primary, 0.08),                       # radial from the top
            "top": canvas,
            "bottom": mix(canvas, primary, 0.04),
            "sidebarTop": surface,
            "sidebarBottom": t["primarySoft"],
            "peak": mix(canvas, primary, 0.08),            # glow centre, worst case
        },
        "dark": {
            "glow": (primary, 0.55),
            "top": d["bg"],
            "bottom": mix(t["ink"], primary, 0.12),
            "sidebarTop": d["sidebar"],
            "sidebarBottom": mix(d["sidebar"], primary, 0.22),
            "peak": mix(d["bg"], primary, 0.55),
        },
    }


def check_plus(t: dict, lc: dict, dc: dict) -> None:
    g = plus_stops(t)
    fails, worst = [], []
    for mode, c in (("light", lc), ("dark", dc)):
        for stop in ("peak", "top", "bottom", "sidebarTop", "sidebarBottom"):
            for fg in ("foreground", "mutedForeground", "primary"):
                r = contrast(c[fg], g[mode][stop])
                worst.append((r, f"plus {mode}: {fg} on gradient {stop} {r:.2f}"))
                if r < AA:
                    fails.append(f"plus {mode}: {fg} on gradient {stop} {r:.2f} < {AA}")
    if fails:
        raise SystemExit("contrast gate failed:\n  " + "\n  ".join(fails))
    w = min(worst)
    print(f"  plus gradients: {len(worst)} pairs pass, worst {w[1].split(': ', 1)[1]}")


def plus_css(t: dict) -> str:
    g = plus_stops(t)
    base = ":root[data-hermes-theme='mora-bygg-plus']"
    solid = f"{base}:not([data-hermes-glass])"
    glass = f"{base}[data-hermes-glass]"
    out = []
    for mode in ("light", "dark"):
        m = g[mode]
        glow = f"radial-gradient(130% 75% at 50% -15%, {rgba(*m['glow'])} 0%, transparent 70%)"
        side_tint = f"linear-gradient(180deg, transparent 0%, transparent 45%, {rgba(t['primary'], 0.06 if mode == 'light' else 0.22)} 100%)"
        out.append(f"""{solid}[data-hermes-mode='{mode}'] [data-chat-surface] {{
  background-color: {m['top']};
  background-image:
    {glow},
    linear-gradient(180deg, {m['top']} 0%, {m['bottom']} 100%);
}}
{solid}[data-hermes-mode='{mode}'] [data-tour='sessions-sidebar'] {{
  background-image: linear-gradient(180deg, {m['sidebarTop']} 0%, {m['sidebarTop']} 45%, {m['sidebarBottom']} 100%);
}}
/* Glass: the window material shows through, so only translucent light is
   layered on top - never an opaque fill that would hide the glass. */
{glass}[data-hermes-mode='{mode}'] [data-chat-surface] {{
  background-image: {glow};
}}
{glass}[data-hermes-mode='{mode}'] [data-tour='sessions-sidebar'] {{
  background-image: {side_tint};
}}""")
    out.append(f"""{base} [data-chat-surface] [data-slot='composer-bounds'] {{
  background: transparent !important;
}}""")
    return "\n".join(out)


# ── output ─────────────────────────────────────────────────────────────────

def custom_css(t: dict, name: str, plus: bool = False) -> str:
    d = dark_tokens(t, plus)
    scope = f":root[data-hermes-theme='{name}']"
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
{plus_css(t) if plus else ''}
""".strip()


FONT_SANS = ('"Source Sans 3 Variable", "Source Sans 3", "Segoe UI", -apple-system, '
             'BlinkMacSystemFont, system-ui, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", emoji')
FONT_MONO = ('"JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace, '
             '"Apple Color Emoji", "Segoe UI Emoji", emoji')


def theme(t: dict, name: str, label: str, description: str, plus: bool) -> dict:
    lc, dc = light(t), dark(t, plus)
    lt, dt = terminal(t, "light"), terminal(t, "dark", plus)
    if PREVIEW == "light":
        dc, dt = lc, lt
    elif PREVIEW == "dark":
        lc, lt = dc, dt
    return {
        "name": name,
        "label": label,
        "description": description,
        "colors": lc,
        "darkColors": dc,
        "typography": {"fontSans": FONT_SANS, "fontMono": FONT_MONO},
        "terminal": lt,
        "darkTerminal": dt,
        "customCSS": custom_css(t, name, plus),
    }


def build() -> str:
    t = tokens()
    print("contrast (WCAG):")
    check("light", light(t))
    check("dark", dark(t))
    check("plus dark", dark(t, plus=True))
    check_plus(t, light(t), dark(t, plus=True))

    themes = [
        theme(t, "mora-bygg", "Mora Bygg",
              "Mora Bygg design v1: Mora-blå för handling, bläck för text, ljust och mörkt läge", False),
        theme(t, "mora-bygg-plus", "Mora Bygg Plus",
              "Mora Bygg med gradienter: blått ljus uppifrån, midnattsblått mörkt läge", True),
    ]

    banner = "PREVIEW BUILD (" + PREVIEW + " only) - do not ship" if PREVIEW else "Do not edit by hand."
    return f"""// GENERATED by build.py from Mora Bygg Design/DESIGN.md v1. {banner}
import {{ PALETTE_AREA, THEMES_AREA, host, requestTheme }} from '@hermes/plugin-sdk'

const ID = 'mora-bygg-theme'
const THEMES = {json.dumps(themes, indent=2, ensure_ascii=False)}

function activate(name) {{
  if (!requestTheme(name)) {{
    host.notifyError('Mora Bygg-temat kunde inte aktiveras.')
  }}
}}

export default {{
  id: ID,
  name: 'Mora Bygg Theme',
  register(ctx) {{
    for (const theme of THEMES) {{
      ctx.register({{ id: theme.name, area: THEMES_AREA, data: theme }})
      ctx.register({{
        id: `activate-${{theme.name}}`,
        area: PALETTE_AREA,
        data: {{
          id: `mora-bygg-theme.activate.${{theme.name}}`,
          label: `${{theme.label}}: Aktivera tema`,
          keywords: ['theme', 'tema', 'mora', 'bygg', 'plus', 'gradient'],
          run: () => activate(theme.name)
        }}
      }})
    }}

    // Select the plain theme once on first install; afterwards the user's pick wins.
    if (!ctx.storage.get('autoApplied', false)) {{
      ctx.storage.set('autoApplied', true)
      queueMicrotask(() => activate('mora-bygg'))
    }}
  }}
}}
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
