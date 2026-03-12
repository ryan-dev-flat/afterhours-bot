"""
After-Hours Bot — Demo Video Generator v2
Proper chat bubble UI, hook screen, CTA, ~90s runtime.
Output: demo_video.mp4
"""

import os, sys, textwrap
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H  = 1280, 720
FPS   = 30
CHAT_W = 640           # width of the chat panel (right half)
CHAT_X = W - CHAT_W   # left edge of chat panel

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK   = (14, 16, 22)
BG_PANEL  = (22, 25, 35)
BG_LEFT   = (18, 20, 30)
ACCENT    = (64, 196, 255)     # cyan-blue headline
GREEN     = (52, 211, 153)     # bot message
BLUE      = (99, 179, 237)     # customer message
AMBER     = (251, 191, 36)     # notification / highlight
WHITE     = (240, 242, 248)
GRAY      = (120, 128, 150)
DIVIDER   = (35, 40, 58)
BUBBLE_BOT= (32, 38, 58)
BUBBLE_CUS= (25, 65, 110)
RED_SOFT  = (239, 100, 100)

# ── Fonts ─────────────────────────────────────────────────────────────────────
def font(size, bold=False):
    paths = ["C:/Windows/Fonts/segoeui.ttf",
             "C:/Windows/Fonts/arial.ttf",
             "C:/Windows/Fonts/verdana.ttf"]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F_HERO   = font(52)
F_SUB    = font(28)
F_LABEL  = font(18)
F_MSG    = font(20)
F_SMALL  = font(15)
F_CTA    = font(36)
F_STAT   = font(42)

# ── Helpers ───────────────────────────────────────────────────────────────────
def wrap_text(text, max_px, f):
    words = text.split()
    dummy = Image.new("RGB", (1, 1))
    d = ImageDraw.Draw(dummy)
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) <= max_px:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]

def text_h(lines, line_h):
    return len(lines) * line_h

def rounded_rect(d, xy, radius, fill):
    x0, y0, x1, y1 = xy
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)

# ── Scene builders ────────────────────────────────────────────────────────────

