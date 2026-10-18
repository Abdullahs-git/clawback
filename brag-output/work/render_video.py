"""
Clawback /brag Launch Video Renderer v2 - PROFESSIONAL GRADE
Generates 600 frames (20.0s @ 30fps, 1920x1080) with:
  - Radial gradient backgrounds with animated spotlight
  - Glowing neon accent borders (Gaussian blur compositing)
  - Smooth crossfade transitions between scenes
  - Animated counters that count up to final values
  - Animated progress bars and typing cursor effects
  - Bold typography hierarchy with massive headings
  - Professional card depth with layered shadows
"""

import os
import math
import time
from multiprocessing import Pool, cpu_count
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = 600
FPS = 30
TRANSITION_FRAMES = 18  # 0.6s crossfade between scenes

# Scene boundaries (frame ranges)
SCENE_1_END = 105
SCENE_2_END = 240
SCENE_3_END = 435
SCENE_4_END = 600

# === COLOR PALETTE ===
BG_BASE = (8, 10, 18)
BG_DARK = (11, 15, 25)
BG_CARD = (16, 22, 36)
BG_CARD_ELEVATED = (22, 30, 48)
BG_CARD_TOP = (28, 38, 58)
BORDER_SUBTLE = (35, 45, 65)
BORDER_CARD = (45, 58, 82)
BORDER_BRIGHT = (65, 80, 110)

TEXT_BRIGHT = (255, 255, 255)
TEXT_PRIMARY = (240, 244, 248)
TEXT_SECONDARY = (170, 185, 205)
TEXT_MUTED = (120, 140, 165)
TEXT_DIM = (80, 95, 120)

EMERALD = (16, 185, 129)
EMERALD_LIGHT = (52, 211, 153)
EMERALD_GLOW = (16, 185, 129, 100)
EMERALD_BG = (6, 50, 38)

ROSE = (244, 63, 94)
ROSE_LIGHT = (251, 113, 133)
ROSE_GLOW = (244, 63, 94, 100)
ROSE_BG = (80, 15, 30)

SKY = (56, 189, 248)
SKY_LIGHT = (125, 211, 252)
SKY_BG = (12, 45, 68)

AMD_RED = (237, 28, 36)
AMBER = (245, 158, 11)
VIOLET = (139, 92, 246)

# === FONTS ===
FONT_HERO = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 72)
FONT_HERO_LARGE = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 96)
FONT_TITLE = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 52)
FONT_HEADING = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 36)
FONT_SUBHEADING = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 28)
FONT_BODY = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 22)
FONT_BODY_BOLD = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 22)
FONT_BODY_LARGE = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 26)
FONT_MONO = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 20)
FONT_MONO_BOLD = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 22)
FONT_MONO_LARGE = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 28)
FONT_STAT_HUGE = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 64)
FONT_STAT_VAL = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 48)
FONT_BADGE = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 16)
FONT_BADGE_LARGE = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 20)
FONT_LABEL = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 15)
FONT_MICRO = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 13)


# === UTILITY FUNCTIONS ===

def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3

def ease_out_expo(t):
    t = max(0.0, min(1.0, t))
    return 1.0 if t >= 1.0 else 1.0 - 2.0 ** (-10.0 * t)

def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def create_gradient_bg(width, height, frame_idx):
    """Create a rich dark gradient background with animated radial spotlight."""
    im = Image.new('RGB', (width, height), BG_BASE)
    draw = ImageDraw.Draw(im)

    # Vertical gradient from dark top to slightly lighter bottom
    for y in range(height):
        t = y / height
        r = int(lerp(6, 14, t))
        g = int(lerp(8, 20, t))
        b = int(lerp(14, 32, t))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Animated radial spotlight (slow drift)
    spot_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    spot_draw = ImageDraw.Draw(spot_layer)

    # Primary spotlight - large, subtle emerald tint drifting slowly
    cx = int(width * 0.5 + math.sin(frame_idx * 0.008) * 200)
    cy = int(height * 0.35 + math.cos(frame_idx * 0.006) * 80)
    for r_radius in range(500, 0, -2):
        alpha = int(18 * (r_radius / 500.0))
        spot_draw.ellipse([(cx - r_radius, cy - r_radius), (cx + r_radius, cy + r_radius)],
                          fill=(16, 80, 65, alpha))

    # Secondary spotlight - rose accent, upper right
    cx2 = int(width * 0.82 + math.sin(frame_idx * 0.005 + 2.0) * 120)
    cy2 = int(height * 0.2 + math.cos(frame_idx * 0.007 + 1.0) * 60)
    for r_radius in range(300, 0, -3):
        alpha = int(10 * (r_radius / 300.0))
        spot_draw.ellipse([(cx2 - r_radius, cy2 - r_radius), (cx2 + r_radius, cy2 + r_radius)],
                          fill=(120, 20, 40, alpha))

    # Composite spotlight onto base
    im_rgba = im.convert('RGBA')
    im_rgba = Image.alpha_composite(im_rgba, spot_layer)

    return im_rgba


def draw_glow_rect(base_im, x1, y1, x2, y2, glow_color, glow_radius=20, intensity=120):
    """Draw a glowing rectangle border effect."""
    pad = glow_radius * 2
    gw = int(x2 - x1 + pad * 2)
    gh = int(y2 - y1 + pad * 2)
    glow_layer = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gc = (*glow_color[:3], intensity) if len(glow_color) == 3 else glow_color
    gd.rounded_rectangle([(pad, pad), (gw - pad, gh - pad)],
                          radius=16, outline=gc, width=4)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius))
    base_im.paste(glow_layer, (int(x1 - pad), int(y1 - pad)), glow_layer)


