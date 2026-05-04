#!/usr/bin/env python3
"""
Claude Code statusline: shows context usage, rate limits, cost.
Receives JSON on stdin from Claude Code.
"""

import json
import sys
from datetime import datetime, timezone

# ── ANSI colours ────────────────────────────────────────────
R = "\033[0m"           # reset
BOLD = "\033[1m"
DIM = "\033[2m"

GREEN  = "\033[38;5;82m"   # bright green
YELLOW = "\033[38;5;220m"  # yellow
RED    = "\033[38;5;196m"  # red
ORANGE = "\033[38;5;208m"  # orange  (5h block)
BLUE   = "\033[38;5;39m"   # sky blue (7d block)
GREY   = "\033[38;5;245m"  # separator / model
CYAN   = "\033[38;5;87m"   # cost


def ctx_color(pct: float) -> str:
    if pct < 50:
        return GREEN
    if pct < 80:
        return YELLOW
    return RED


def c(color: str, text: str) -> str:
    return f"{color}{text}{R}"


def fmt_reset_in(ts: float) -> str:
    now = datetime.now(timezone.utc).timestamp()
    diff = ts - now
    if diff <= 0:
        return "resetting..."
    h = int(diff // 3600)
    m = int((diff % 3600) // 60)
    if h < 24:
        return f"resets in {h}h {m}m"
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return f"resets {dt.strftime('%a %H:%M')}"


def bar(pct: float, color: str, width: int = 6) -> str:
    filled = round(pct / 100 * width)
    filled = max(0, min(width, filled))
    return f"{color}{'█' * filled}{DIM}{'░' * (width - filled)}{R}"


SEP = c(GREY, "  |  ")


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        print(c(GREY, "waiting..."), end="")
        return

    parts = []

    # ── Context window ──────────────────────────────────────
    ctx = data.get("context_window", {})
    used_pct = ctx.get("used_percentage", 0)
    total = ctx.get("context_window_size", 200000)
    used_tokens = ctx.get("total_input_tokens", 0)

    if total:
        used_k = round(used_pct / 100 * total / 1000)
        total_k = round(total / 1000)
        col = ctx_color(used_pct)
        label = c(BOLD + col, "CTX")
        b = bar(used_pct, col)
        stat = c(col, f"{used_pct:.0f}%")
        detail = c(GREY, f"({used_k}k/{total_k}k)")
        parts.append(f"{label} {b} {stat} {detail}")

    # ── 5-hour rate limit ───────────────────────────────────
    rl = data.get("rate_limits", {})
    five = rl.get("five_hour", {})
    if five:
        pct5 = five.get("used_percentage", 0)
        reset5 = five.get("resets_at", 0)
        reset_str = c(GREY, f", {fmt_reset_in(reset5)}") if reset5 else ""
        label = c(BOLD + ORANGE, "5h")
        b = bar(pct5, ORANGE)
        stat = c(ORANGE, f"{pct5:.0f}%")
        parts.append(f"{label} {b} {stat}{reset_str}")

    # ── 7-day rate limit ────────────────────────────────────
    seven = rl.get("seven_day", {})
    if seven:
        pct7 = seven.get("used_percentage", 0)
        reset7 = seven.get("resets_at", 0)
        reset_str = c(GREY, f", {fmt_reset_in(reset7)}") if reset7 else ""
        label = c(BOLD + BLUE, "7d")
        b = bar(pct7, BLUE)
        stat = c(BLUE, f"{pct7:.0f}%")
        parts.append(f"{label} {b} {stat}{reset_str}")

    # ── Cost ────────────────────────────────────────────────
    cost = data.get("cost", {})
    cost_usd = cost.get("total_cost_usd", 0)
    if cost_usd and cost_usd > 0:
        parts.append(c(CYAN, f"${cost_usd:.4f}"))

    # ── Model ───────────────────────────────────────────────
    model = data.get("model", {})
    model_name = model.get("display_name", "") if isinstance(model, dict) else str(model)
    if model_name:
        parts.append(c(GREY, model_name))

    print(SEP.join(parts) if parts else c(GREY, "waiting..."), end="")


if __name__ == "__main__":
    main()