def scene_hook():
    """Opening hook — dark, dramatic."""
    img = Image.new("RGB", (W, H), BG_DARK)
    d   = ImageDraw.Draw(img)

    # Subtle grid lines
    for x in range(0, W, 80):
        d.line([(x, 0), (x, H)], fill=(22, 26, 38), width=1)
    for y in range(0, H, 80):
        d.line([(0, y), (W, y)], fill=(22, 26, 38), width=1)

    # Big time stamp
    d.text((W//2, 200), "9:14 PM", font=F_HERO, fill=GRAY, anchor="mm")
    d.text((W//2, 275), "A customer just texted your business.", font=F_SUB, fill=WHITE, anchor="mm")
    d.text((W//2, 320), "You're closed. No one will see it until morning.", font=F_SUB, fill=GRAY, anchor="mm")
    d.text((W//2, 400), "That job just went to your competitor.", font=F_CTA, fill=RED_SOFT, anchor="mm")

    # Bottom label — raised to avoid mobile crop
    d.text((W//2, H - 80), "Unless you have this.", font=F_SUB, fill=ACCENT, anchor="mm")

    return np.array(img)


def scene_intro():
    """Brand intro screen."""
    img = Image.new("RGB", (W, H), BG_DARK)
    d   = ImageDraw.Draw(img)

    # Accent bar
    d.rectangle([(0, H//2 - 4), (W, H//2 + 4)], fill=ACCENT)

    d.text((W//2, H//2 - 80), "After-Hours AI Lead Capture", font=F_HERO, fill=WHITE, anchor="mm")
    d.text((W//2, H//2 + 60), "Watch a real conversation. Zero humans involved.", font=F_SUB, fill=GRAY, anchor="mm")
    d.text((W//2, H//2 + 100), "Summit Home Services  |  Plumbing & HVAC", font=F_SMALL, fill=GRAY, anchor="mm")

    return np.array(img)


def build_chat_frame(messages, highlight=False, notification=None):
    """
    Render a split-screen frame:
    Left  — info panel with stats
    Right — chat conversation
    """
    img = Image.new("RGB", (W, H), BG_DARK)
    d   = ImageDraw.Draw(img)

    # ── Left panel ─────────────────────────────────────────────────────────
    d.rectangle([(0, 0), (CHAT_X - 1, H)], fill=BG_LEFT)

    # Business name header
    d.rectangle([(0, 0), (CHAT_X - 1, 70)], fill=(20, 22, 34))
    d.text((30, 22), "Summit Home Services", font=F_LABEL, fill=ACCENT)
    d.text((30, 44), "After-Hours AI Bot  |  LIVE", font=F_SMALL, fill=GREEN)

    # Stats
    stats = [
        ("24 / 7", "Always On"),
        ("< 3s", "Response Time"),
        ("100%", "Leads Captured"),
        ("$0", "Staff Cost"),
    ]
    sy = 110
    for val, lbl in stats:
        d.text((50, sy), val, font=F_STAT, fill=ACCENT)
        d.text((50, sy + 52), lbl, font=F_SMALL, fill=GRAY)
        sy += 110

    # Tagline
    d.rectangle([(20, H - 80), (CHAT_X - 20, H - 20)], fill=(25, 30, 48), outline=DIVIDER)
    d.text((CHAT_X // 2, H - 50), "No missed leads. Ever.", font=F_LABEL, fill=WHITE, anchor="mm")

    # ── Right chat panel ────────────────────────────────────────────────────
    d.rectangle([(CHAT_X, 0), (W, H)], fill=BG_PANEL)
    d.text((CHAT_X + CHAT_W // 2, 35), "Chat with Summit", font=F_LABEL, fill=GRAY, anchor="mm")
    d.rectangle([(CHAT_X, 60), (W, 62)], fill=DIVIDER)

    # Render messages
    MSG_PAD   = 20
    BUBBLE_PAD = 12
    MAX_MSG_W  = CHAT_W - 100
    cy = 80

    for (speaker, text) in messages:
        is_bot    = (speaker == "BOT")
        is_notify = (speaker == "NOTIFY")
        is_emerg  = (speaker == "EMERGENCY")

        if is_notify or is_emerg:
            color = AMBER if is_notify else RED_SOFT
            lines = wrap_text(text, CHAT_W - 60, F_SMALL)
            bh    = len(lines) * 22 + BUBBLE_PAD * 2
            d.rectangle([(CHAT_X + 10, cy), (W - 10, cy + bh)],
                        fill=(45, 36, 10) if is_notify else (50, 20, 20))
            for i, ln in enumerate(lines):
                d.text((CHAT_X + 20, cy + BUBBLE_PAD + i * 22), ln, font=F_SMALL, fill=color)
            cy += bh + 10
            continue

        lines = wrap_text(text, MAX_MSG_W - BUBBLE_PAD * 2, F_MSG)
        bh    = len(lines) * 28 + BUBBLE_PAD * 2
        bw    = min(MAX_MSG_W, int(max(
            ImageDraw.Draw(Image.new("RGB",(1,1))).textlength(ln, font=F_MSG)
            for ln in lines
        )) + BUBBLE_PAD * 2 + 10)

        if is_bot:
            bx = CHAT_X + MSG_PAD
            bubble_fill = BUBBLE_BOT
            label_color = GREEN
            label = "AI Bot"
        else:
            bx = W - MSG_PAD - bw
            bubble_fill = BUBBLE_CUS
            label_color = BLUE
            label = "Customer"

        d.text((bx, cy), label, font=F_SMALL, fill=label_color)
        cy += 20
        rounded_rect(d, (bx, cy, bx + bw, cy + bh), 12, bubble_fill)

        for i, ln in enumerate(lines):
            d.text((bx + BUBBLE_PAD, cy + BUBBLE_PAD + i * 28), ln,
                   font=F_MSG, fill=WHITE)
        cy += bh + 10

        if cy > H - 60:
            break

    # Notification flash overlay
    if highlight and notification:
        d.rectangle([(CHAT_X, H - 80), (W, H)], fill=(50, 40, 5))
        d.text((CHAT_X + CHAT_W // 2, H - 50),
               notification, font=F_SMALL, fill=AMBER, anchor="mm")

    return np.array(img)


def scene_cta():
    """Final call-to-action screen."""
    img = Image.new("RGB", (W, H), BG_DARK)
    d   = ImageDraw.Draw(img)

    d.rectangle([(0, 0), (W, 8)], fill=ACCENT)
    d.rectangle([(0, H - 8), (W, H)], fill=ACCENT)

    d.text((W//2, 160), "Want this for your business?", font=F_HERO, fill=WHITE, anchor="mm")
    d.text((W//2, 240), "Setup takes less than 1 hour.", font=F_SUB, fill=GREEN, anchor="mm")

    # Pricing box
    d.rounded_rectangle([(W//2 - 280, 290), (W//2 + 280, 420)], radius=16, fill=(25, 30, 48))
    d.text((W//2, 330), "Starting at $400 / month", font=F_CTA, fill=AMBER, anchor="mm")
    d.text((W//2, 385), "Costs less than a single missed job.", font=F_SMALL, fill=GRAY, anchor="mm")

    d.text((W//2, 480), "Plumbers  |  HVAC  |  Dentists  |  Gyms  |  Contractors", font=F_SMALL, fill=GRAY, anchor="mm")
    d.text((W//2, 540), "Drop a comment or DM to get started.", font=F_SUB, fill=ACCENT, anchor="mm")

    # Brand URL + tagline
    d.text((W//2, H - 65), "yourwebsite.com  |  DM or comment below to get started", font=F_LABEL, fill=ACCENT, anchor="mm")
    d.text((W//2, H - 35), "AI-powered  |  No staff required  |  Instant lead capture", font=F_SMALL, fill=GRAY, anchor="mm")

    return np.array(img)


# ── Main video assembly ───────────────────────────────────────────────────────

CONVERSATION = [
    ("CUSTOMER", "hi"),
    ("BOT",      "Hey there! Welcome to Summit Home Services. How can we help you tonight?"),
    ("CUSTOMER", "my kitchen drain is completely clogged"),
    ("BOT",      "Got it - we can definitely help. What's your name and best time for a callback tomorrow?"),
    ("CUSTOMER", "Tomorrow morning around 9am"),
    ("BOT",      "Perfect! And your name and callback number?"),
    ("CUSTOMER", "It's Sarah, 720-555-4321"),
    ("NOTIFY",   "OWNER NOTIFIED  >>  Sarah | Drain cleaning | Tomorrow 9am | 720-555-4321"),
    ("BOT",      "Confirmed, Sarah! Drain cleaning, tomorrow 9am, call 720-555-4321. Mike will reach out to confirm. Thanks!"),
]

EMERGENCY = [
    ("EMERGENCY", "EMERGENCY TEST  >>  'help my pipe just burst'"),
    ("BOT",        "This sounds like an emergency. Call our 24/7 line NOW: (720) 555-0123 - we'll be there within the hour."),
]


def build_video():
    # Collect (frame_array, duration_seconds) pairs — no MoviePy needed
    frame_list = []

    frame_list.append((scene_hook(),  5.0))
    frame_list.append((scene_intro(), 3.0))

    # Build conversation progressively
    shown = []
    timings = [1.5, 3.0, 1.5, 3.5, 1.5, 2.5, 1.5, 3.0, 4.0]
    for msg, t in zip(CONVERSATION, timings):
        shown.append(msg)
        notif     = "OWNER NOTIFIED on owner's phone!" if any(s == "NOTIFY" for s, _ in shown) else None
        highlight = (msg[0] == "NOTIFY")
        frame     = build_chat_frame(shown, highlight=highlight, notification=notif if highlight else None)
        frame_list.append((frame, t))

    # Emergency demo
    shown_emerg = shown.copy()
    for msg in EMERGENCY:
        shown_emerg.append(msg)
        frame_list.append((build_chat_frame(shown_emerg), 3.5))

    # CTA
    frame_list.append((scene_cta(), 6.0))

    total_s      = sum(d for _, d in frame_list)
    total_frames = sum(int(round(d * FPS)) for _, d in frame_list)
    out          = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_video.mp4")

    print(f"Rendering {total_s:.1f}s video ({total_frames} frames) → {out}")

    with imageio.get_writer(out, fps=FPS, codec="libx264",
                            pixelformat="yuv420p",
                            ffmpeg_params=["-crf", "23"]) as writer:
        for idx, (frame, duration) in enumerate(frame_list):
            n = int(round(duration * FPS))
            for _ in range(n):
                writer.append_data(frame)
            print(f"  Scene {idx + 1}/{len(frame_list)} ✓", flush=True)

    print(f"Done: {out}")


if __name__ == "__main__":
    build_video()