def draw_glow_circle(base_im, cx, cy, radius, glow_color, glow_radius=15, intensity=160):
    """Draw a glowing circle."""
    pad = glow_radius * 2
    size = int(radius * 2 + pad * 2)
    glow_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gc = (*glow_color[:3], intensity)
    gd.ellipse([(pad, pad), (size - pad, size - pad)], fill=gc)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius))
    base_im.paste(glow_layer, (int(cx - radius - pad), int(cy - radius - pad)), glow_layer)


def draw_card(draw, x1, y1, x2, y2, fill, outline=None, radius=16, width=1):
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, fill=fill,
                            outline=outline, width=width)


def draw_shadow_card(im, draw, x1, y1, x2, y2, fill, outline=None, radius=16,
                     shadow_offset=6, shadow_blur=12, width=1):
    """Draw a card with a soft drop shadow beneath it."""
    sw = int(x2 - x1 + shadow_blur * 4)
    sh = int(y2 - y1 + shadow_blur * 4)
    shadow = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    pad = shadow_blur * 2
    sd.rounded_rectangle([(pad, pad), (sw - pad, sh - pad)],
                          radius=radius, fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    im.paste(shadow, (int(x1 - shadow_blur * 2 + shadow_offset),
                       int(y1 - shadow_blur * 2 + shadow_offset)), shadow)
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, fill=fill,
                            outline=outline, width=width)


def draw_pill_badge(draw, text, x, y, bg, fg, border=None, font=FONT_BADGE):
    """Draw a rounded pill badge."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    px, py = 18, 8
    brd = border or bg
    draw.rounded_rectangle([(x, y), (x + tw + px * 2, y + th + py * 2)],
                            radius=th, fill=bg, outline=brd, width=1)
    draw.text((x + px, y + py - 1), text, fill=fg, font=font)
    return tw + px * 2


def draw_progress_bar(draw, x, y, w, h, progress, bg_color, fill_color, radius=6):
    """Animated horizontal progress bar."""
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius, fill=bg_color)
    fill_w = max(radius * 2, int(w * progress))
    draw.rounded_rectangle([(x, y), (x + fill_w, y + h)], radius=radius, fill=fill_color)


def animated_counter(target, t, prefix="", suffix="", decimals=0):
    """Return a string with a number counting up to target."""
    val = target * ease_out_expo(t)
    if decimals > 0:
        return f"{prefix}{val:,.{decimals}f}{suffix}"
    return f"{prefix}{int(val):,}{suffix}"


def draw_top_bar(im, draw, f):
    """Premium top navigation bar with frosted glass effect."""
    # Subtle line
    draw.line([(0, 78), (WIDTH, 78)], fill=BORDER_SUBTLE, width=1)

    # Logo mark - glowing red square
    draw_glow_circle(im, 98, 40, 8, AMD_RED, glow_radius=10, intensity=100)
    draw.rounded_rectangle([(78, 20), (118, 60)], radius=10, fill=AMD_RED)
    draw.text((88, 22), "C", fill=TEXT_BRIGHT, font=FONT_HEADING)

    # Logo text
    draw.text((130, 24), "CLAWBACK", fill=TEXT_BRIGHT, font=FONT_HEADING)

    # Dot separator
    draw.ellipse([(330, 38), (336, 44)], fill=TEXT_DIM)

    # Subtitle
    draw.text((348, 30), "Freight Contract Audit Engine", fill=TEXT_MUTED, font=FONT_BODY)

    # Right side - AMD badge with glow
    pulse = 0.5 + 0.5 * math.sin(f * 0.12)
    dot_col = lerp_color((16, 140, 100), (52, 211, 153), pulse)
    draw_glow_circle(im, 1636, 40, 5, EMERALD, glow_radius=8, intensity=int(80 + pulse * 60))
    draw.ellipse([(1631, 35), (1641, 45)], fill=dot_col)
    draw.text((1652, 28), "AMD ROCm", fill=EMERALD_LIGHT, font=FONT_BODY_BOLD)


# ============================================================================
# SCENE 1: THE HOOK - Commerce Billing Problem
# ============================================================================
def render_scene_1(im, draw, f):
    t_in = ease_out_cubic(min(1.0, f / 22.0))
    slide = int((1.0 - t_in) * 50)

    # Hero headline - massive, bold
    draw.text((120, 110 + slide), "Every shipper bleeds margin", fill=TEXT_BRIGHT, font=FONT_HERO)
    draw.text((120, 190 + slide), "on carrier invoices.", fill=TEXT_BRIGHT, font=FONT_HERO)

    # Subtitle with emerald accent
    draw.text((120, 290 + slide), "Thousands of line items. 40-page tariff contracts.", fill=TEXT_SECONDARY, font=FONT_BODY_LARGE)
    draw.text((120, 325 + slide), "Nobody checks. Carriers overcharge.", fill=TEXT_SECONDARY, font=FONT_BODY_LARGE)

    # Main invoice card with glow
    draw_glow_rect(im, 120, 400, 1800, 850, ROSE, glow_radius=25, intensity=40)
    draw_shadow_card(im, draw, 120, 400, 1800, 850, BG_CARD, BORDER_CARD, radius=20)

    # Card header bar
    draw.text((165, 425), "CARRIER EDI 210 FREIGHT INVOICE BATCH", fill=TEXT_MUTED, font=FONT_BADGE_LARGE)
    draw_pill_badge(draw, "1,250 LINES", 620, 422, ROSE_BG, ROSE, ROSE, FONT_BADGE)
    draw.line([(120, 465), (1800, 465)], fill=BORDER_SUBTLE, width=1)

    # Table headers
    headers = [("INVOICE", 165), ("ROUTE", 380), ("CLASS / WT", 820),
               ("BILLED", 1140), ("CONTRACT", 1380), ("DELTA", 1600)]
    for h, x in headers:
        draw.text((x, 478), h, fill=TEXT_DIM, font=FONT_LABEL)
    draw.line([(150, 502), (1780, 502)], fill=(30, 38, 55), width=1)

    # Invoice rows with staggered reveal
    rows = [
        ("INV-849201", "Chicago → Dallas  (840 mi)", "CL70 12,450 lb", "$2,450.00", "$2,127.50", "+$322.50"),
        ("INV-849202", "Atlanta → Newark  (750 mi)", "CL85  8,200 lb", "$1,680.00", "$1,540.00", "+$140.00"),
        ("INV-849203", "LA → Seattle  (1,130 mi)", "CL60 18,900 lb", "$3,890.00", "$3,610.00", "+$280.00"),
        ("INV-849204", "Memphis → Columbus  (480 mi)", "CL70  6,150 lb", "$1,120.00", "$1,045.00", "+$75.00"),
        ("INV-849205", "Denver → Kansas City  (600 mi)", "CL92  10,800 lb", "$2,310.00", "$2,180.00", "+$130.00"),
    ]

    y_row = 518
    for i, (inv, route, cls, billed, contract, delta) in enumerate(rows):
        row_t = ease_out_cubic(min(1.0, (f - 8 - i * 4) / 15.0))
        if row_t <= 0:
            continue
        alpha_factor = row_t
        row_slide = int((1.0 - row_t) * 30)

        # Highlight row bg on hover effect for last row
        if i == 0 and f > 40:
            draw.rounded_rectangle([(140, y_row - 5), (1780, y_row + 37)],
                                    radius=6, fill=(40, 18, 25))

        draw.text((165, y_row + row_slide), inv, fill=SKY, font=FONT_MONO)
        draw.text((380, y_row + row_slide), route, fill=TEXT_PRIMARY, font=FONT_BODY)
        draw.text((820, y_row + row_slide), cls, fill=TEXT_MUTED, font=FONT_BODY)
        draw.text((1140, y_row + row_slide), billed, fill=TEXT_PRIMARY, font=FONT_MONO_BOLD)
        draw.text((1380, y_row + row_slide), contract, fill=EMERALD, font=FONT_MONO_BOLD)
        draw.text((1600, y_row + row_slide), delta, fill=ROSE, font=FONT_MONO_BOLD)

        draw.line([(150, y_row + 42), (1780, y_row + 42)], fill=(25, 32, 48), width=1)
        y_row += 58

    # Critical alert banner (slides in from frame 40)
    if f >= 40:
        alert_t = ease_out_expo(min(1.0, (f - 40) / 20.0))
        alert_slide = int((1.0 - alert_t) * 60)
        alert_y = 870

        draw_glow_rect(im, 120, alert_y + alert_slide, 1800, alert_y + alert_slide + 95,
                        ROSE, glow_radius=20, intensity=int(60 * alert_t))
        draw_shadow_card(im, draw, 120, alert_y + alert_slide, 1800, alert_y + alert_slide + 95,
                          (45, 12, 22), ROSE, radius=14, width=2)

        if alert_t > 0.3:
            draw.text((175, alert_y + alert_slide + 18), "CRITICAL",
                      fill=ROSE, font=FONT_SUBHEADING)
            draw.text((355, alert_y + alert_slide + 22),
                      "$9,130.51 in unverified overcharges detected across 284 line items",
                      fill=TEXT_BRIGHT, font=FONT_BODY_BOLD)
            draw.text((175, alert_y + alert_slide + 58),
                      "Tariff rate mismatches, unapplied fuel surcharge credits, accessorial fee errors",
                      fill=TEXT_SECONDARY, font=FONT_BODY)


# ============================================================================
# SCENE 2: THE ARCHITECTURE - Two-Stage Air-Gap
# ============================================================================
def render_scene_2(im, draw, f):
    lf = f - SCENE_1_END
    t_in = ease_out_cubic(min(1.0, lf / 22.0))
    slide = int((1.0 - t_in) * 50)

    # Hero
    draw.text((120, 110 + slide), "LLMs hallucinate math.", fill=TEXT_BRIGHT, font=FONT_HERO)
    draw.text((120, 190 + slide), "Clawback doesn't let them try.", fill=EMERALD_LIGHT, font=FONT_HERO)

    draw.text((120, 290 + slide),
              "Two-stage architecture: AI extracts text.  Deterministic engine does arithmetic.",
              fill=TEXT_SECONDARY, font=FONT_BODY_LARGE)

    # --- LEFT CARD: Stage 1 (LLM Extraction) ---
    left_t = ease_out_cubic(min(1.0, (lf - 5) / 20.0))
    left_slide = int((1.0 - left_t) * 40)

    draw_glow_rect(im, 120, 380 + left_slide, 860, 920 + left_slide,
                    SKY, glow_radius=18, intensity=int(35 * left_t))
    draw_shadow_card(im, draw, 120, 380 + left_slide, 860, 920 + left_slide,
                      BG_CARD, BORDER_CARD, radius=18)

    # Stage 1 header
    draw_pill_badge(draw, "STAGE 1", 155, 405 + left_slide, SKY_BG, SKY, SKY, FONT_BADGE)
    draw.text((255, 402 + left_slide), "CLAUSE EXTRACTOR", fill=TEXT_MUTED, font=FONT_BADGE_LARGE)

    draw.text((155, 450 + left_slide), "AMD ROCm + Gemma", fill=TEXT_BRIGHT, font=FONT_HEADING)
    draw.text((155, 500 + left_slide),
              "Extracts tariff clauses from complex", fill=TEXT_SECONDARY, font=FONT_BODY)
    draw.text((155, 530 + left_slide),
              "40-page carrier contracts as verbatim", fill=TEXT_SECONDARY, font=FONT_BODY)
    draw.text((155, 560 + left_slide),
              "section quotes with PDF citations.", fill=TEXT_SECONDARY, font=FONT_BODY)

    draw.line([(155, 600 + left_slide), (825, 600 + left_slide)], fill=BORDER_SUBTLE, width=1)

    features_l = [
        ("Verbatim Citation", "Exact contract section quotes", SKY),
        ("k=3 Self-Consistency", "Multi-pass agreement check", SKY),
        ("Zero Arithmetic", "No math delegated to LLM", AMBER),
        ("GPU Accelerated", "AMD Instinct / Radeon ROCm", AMD_RED),
    ]
    fy = 620 + left_slide
    for i, (title, desc, dot_col) in enumerate(features_l):
        feat_t = ease_out_cubic(min(1.0, (lf - 12 - i * 4) / 15.0))
        if feat_t <= 0:
            continue
        fs = int((1.0 - feat_t) * 20)
        draw.ellipse([(155, fy + fs + 7), (167, fy + fs + 19)], fill=dot_col)
        draw.text((180, fy + fs), title, fill=TEXT_PRIMARY, font=FONT_BODY_BOLD)
        draw.text((180, fy + fs + 26), desc, fill=TEXT_MUTED, font=FONT_LABEL)
        fy += 62

    # --- CENTER: AIR-GAP BARRIER (animated) ---
    gap_pulse = 0.5 + 0.5 * math.sin(lf * 0.15)
    gap_col = lerp_color((40, 60, 100), (100, 140, 220), gap_pulse)
    gap_glow_col = lerp_color((30, 50, 120), (80, 130, 240), gap_pulse)

    # Vertical divider with glow
    glow_layer = Image.new('RGBA', (120, 500), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.rounded_rectangle([(30, 10), (90, 490)], radius=12,
                          fill=(gap_glow_col[0], gap_glow_col[1], gap_glow_col[2], 40))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=15))
    im.paste(glow_layer, (930, 400), glow_layer)

    draw.rounded_rectangle([(960, 420), (1010, 900)], radius=10,
                            fill=(15, 20, 35), outline=gap_col, width=2)

    # AIR-GAP text vertically
    gap_letters = "AIR-GAP"
    gy = 455
    for ch in gap_letters:
        draw.text((975, gy), ch, fill=gap_col, font=FONT_SUBHEADING)
        gy += 58

    # --- RIGHT CARD: Stage 2 (Deterministic Engine) ---
    right_t = ease_out_cubic(min(1.0, (lf - 10) / 20.0))
    right_slide = int((1.0 - right_t) * 40)

    draw_glow_rect(im, 1060, 380 + right_slide, 1800, 920 + right_slide,
                    EMERALD, glow_radius=18, intensity=int(35 * right_t))
    draw_shadow_card(im, draw, 1060, 380 + right_slide, 1800, 920 + right_slide,
                      BG_CARD, BORDER_CARD, radius=18)

    draw_pill_badge(draw, "STAGE 2", 1095, 405 + right_slide, EMERALD_BG, EMERALD, EMERALD, FONT_BADGE)
    draw.text((1195, 402 + right_slide), "DETERMINISTIC AUDITOR", fill=TEXT_MUTED, font=FONT_BADGE_LARGE)

    draw.text((1095, 450 + right_slide), "Pure Python Decimal", fill=TEXT_BRIGHT, font=FONT_HEADING)
    draw.text((1095, 500 + right_slide),
              "100% deterministic arithmetic against", fill=TEXT_SECONDARY, font=FONT_BODY)
    draw.text((1095, 530 + right_slide),
              "verified contract ground truth. Zero", fill=TEXT_SECONDARY, font=FONT_BODY)
    draw.text((1095, 560 + right_slide),
              "floating-point. Exact Decimal math.", fill=TEXT_SECONDARY, font=FONT_BODY)

    draw.line([(1095, 600 + right_slide), (1765, 600 + right_slide)], fill=BORDER_SUBTLE, width=1)

    features_r = [
        ("Exact Decimal Math", "$0.00 variance vs ground truth", EMERALD),
        ("Tariff Rule Auditing", "Base freight, fuel, detention", EMERALD),
        ("Three-Column Proof", "Invoice vs Contract vs Delta", SKY),
        ("Clerk Sign-Off", "Human-in-the-loop dispute export", VIOLET),
    ]
    fy = 620 + right_slide
    for i, (title, desc, dot_col) in enumerate(features_r):
        feat_t = ease_out_cubic(min(1.0, (lf - 14 - i * 4) / 15.0))
        if feat_t <= 0:
            continue
        fs = int((1.0 - feat_t) * 20)
        draw.ellipse([(1095, fy + fs + 7), (1107, fy + fs + 19)], fill=dot_col)
        draw.text((1120, fy + fs), title, fill=TEXT_PRIMARY, font=FONT_BODY_BOLD)
        draw.text((1120, fy + fs + 26), desc, fill=TEXT_MUTED, font=FONT_LABEL)
        fy += 62

    # Bottom bar
    draw.text((120, 960), "Architecture enforces strict boundary: language model extracts text, Python engine does all math.",
              fill=TEXT_DIM, font=FONT_LABEL)


# ============================================================================
# SCENE 3: THE PROOF - Audited Benchmark Results
# ============================================================================
def render_scene_3(im, draw, f):
    lf = f - SCENE_2_END
    t_in = ease_out_cubic(min(1.0, lf / 22.0))
    slide = int((1.0 - t_in) * 50)

    # Hero
    draw.text((120, 110 + slide), "Audited. Traceable. Exact.", fill=TEXT_BRIGHT, font=FONT_HERO)

    draw.text((120, 200 + slide),
              "Every overcharge backed by three-column proof: invoice, contract clause, and Decimal delta.",
              fill=TEXT_SECONDARY, font=FONT_BODY_LARGE)

    # === KPI STAT CARDS (4 columns with animated counters) ===
    counter_t = min(1.0, lf / 40.0)

    kpi_data = [
        ("INVOICES AUDITED", animated_counter(1250, counter_t), TEXT_BRIGHT, None, 120, 530),
        ("VERIFIED FINDINGS", animated_counter(284, counter_t), ROSE_LIGHT, ROSE, 530, 940),
        ("TOTAL RECOVERED", animated_counter(9130.51, counter_t, prefix="$", decimals=2), EMERALD_LIGHT, EMERALD, 940, 1430),
        ("MATH VARIANCE", "$0.00", SKY_LIGHT, SKY, 1430, 1800),
    ]

    for label, val, val_col, glow_col, x1, x2 in kpi_data:
        kpi_t = ease_out_cubic(min(1.0, (lf - 3) / 18.0))
        ks = int((1.0 - kpi_t) * 30)

        if glow_col:
            draw_glow_rect(im, x1, 270 + ks, x2, 385 + ks, glow_col,
                            glow_radius=14, intensity=int(30 * kpi_t))
        draw_shadow_card(im, draw, x1, 270 + ks, x2, 385 + ks,
                          BG_CARD_ELEVATED, BORDER_CARD, radius=14)
        draw.text((x1 + 25, 288 + ks), label, fill=TEXT_DIM, font=FONT_LABEL)
        draw.text((x1 + 25, 312 + ks), val, fill=val_col, font=FONT_STAT_VAL)

    # === MAIN 3-COLUMN PROOF TABLE ===
    proof_t = ease_out_cubic(min(1.0, (lf - 15) / 20.0))
    ps = int((1.0 - proof_t) * 40)

    draw_glow_rect(im, 120, 420 + ps, 1800, 920 + ps, EMERALD,
                    glow_radius=22, intensity=int(35 * proof_t))
    draw_shadow_card(im, draw, 120, 420 + ps, 1800, 920 + ps,
                      BG_CARD, BORDER_CARD, radius=18)

    # Table header
    draw.text((165, 445 + ps),
              "AUDIT FINDING #CB-284", fill=TEXT_MUTED, font=FONT_BADGE_LARGE)
    draw_pill_badge(draw, "EDI 210 LINE 412", 410, 442 + ps, (20, 30, 50), SKY, SKY_BG, FONT_BADGE)
    draw_pill_badge(draw, "CONFIDENCE: 100%", 1580, 442 + ps, EMERALD_BG, EMERALD, EMERALD, FONT_BADGE)
    draw.line([(120, 480 + ps), (1800, 480 + ps)], fill=BORDER_SUBTLE, width=1)

    # Column 1: Invoice Charge
    col1_t = ease_out_cubic(min(1.0, (lf - 20) / 18.0))
    if col1_t > 0:
        c1s = int((1.0 - col1_t) * 25)
        draw_card(draw, 150, 500 + ps + c1s, 640, 880 + ps + c1s,
                  BG_CARD_ELEVATED, BORDER_SUBTLE, radius=14)
        draw.text((180, 518 + ps + c1s), "BILLED CHARGE", fill=TEXT_DIM, font=FONT_BADGE_LARGE)
        draw.text((180, 555 + ps + c1s), "$2,450.00", fill=TEXT_BRIGHT, font=FONT_STAT_HUGE)
        draw.line([(180, 635 + ps + c1s), (610, 635 + ps + c1s)], fill=BORDER_SUBTLE, width=1)
        draw.text((180, 655 + ps + c1s), "Carrier: Midwestern Freight Inc.", fill=TEXT_SECONDARY, font=FONT_BODY)
        draw.text((180, 690 + ps + c1s), "Rate: $2.15 / cwt", fill=TEXT_MUTED, font=FONT_BODY)
        draw.text((180, 720 + ps + c1s), "Weight: 12,450 lbs", fill=TEXT_MUTED, font=FONT_BODY)
        draw.text((180, 750 + ps + c1s), "Chicago, IL → Dallas, TX", fill=TEXT_MUTED, font=FONT_BODY)

        # Status badge
        draw_pill_badge(draw, "OVERCHARGE FLAGGED", 180, 800 + ps + c1s, ROSE_BG, ROSE, ROSE, FONT_BADGE)

    # Column 2: Contract Ground Truth
    col2_t = ease_out_cubic(min(1.0, (lf - 25) / 18.0))
    if col2_t > 0:
        c2s = int((1.0 - col2_t) * 25)
        draw_card(draw, 670, 500 + ps + c2s, 1230, 880 + ps + c2s,
                  BG_CARD_ELEVATED, BORDER_SUBTLE, radius=14)
        draw.text((700, 518 + ps + c2s), "CONTRACT CLAUSE", fill=SKY, font=FONT_BADGE_LARGE)
        draw.text((700, 555 + ps + c2s), "$2,127.50", fill=SKY_LIGHT, font=FONT_STAT_HUGE)
        draw.line([(700, 635 + ps + c2s), (1200, 635 + ps + c2s)], fill=BORDER_SUBTLE, width=1)
        draw.text((700, 655 + ps + c2s), "Section 4.2.1 (LTL Schedule B)", fill=TEXT_SECONDARY, font=FONT_BODY)
        draw.text((700, 690 + ps + c2s), "Rate: $1.85/cwt (14% discount)", fill=TEXT_BRIGHT, font=FONT_BODY)
        draw.text((700, 720 + ps + c2s), "Gemma extracted quote:", fill=TEXT_DIM, font=FONT_BODY)

        # Quoted text with cursor
        quote = '"Carrier shall bill Class 70'
        chars = int(len(quote) * min(1.0, (lf - 30) / 25.0))
        draw.text((700, 752 + ps + c2s), quote[:chars], fill=TEXT_BRIGHT, font=FONT_MONO)
        quote2 = 'at $1.85/cwt on lanes > 800mi"'
        chars2 = int(len(quote2) * min(1.0, (lf - 40) / 25.0))
        if chars2 > 0:
            draw.text((700, 778 + ps + c2s), quote2[:chars2], fill=TEXT_BRIGHT, font=FONT_MONO)

        draw_pill_badge(draw, "PDF p.14 §4.2.1", 700, 820 + ps + c2s, SKY_BG, SKY, SKY_BG, FONT_BADGE)

    # Column 3: Mathematical Proof (with glow)
    col3_t = ease_out_cubic(min(1.0, (lf - 30) / 18.0))
    if col3_t > 0:
        c3s = int((1.0 - col3_t) * 25)
        glow_pulse = 0.5 + 0.5 * math.sin(lf * 0.15)
        draw_glow_rect(im, 1260, 500 + ps + c3s, 1770, 880 + ps + c3s,
                        EMERALD, glow_radius=16, intensity=int(50 + 30 * glow_pulse))
        draw_card(draw, 1260, 500 + ps + c3s, 1770, 880 + ps + c3s,
                  (12, 30, 26), EMERALD, radius=14, width=2)
        draw.text((1290, 518 + ps + c3s), "MATHEMATICAL PROOF", fill=EMERALD_LIGHT, font=FONT_BADGE_LARGE)
        draw.text((1290, 555 + ps + c3s), "+$322.50", fill=EMERALD_LIGHT, font=FONT_STAT_HUGE)
        draw.line([(1290, 635 + ps + c3s), (1740, 635 + ps + c3s)], fill=(20, 60, 50), width=1)
        draw.text((1290, 655 + ps + c3s), "Pure Python Decimal:", fill=TEXT_SECONDARY, font=FONT_BODY)
        draw.text((1290, 690 + ps + c3s), "$2.15 - $1.85 = $0.30/cwt", fill=TEXT_BRIGHT, font=FONT_MONO)
        draw.text((1290, 725 + ps + c3s), "$0.30 × 124.5 = $37.35", fill=TEXT_BRIGHT, font=FONT_MONO)
        draw.text((1290, 760 + ps + c3s), "+ Fuel credit = $285.15", fill=TEXT_BRIGHT, font=FONT_MONO)

        draw_pill_badge(draw, "100% VERIFIED", 1290, 810 + ps + c3s, EMERALD_BG, EMERALD, EMERALD, FONT_BADGE)

    # Bottom
    draw.text((120, 960), "100% deterministic: full audit trail from invoice to contract clause to exact refund.",
              fill=TEXT_DIM, font=FONT_LABEL)


# ============================================================================
# SCENE 4: THE OUTRO - Recover & Ship
# ============================================================================
def render_scene_4(im, draw, f):
    lf = f - SCENE_3_END
    t_in = ease_out_cubic(min(1.0, lf / 22.0))
    slide = int((1.0 - t_in) * 50)

    # Massive hero text
    draw.text((120, 100 + slide), "Protect margin", fill=TEXT_BRIGHT, font=FONT_HERO_LARGE)
    draw.text((120, 205 + slide), "from the cost side.", fill=EMERALD_LIGHT, font=FONT_HERO_LARGE)

    # Recovery summary card
    card_t = ease_out_cubic(min(1.0, (lf - 8) / 20.0))
    cs = int((1.0 - card_t) * 40)

    draw_glow_rect(im, 120, 340 + cs, 960, 780 + cs, EMERALD,
                    glow_radius=22, intensity=int(40 * card_t))
    draw_shadow_card(im, draw, 120, 340 + cs, 960, 780 + cs,
                      BG_CARD, BORDER_CARD, radius=18)

    draw_pill_badge(draw, "DISPUTE PACKAGE READY", 165, 370 + cs,
                    EMERALD_BG, EMERALD, EMERALD, FONT_BADGE_LARGE)

    items = [
        ("Recovery Amount", "$9,130.51 across 284 findings", EMERALD_LIGHT),
        ("Invoices Audited", "1,250 freight bill lines", TEXT_BRIGHT),
        ("Arithmetic Proof", "100% Python Decimal ($0.00 drift)", SKY_LIGHT),
        ("Export Formats", "PDF, EDI 210, CSV Ledger", TEXT_BRIGHT),
        ("Human Review", "Clerk sign-off verification", AMBER),
    ]
    iy = 420 + cs
    for i, (label, val, col) in enumerate(items):
        item_t = ease_out_cubic(min(1.0, (lf - 12 - i * 3) / 15.0))
        if item_t <= 0:
            continue
        item_s = int((1.0 - item_t) * 15)
        draw.text((165, iy + item_s), label, fill=TEXT_MUTED, font=FONT_BODY)
        draw.text((410, iy + item_s), val, fill=col, font=FONT_BODY_BOLD)
        iy += 52

    # Progress bar for "recovery processing"
    bar_progress = ease_out_expo(min(1.0, (lf - 20) / 30.0))
    draw_progress_bar(draw, 165, 720 + cs, 760, 14, bar_progress,
                       (20, 30, 45), EMERALD, radius=7)
    pct_text = f"{int(bar_progress * 100)}% dispute package compiled"
    draw.text((165, 742 + cs), pct_text, fill=TEXT_MUTED, font=FONT_LABEL)

    # Right card: Hackathon & Tech Stack
    right_t = ease_out_cubic(min(1.0, (lf - 12) / 20.0))
    rs = int((1.0 - right_t) * 40)

    draw_glow_rect(im, 1000, 340 + rs, 1800, 780 + rs, AMD_RED,
                    glow_radius=18, intensity=int(30 * right_t))
    draw_shadow_card(im, draw, 1000, 340 + rs, 1800, 780 + rs,
                      BG_CARD, BORDER_CARD, radius=18)

    draw_pill_badge(draw, "AMD HACKATHON: ACT III", 1045, 370 + rs,
                    (50, 10, 15), AMD_RED, AMD_RED, FONT_BADGE_LARGE)

    draw.text((1045, 420 + rs), "Track 3:", fill=TEXT_MUTED, font=FONT_BODY_BOLD)
    draw.text((1145, 420 + rs), "Reinvent Commerce", fill=TEXT_BRIGHT, font=FONT_BODY_BOLD)

    draw.line([(1045, 460 + rs), (1760, 460 + rs)], fill=BORDER_SUBTLE, width=1)

    techs = [
        ("AMD ROCm", "GPU acceleration & PyTorch", AMD_RED),
        ("Gemma 27B / 9B", "Contract clause extraction", VIOLET),
        ("Python Decimal", "Deterministic rules engine", EMERALD),
        ("React + FastAPI", "Full-stack audit platform", SKY),
    ]
    ty = 480 + rs
    for i, (name, desc, dot_col) in enumerate(techs):
        tech_t = ease_out_cubic(min(1.0, (lf - 16 - i * 3) / 15.0))
        if tech_t <= 0:
            continue
        ts = int((1.0 - tech_t) * 15)
        draw.ellipse([(1045, ty + ts + 7), (1057, ty + ts + 19)], fill=dot_col)
        draw.text((1070, ty + ts), name, fill=TEXT_BRIGHT, font=FONT_BODY_BOLD)
        draw.text((1070, ty + ts + 26), desc, fill=TEXT_MUTED, font=FONT_LABEL)
        ty += 56

    # Repo URL
    draw.text((1045, 720 + rs), "github.com/Abdullahs-git/clawback", fill=SKY, font=FONT_MONO_BOLD)

    # Bottom tagline
    draw.text((120, 960), "CLAWBACK  ·  Deterministic Carrier Freight Contract Audit Engine  ·  Open Source · Apache 2.0",
              fill=TEXT_DIM, font=FONT_LABEL)


# ============================================================================
# MAIN RENDERER
# ============================================================================
def render_single_frame(f):
    # Create rich gradient background
    im = create_gradient_bg(WIDTH, HEIGHT, f)
    draw = ImageDraw.Draw(im)

    # Top bar (always present)
    draw_top_bar(im, draw, f)

    # Determine which scene(s) to render (with crossfade transitions)
    def dip_through_black(scene_a_fn, scene_b_fn, t_fade, f):
        """Dip-to-black transition: scene A fades out, then scene B fades in."""
        black = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
        if t_fade < 0.5:
            # First half: scene A fades to black
            opacity = 1.0 - (t_fade * 2.0)  # 1.0 → 0.0
            scene_im = create_gradient_bg(WIDTH, HEIGHT, f)
            scene_draw = ImageDraw.Draw(scene_im)
            draw_top_bar(scene_im, scene_draw, f)
            scene_a_fn(scene_im, scene_draw, f)
            return Image.blend(black, scene_im.convert('RGB'), opacity).convert('RGBA')
        else:
            # Second half: scene B fades from black
            opacity = (t_fade - 0.5) * 2.0  # 0.0 → 1.0
            scene_im = create_gradient_bg(WIDTH, HEIGHT, f)
            scene_draw = ImageDraw.Draw(scene_im)
            draw_top_bar(scene_im, scene_draw, f)
            scene_b_fn(scene_im, scene_draw, f)
            return Image.blend(black, scene_im.convert('RGB'), opacity).convert('RGBA')

    if f < SCENE_1_END - TRANSITION_FRAMES:
        # Pure Scene 1
        render_scene_1(im, draw, f)
    elif f < SCENE_1_END:
        # Dip-to-black: Scene 1 → Scene 2
        t_fade = (f - (SCENE_1_END - TRANSITION_FRAMES)) / TRANSITION_FRAMES
        im = dip_through_black(render_scene_1, render_scene_2, ease_in_out_cubic(t_fade), f)

    elif f < SCENE_2_END - TRANSITION_FRAMES:
        render_scene_2(im, draw, f)
    elif f < SCENE_2_END:
        t_fade = (f - (SCENE_2_END - TRANSITION_FRAMES)) / TRANSITION_FRAMES
        im = dip_through_black(render_scene_2, render_scene_3, ease_in_out_cubic(t_fade), f)

    elif f < SCENE_3_END - TRANSITION_FRAMES:
        render_scene_3(im, draw, f)
    elif f < SCENE_3_END:
        t_fade = (f - (SCENE_3_END - TRANSITION_FRAMES)) / TRANSITION_FRAMES
        im = dip_through_black(render_scene_3, render_scene_4, ease_in_out_cubic(t_fade), f)

    else:
        render_scene_4(im, draw, f)

    # Save frame
    out_path = os.path.join("brag-output", "work", f"frame_{f:04d}.png")
    im.convert('RGB').save(out_path)

    return f


def render_poster():
    """Render a dedicated hero poster frame (not just a video still)."""
    im = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))

    # Rich gradient
    draw = ImageDraw.Draw(im)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(lerp(8, 16, t))
        g = int(lerp(10, 22, t))
        b = int(lerp(18, 38, t))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    im = im.convert('RGBA')

    # Central emerald spotlight
    spot = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spot)
    for radius in range(600, 0, -2):
        alpha = int(20 * (radius / 600.0))
        sd.ellipse([(960 - radius, 400 - radius), (960 + radius, 400 + radius)],
                    fill=(16, 100, 75, alpha))
    im = Image.alpha_composite(im, spot)

    draw = ImageDraw.Draw(im)

    # Top bar
    draw.line([(0, 78), (WIDTH, 78)], fill=BORDER_SUBTLE, width=1)
    draw.rounded_rectangle([(78, 20), (118, 60)], radius=10, fill=AMD_RED)
    draw.text((88, 22), "C", fill=TEXT_BRIGHT, font=FONT_HEADING)
    draw.text((130, 24), "CLAWBACK", fill=TEXT_BRIGHT, font=FONT_HEADING)
    draw_glow_circle(im, 1636, 40, 5, EMERALD, glow_radius=8, intensity=120)
    draw = ImageDraw.Draw(im)
    draw.ellipse([(1631, 35), (1641, 45)], fill=EMERALD_LIGHT)
    draw.text((1652, 28), "AMD ROCm", fill=EMERALD_LIGHT, font=FONT_BODY_BOLD)

    # Hero text
    draw.text((120, 130), "Deterministic Freight", fill=TEXT_BRIGHT, font=FONT_HERO_LARGE)
    draw.text((120, 235), "Contract Audit Engine", fill=EMERALD_LIGHT, font=FONT_HERO_LARGE)

    draw.text((120, 350), "AI extracts contract clauses.  Python Decimal audits the math.  Humans approve the claims.",
              fill=TEXT_SECONDARY, font=FONT_BODY_LARGE)

    # Giant stat cards
    stats = [
        ("RECOVERED", "$9,130.51", EMERALD_LIGHT, EMERALD, 120, 550),
        ("FINDINGS", "284", ROSE_LIGHT, ROSE, 550, 880),
        ("INVOICES", "1,250", TEXT_BRIGHT, None, 880, 1210),
        ("VARIANCE", "$0.00", SKY_LIGHT, SKY, 1210, 1540),
    ]
    for lbl, val, vc, gc, x1, x2 in stats:
        if gc:
            draw_glow_rect(im, x1, 430, x2, 560, gc, glow_radius=16, intensity=50)
        draw = ImageDraw.Draw(im)
        draw_shadow_card(im, draw, x1, 430, x2, 560, BG_CARD_ELEVATED, BORDER_CARD, radius=14)
        draw.text((x1 + 25, 448), lbl, fill=TEXT_DIM, font=FONT_LABEL)
        draw.text((x1 + 25, 475), val, fill=vc, font=FONT_STAT_VAL)

    # Architecture badges
    draw_pill_badge(draw, "AMD ROCm GPU", 1570, 450, (50, 10, 15), AMD_RED, AMD_RED, FONT_BADGE_LARGE)
    draw_pill_badge(draw, "Gemma LLM", 1570, 490, (30, 20, 60), VIOLET, VIOLET, FONT_BADGE_LARGE)
    draw_pill_badge(draw, "Python Decimal", 1570, 530, EMERALD_BG, EMERALD, EMERALD, FONT_BADGE_LARGE)

    # 3-column proof preview
    draw_glow_rect(im, 120, 600, 1800, 880, EMERALD, glow_radius=20, intensity=35)
    draw = ImageDraw.Draw(im)
    draw_shadow_card(im, draw, 120, 600, 1800, 880, BG_CARD, BORDER_CARD, radius=18)
    draw.text((165, 625), "THREE-COLUMN TRACEABLE PROOF", fill=TEXT_MUTED, font=FONT_BADGE_LARGE)
    draw_pill_badge(draw, "CONFIDENCE: 100%", 1580, 620, EMERALD_BG, EMERALD, EMERALD, FONT_BADGE)
    draw.line([(120, 660), (1800, 660)], fill=BORDER_SUBTLE, width=1)

    # Col 1
    draw_card(draw, 150, 680, 620, 850, BG_CARD_ELEVATED, BORDER_SUBTLE, radius=12)
    draw.text((180, 698), "BILLED CHARGE", fill=TEXT_DIM, font=FONT_BADGE_LARGE)
    draw.text((180, 730), "$2,450.00", fill=TEXT_BRIGHT, font=FONT_STAT_VAL)
    draw.text((180, 790), "Midwestern Freight · $2.15/cwt", fill=TEXT_MUTED, font=FONT_BODY)

    # Col 2
    draw_card(draw, 650, 680, 1190, 850, BG_CARD_ELEVATED, BORDER_SUBTLE, radius=12)
    draw.text((680, 698), "CONTRACT CLAUSE", fill=SKY, font=FONT_BADGE_LARGE)
    draw.text((680, 730), "$2,127.50", fill=SKY_LIGHT, font=FONT_STAT_VAL)
    draw.text((680, 790), "§4.2.1 · Rate: $1.85/cwt", fill=TEXT_MUTED, font=FONT_BODY)

    # Col 3
    draw_card(draw, 1220, 680, 1770, 850, (12, 30, 26), EMERALD, radius=12, width=2)
    draw.text((1250, 698), "MATHEMATICAL PROOF", fill=EMERALD_LIGHT, font=FONT_BADGE_LARGE)
    draw.text((1250, 730), "+$322.50", fill=EMERALD_LIGHT, font=FONT_STAT_VAL)
    draw_pill_badge(draw, "100% VERIFIED", 1250, 800, EMERALD_BG, EMERALD, EMERALD, FONT_BADGE)

    # Bottom
    draw_pill_badge(draw, "AMD DEVELOPER HACKATHON: ACT III  ·  TRACK 3: REINVENT COMMERCE", 120, 920,
                    (20, 10, 15), AMD_RED, AMD_RED, FONT_BADGE_LARGE)
    draw.text((120, 970), "github.com/Abdullahs-git/clawback", fill=SKY, font=FONT_MONO_BOLD)
    draw.text((700, 970), "Open Source  ·  Apache 2.0", fill=TEXT_DIM, font=FONT_BODY)

    im.convert('RGB').save(os.path.join("brag-output", "brag.jpg"), quality=95)
    print("Poster rendered: brag-output/brag.jpg")


def main():
    os.makedirs(os.path.join("brag-output", "work"), exist_ok=True)

    # Render poster first
    render_poster()

    # Render all video frames
    t0 = time.time()
    num_workers = min(cpu_count(), 4)
    print(f"Rendering {TOTAL_FRAMES} frames using {num_workers} workers...")

    with Pool(num_workers) as pool:
        done = 0
        for idx in pool.imap_unordered(render_single_frame, range(TOTAL_FRAMES), chunksize=8):
            done += 1
            if done % 50 == 0 or done == TOTAL_FRAMES:
                elapsed = time.time() - t0
                fps = done / elapsed
                eta = (TOTAL_FRAMES - done) / fps if fps > 0 else 0
                print(f"  [{done:3d}/{TOTAL_FRAMES}] {elapsed:.1f}s elapsed, {fps:.1f} fps, ETA {eta:.0f}s")

    print(f"All {TOTAL_FRAMES} frames rendered in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
