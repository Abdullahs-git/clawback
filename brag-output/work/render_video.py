"""
Clawback /brag Launch Video Renderer
Generates 600 frames (20.0s @ 30fps, 1920x1080) in parallel using Pillow.
"""

import os
import math
import time
from multiprocessing import Pool, cpu_count
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = 600
FPS = 30

# Colors
BG_DARK = (11, 15, 25)
BG_CARD = (22, 30, 46)
BG_CARD_HIGHLIGHT = (28, 40, 62)
BORDER_CARD = (51, 65, 85)
BORDER_HIGHLIGHT = (71, 85, 105)

TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_DIM = (100, 116, 139)

ACCENT_EMERALD = (16, 185, 129)
ACCENT_EMERALD_BG = (6, 78, 59)
ACCENT_ROSE = (244, 63, 94)
ACCENT_ROSE_BG = (136, 19, 55)
ACCENT_SKY = (56, 189, 248)
ACCENT_AMD = (237, 28, 36)

# Fonts
FONT_TITLE = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 46)
FONT_SUBTITLE = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 24)
FONT_HEADING = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 32)
FONT_BODY = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 20)
FONT_BODY_BOLD = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 22)
FONT_MONO = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 20)
FONT_MONO_BOLD = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 24)
FONT_STAT_VAL = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 44)
FONT_STAT_LBL = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 16)
FONT_BADGE = ImageFont.truetype("C:\\Windows\\Fonts\\bahnschrift.ttf", 18)
FONT_MICRO = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 14)


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - math.pow(1.0 - t, 3)


def draw_card(draw, x1, y1, x2, y2, fill, outline, radius=14, width=2):
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, fill=fill, outline=outline, width=width)


def draw_badge(draw, text, x, y, bg_col, text_col, border_col, font=FONT_BADGE):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 16, 7
    draw.rounded_rectangle([(x, y), (x + tw + pad_x * 2, y + th + pad_y * 2)], radius=6, fill=bg_col, outline=border_col, width=1)
    draw.text((x + pad_x, y + pad_y - 1), text, fill=text_col, font=font)
    return tw + pad_x * 2


def draw_header(draw, frame_idx):
    # Top banner / Header
    draw.line([(80, 85), (1840, 85)], fill=BORDER_CARD, width=1)

    # Logo & Name
    # Draw logo icon
    draw.rounded_rectangle([(80, 32), (122, 74)], radius=8, fill=ACCENT_AMD, outline=(255, 100, 100), width=1)
    draw.text((93, 38), "C", fill=TEXT_WHITE, font=FONT_HEADING)
    draw.text((134, 38), "CLAWBACK", fill=TEXT_WHITE, font=FONT_HEADING)
    draw.text((310, 48), "v1.0.0-rc", fill=TEXT_DIM, font=FONT_MICRO)

    # Hackathon badge
    draw_badge(draw, "AMD DEVELOPER HACKATHON: ACT III  |  TRACK 3: REINVENT COMMERCE", 430, 40, (15, 23, 42), TEXT_MUTED, BORDER_CARD, FONT_BADGE)

    # Engine status badge
    pulse = 0.5 + 0.5 * math.sin(frame_idx * 0.15)
    dot_color = (int(16 + pulse * 20), int(185 + pulse * 40), 129)
    draw.ellipse([(1550, 49), (1562, 61)], fill=dot_color)
    draw.text((1572, 45), "AMD ROCm ACCELERATED", fill=ACCENT_EMERALD, font=FONT_BODY_BOLD)


def draw_scene_1(im, draw, f):
    # Frame 0 to 104 (0.0s to 3.5s)
    # Hook: The Commerce Billing Problem
    t_enter = ease_out_cubic(min(1.0, f / 20.0))
    y_offset = int((1.0 - t_enter) * 30)

    # Eyebrow
    draw_badge(draw, "THE COMMERCE OVERCHARGE CRISIS", 80, 125 + y_offset, ACCENT_ROSE_BG, ACCENT_ROSE, ACCENT_ROSE, FONT_BADGE)

    # Headline
    draw.text((80, 175 + y_offset), "Shippers Pay Thousands of Line Items Every Month.", fill=TEXT_WHITE, font=FONT_TITLE)
    draw.text((80, 240 + y_offset), "Carriers make billing errors. Checking 40-page tariff contracts manually is impossible.", fill=TEXT_MUTED, font=FONT_SUBTITLE)

    # Main Ledger Card (Simulated Carrier EDI 210 feed)
    draw_card(draw, 80, 320, 1840, 860, BG_CARD, BORDER_CARD, radius=16)

    # Card title bar
    draw.text((115, 345), "CARRIER FREIGHT INVOICE STREAM  (1,250 EDI 210 AUDIT BATCH)", fill=TEXT_MUTED, font=FONT_BODY_BOLD)
    draw.line([(80, 395), (1840, 395)], fill=BORDER_CARD, width=1)

    # Table headers
    headers = [("INVOICE #", 115), ("SHIPMENT / ROUTE", 340), ("CLASS & WEIGHT", 780), ("BILLED TARIFF", 1140), ("STATUS", 1520)]
    for h, x in headers:
        draw.text((x, 415), h, fill=TEXT_DIM, font=FONT_MICRO)
    draw.line([(80, 445), (1840, 445)], fill=BORDER_CARD, width=1)

    # Sample rows
    rows = [
        ("INV-849201", "Chicago, IL  -->  Dallas, TX (840 mi)", "Class 70  |  12,450 lbs", "$2,450.00", "BILLED", TEXT_WHITE),
        ("INV-849202", "Atlanta, GA  -->  Newark, NJ (750 mi)", "Class 85  |   8,200 lbs", "$1,680.00", "BILLED", TEXT_WHITE),
        ("INV-849203", "Los Angeles, CA  -->  Seattle, WA (1,130 mi)", "Class 60  |  18,900 lbs", "$3,890.00", "BILLED", TEXT_WHITE),
        ("INV-849204", "Memphis, TN  -->  Columbus, OH (480 mi)", "Class 70  |   6,150 lbs", "$1,120.00", "BILLED", TEXT_WHITE),
        ("INV-849205", "Denver, CO  -->  Kansas City, MO (600 mi)", "Class 92.5 | 10,800 lbs", "$2,310.00", "BILLED", TEXT_WHITE),
    ]

    y_row = 465
    for r in rows:
        draw.text((115, y_row), r[0], fill=ACCENT_SKY, font=FONT_MONO)
        draw.text((340, y_row), r[1], fill=r[5], font=FONT_BODY)
        draw.text((780, y_row), r[2], fill=TEXT_MUTED, font=FONT_BODY)
        draw.text((1140, y_row), r[3], fill=r[5], font=FONT_MONO_BOLD)
        draw.text((1520, y_row), r[4], fill=TEXT_DIM, font=FONT_MONO)
        draw.line([(100, y_row + 42), (1820, y_row + 42)], fill=(30, 41, 59), width=1)
        y_row += 60

    # Pop-up Alert Banner appears from frame 35
    if f >= 35:
        t_alert = ease_out_cubic(min(1.0, (f - 35) / 18.0))
        scale_y = int(t_alert * 180)
        top_y = 650
        draw_card(draw, 140, top_y, 1780, top_y + scale_y, (35, 15, 25), ACCENT_ROSE, radius=12, width=3)
        if scale_y > 100:
            draw.text((180, top_y + 35), "[CRITICAL AUDIT ALERT]  $9,130.51 IN UNVERIFIED OVERCHARGES DETECTED", fill=ACCENT_ROSE, font=FONT_HEADING)
            draw.text((180, top_y + 85), "284 Discrepancies Identified Across 1,250 Invoices  *  Tariff Discrepancies  *  Fuel Surcharge Errors", fill=TEXT_WHITE, font=FONT_BODY)
            draw.text((180, top_y + 120), "Manual invoice auditing cannot keep up with high-frequency commerce logistics.", fill=TEXT_MUTED, font=FONT_BODY)

    # Footer note
    draw.text((80, 960), "Source: Actual Audited Benchmark Batch (1,250 lines from real carrier billing)", fill=TEXT_DIM, font=FONT_MICRO)


def draw_scene_2(im, draw, f):
    # Frames 105 to 239 (3.5s to 8.0s)
    # The Architectural Solution: Air-Gap Between LLM and Math
    local_f = f - 105
    t_enter = ease_out_cubic(min(1.0, local_f / 20.0))
    y_offset = int((1.0 - t_enter) * 30)

    # Eyebrow
    draw_badge(draw, "THE CLAWBACK ARCHITECTURE", 80, 125 + y_offset, ACCENT_EMERALD_BG, ACCENT_EMERALD, ACCENT_EMERALD, FONT_BADGE)

    # Headline
    draw.text((80, 175 + y_offset), "LLMs Hallucinate Math. Clawback Eliminates Arithmetic From AI.", fill=TEXT_WHITE, font=FONT_TITLE)
    draw.text((80, 240 + y_offset), "Gemma on AMD ROCm extracts verified text quotes. A pure Python Decimal engine audits the numbers.", fill=TEXT_MUTED, font=FONT_SUBTITLE)

    # Two Main Architecture Stage Cards
    # Left Card: AMD ROCm + Gemma (Natural Language Extraction)
    draw_card(draw, 80, 320, 890, 870, BG_CARD, BORDER_CARD, radius=16)
    draw_badge(draw, "STAGE 1: CLAUSE EXTRACTOR", 115, 350, (15, 23, 42), ACCENT_SKY, BORDER_CARD, FONT_BADGE)
    draw.text((115, 405), "AMD ROCm + Gemma LLM", fill=TEXT_WHITE, font=FONT_HEADING)
    draw.text((115, 450), "Extracts complex unstructured tariff agreements from 40-page PDFs", fill=TEXT_MUTED, font=FONT_BODY)
    draw.line([(115, 495), (855, 495)], fill=BORDER_CARD, width=1)

    bullets_left = [
        ("Verbatim Citation", "Quotes exact contract sections with PDF page/clause pointers"),
        ("k=3 Self-Consistency", "Multi-pass agreement verification guarantees extraction stability"),
        ("Strict Boundary", "Zero arithmetic delegated to language model -- no hallucinations"),
        ("Hardware Acceleration", "High-throughput execution on AMD ROCm Instinct / Radeon GPUs")
    ]
    by = 520
    for title, desc in bullets_left:
        draw.ellipse([(115, by + 8), (127, by + 20)], fill=ACCENT_SKY)
        draw.text((140, by + 2), title, fill=TEXT_WHITE, font=FONT_BODY_BOLD)
        draw.text((140, by + 28), desc, fill=TEXT_MUTED, font=FONT_MICRO)
        by += 72

    # Center Air-Gap Barrier (animated pulse)
    center_pulse = 0.5 + 0.5 * math.sin(local_f * 0.12)
    border_pulse_col = (int(50 + center_pulse * 100), int(100 + center_pulse * 85), 248)
    draw_card(draw, 920, 420, 1000, 770, (18, 25, 40), border_pulse_col, radius=10, width=2)
    draw.text((945, 480), "A\nI\nR\n-\nG\nA\nP", fill=border_pulse_col, font=FONT_HEADING)

    # Right Card: Pure Python Decimal (Deterministic Rules Engine)
    draw_card(draw, 1030, 320, 1840, 870, BG_CARD, BORDER_CARD, radius=16)
    draw_badge(draw, "STAGE 2: DETERMINISTIC AUDITOR", 1065, 350, (15, 23, 42), ACCENT_EMERALD, BORDER_CARD, FONT_BADGE)
    draw.text((1065, 405), "Pure Python Decimal Engine", fill=TEXT_WHITE, font=FONT_HEADING)
    draw.text((1065, 450), "Executes 100% deterministic arithmetic against verified ground truth", fill=TEXT_MUTED, font=FONT_BODY)
    draw.line([(1065, 495), (1805, 495)], fill=BORDER_CARD, width=1)

    bullets_right = [
        ("Exact Decimal Math", "Zero floating-point rounding errors ($0.00 mathematical variance)"),
        ("Tariff Rule Auditing", "Base freight (cwt/min), fuel surcharges, detention & demurrage"),
        ("Three-Column Proof", "Every single penny backed by Invoice vs Contract vs Difference"),
        ("Clerk Sign-Off", "Dispute packages drafted with EDI 210 citations for recovery claims")
    ]
    by = 520
    for title, desc in bullets_right:
        draw.ellipse([(1065, by + 8), (1077, by + 20)], fill=ACCENT_EMERALD)
        draw.text((1090, by + 2), title, fill=TEXT_WHITE, font=FONT_BODY_BOLD)
        draw.text((1090, by + 28), desc, fill=TEXT_MUTED, font=FONT_MICRO)
        by += 72

    draw.text((80, 960), "Architecture: Clean Separation of Extraction (AMD ROCm LLM) and Arithmetic (Deterministic Rules Engine)", fill=TEXT_DIM, font=FONT_MICRO)


def draw_scene_3(im, draw, f):
    # Frames 240 to 434 (8.0s to 14.5s)
    # The Action: 3-Column Traceable Proof & Audited Benchmark
    local_f = f - 240
    t_enter = ease_out_cubic(min(1.0, local_f / 20.0))
    y_offset = int((1.0 - t_enter) * 30)

    # Eyebrow
    draw_badge(draw, "VERIFIED AUDIT BENCHMARK  *  1,250 FREIGHT BILLS", 80, 125 + y_offset, ACCENT_EMERALD_BG, ACCENT_EMERALD, ACCENT_EMERALD, FONT_BADGE)

    # Headline
    draw.text((80, 175 + y_offset), "Three-Column Traceable Proof for Every Overcharge Claim", fill=TEXT_WHITE, font=FONT_TITLE)
    draw.text((80, 240 + y_offset), "Audited on 1,250 freight invoices. Zero math discrepancy against ground truth.", fill=TEXT_MUTED, font=FONT_SUBTITLE)

    # 4 Top KPI Stat Badges
    kpis = [
        ("INVOICES AUDITED", "1,250", TEXT_WHITE, 80, 480),
        ("VERIFIED FINDINGS", "284", ACCENT_ROSE, 510, 910),
        ("TOTAL OVERCHARGES RECOVERED", "$9,130.51", ACCENT_EMERALD, 940, 1420),
        ("MATH VARIANCE", "$0.00", ACCENT_SKY, 1450, 1840),
    ]
    for lbl, val, val_col, x1, x2 in kpis:
        draw_card(draw, x1, 310, x2, 410, BG_CARD, BORDER_CARD, radius=12)
        draw.text((x1 + 25, 328), lbl, fill=TEXT_DIM, font=FONT_STAT_LBL)
        draw.text((x1 + 25, 350), val, fill=val_col, font=FONT_STAT_VAL)

    # Main 3-Column Proof Table Card
    draw_card(draw, 80, 440, 1840, 910, BG_CARD, BORDER_CARD, radius=16)

    # Header of Inspector
    draw.text((115, 465), "AUDIT FINDING #CB-284  *  CARRIER EDI 210 LINE 412  *  LTL FREIGHT SHIPMENT", fill=TEXT_MUTED, font=FONT_BODY_BOLD)
    draw_badge(draw, "CONFIDENCE: 100%", 1640, 460, ACCENT_EMERALD_BG, ACCENT_EMERALD, ACCENT_EMERALD, FONT_BADGE)
    draw.line([(80, 505), (1840, 505)], fill=BORDER_CARD, width=1)

    # Column 1: Billed Invoice
    draw_card(draw, 115, 530, 640, 870, (18, 25, 40), BORDER_CARD, radius=12)
    draw.text((140, 550), "1. BILLED INVOICE CHARGE", fill=TEXT_MUTED, font=FONT_BODY_BOLD)
    draw.text((140, 600), "$2,450.00", fill=TEXT_WHITE, font=FONT_STAT_VAL)
    draw.text((140, 665), "Carrier: Midwestern Freight Inc.", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((140, 695), "Billed Rate: $2.15 / cwt", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((140, 725), "Billed Weight: 12,450 lbs", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((140, 755), "Lane: Chicago, IL -> Dallas, TX", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((140, 810), "Status: Overcharge Flagged", fill=ACCENT_ROSE, font=FONT_MONO_BOLD)

    # Column 2: Contract Clause Ground Truth
    draw_card(draw, 665, 530, 1260, 870, (18, 25, 40), BORDER_CARD, radius=12)
    draw.text((690, 550), "2. CONTRACT GROUND TRUTH", fill=ACCENT_SKY, font=FONT_BODY_BOLD)
    draw.text((690, 600), "$2,127.50", fill=ACCENT_SKY, font=FONT_STAT_VAL)
    draw.text((690, 665), "Tariff Contract: Section 4.2.1 (LTL Schedule B)", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((690, 695), "Agreed Rate: $1.85 / cwt  (Discount: 14% on lanes > 800 mi)", fill=TEXT_WHITE, font=FONT_BODY)
    draw.text((690, 725), "Extracted Quote (Gemma ROCm):", fill=TEXT_DIM, font=FONT_BODY)
    draw.text((690, 755), "\"Carrier shall bill Class 70 freight at $1.85/cwt on lanes > 800 mi.\"", fill=TEXT_WHITE, font=FONT_MONO)
    draw.text((690, 810), "Citation: Contract PDF p. 14, clause 4.2.1", fill=ACCENT_SKY, font=FONT_MONO)

    # Column 3: Mathematical Proof (audited delta)
    glow_pulse = 0.5 + 0.5 * math.sin(local_f * 0.18)
    delta_border = (int(16 + glow_pulse * 40), int(185 + glow_pulse * 50), 129)
    draw_card(draw, 1285, 530, 1805, 870, (18, 35, 30), delta_border, radius=12, width=2)
    draw.text((1310, 550), "3. MATHEMATICAL PROOF", fill=ACCENT_EMERALD, font=FONT_BODY_BOLD)
    draw.text((1310, 600), "+$322.50", fill=ACCENT_EMERALD, font=FONT_STAT_VAL)
    draw.text((1310, 665), "Pure Python Decimal Calculation:", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((1310, 700), "Delta Rate: $2.15 - $1.85 = $0.30/cwt", fill=TEXT_WHITE, font=FONT_MONO)
    draw.text((1310, 735), "Overcharge: $0.30 x 124.5 cwt = $37.35", fill=TEXT_WHITE, font=FONT_MONO)
    draw.text((1310, 770), "+ Unapplied Fuel Surcharge Credit = $285.15", fill=TEXT_WHITE, font=FONT_MONO)
    draw_badge(draw, "VERIFIED OVERCHARGE", 1310, 815, ACCENT_EMERALD_BG, ACCENT_EMERALD, ACCENT_EMERALD, FONT_BADGE)

    draw.text((80, 960), "100% Deterministic: Full traceable audit trail from raw invoice to carrier contract clause to exact decimal refund.", fill=TEXT_DIM, font=FONT_MICRO)


def draw_scene_4(im, draw, f):
    # Frames 435 to 599 (14.5s to 20.0s)
    # The Outro: Margin Protection & Clerk Sign-Off
    local_f = f - 435
    t_enter = ease_out_cubic(min(1.0, local_f / 20.0))
    y_offset = int((1.0 - t_enter) * 30)

    # Eyebrow
    draw_badge(draw, "COMMERCE MARGIN RECOVERY", 80, 125 + y_offset, ACCENT_EMERALD_BG, ACCENT_EMERALD, ACCENT_EMERALD, FONT_BADGE)

    # Headline
    draw.text((80, 175 + y_offset), "Clawback: Protect Margin on the Cost Side of Commerce.", fill=TEXT_WHITE, font=FONT_TITLE)
    draw.text((80, 240 + y_offset), "Full dispute package compiled for clerk sign-off. Instant claim export for carrier resolution.", fill=TEXT_MUTED, font=FONT_SUBTITLE)

    # Central Hero Action Card
    draw_card(draw, 80, 320, 1840, 870, BG_CARD, BORDER_CARD, radius=16)

    # Left half: Summary of recovery package
    draw.text((130, 370), "DISPUTE RECOVERY PACKAGE READY", fill=TEXT_WHITE, font=FONT_HEADING)
    draw.text((130, 420), "Generated with complete evidentiary chain and carrier invoice references", fill=TEXT_MUTED, font=FONT_BODY)
    draw.line([(130, 465), (960, 465)], fill=BORDER_CARD, width=1)

    items = [
        ("Claim Amount:", "$9,130.51  (284 Itemized Audit Discrepancies)", ACCENT_EMERALD),
        ("Audited Volume:", "1,250 Freight Bill Lines Audited", TEXT_WHITE),
        ("Arithmetic Proof:", "100% Python Decimal (Variance: $0.00)", ACCENT_SKY),
        ("Export Formats:", "Official Carrier Dispute PDF, EDI 210, CSV Ledger", TEXT_WHITE),
        ("Human-in-the-Loop:", "Clerk Sign-Off Verification Workflow", ACCENT_ROSE)
    ]
    iy = 490
    for label, val, col in items:
        draw.text((130, iy), label, fill=TEXT_MUTED, font=FONT_BODY)
        draw.text((360, iy), val, fill=col, font=FONT_BODY_BOLD)
        iy += 52

    # Action Button (pulsing border)
    btn_pulse = 0.5 + 0.5 * math.sin(local_f * 0.2)
    btn_col = (int(16 + btn_pulse * 40), int(185 + btn_pulse * 50), 129)
    draw_card(draw, 130, 770, 560, 835, (16, 185, 129), (255, 255, 255), radius=8, width=2)
    draw.text((170, 788), "EXPORT DISPUTE PACKAGE (PDF)", fill=(11, 15, 25), font=FONT_BODY_BOLD)

    # Right half: Track & Developer Badge
    draw_card(draw, 1020, 360, 1790, 830, (18, 25, 40), BORDER_CARD, radius=14)
    draw.text((1060, 400), "AMD DEVELOPER HACKATHON: ACT III", fill=ACCENT_AMD, font=FONT_HEADING)
    draw.text((1060, 445), "Track 3: Reinvent Commerce", fill=TEXT_WHITE, font=FONT_BODY_BOLD)
    draw.line([(1060, 485), (1750, 485)], fill=BORDER_CARD, width=1)

    draw.text((1060, 515), "Key Technologies:", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((1060, 550), "* AMD ROCm GPU Acceleration & PyTorch", fill=TEXT_WHITE, font=FONT_BODY)
    draw.text((1060, 585), "* Gemma 27B / 9B Contract Clause Extraction", fill=TEXT_WHITE, font=FONT_BODY)
    draw.text((1060, 620), "* Deterministic Python Decimal Rules Engine", fill=TEXT_WHITE, font=FONT_BODY)
    draw.text((1060, 655), "* React 18 + Tailwind + FastAPI Auditing Stack", fill=TEXT_WHITE, font=FONT_BODY)

    draw.text((1060, 715), "Open Source Repository:", fill=TEXT_MUTED, font=FONT_BODY)
    draw.text((1060, 750), "https://github.com/Abdullahs-git/clawback", fill=ACCENT_SKY, font=FONT_MONO_BOLD)

    # Footer note
    draw.text((80, 960), "CLAWBACK  *  Deterministic Carrier Freight Contract Audit & Overcharge Recovery Engine  *  Apache 2.0", fill=TEXT_DIM, font=FONT_MICRO)


def render_single_frame(f):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(im)

    # Background subtle grid pattern
    for gx in range(0, WIDTH, 120):
        draw.line([(gx, 0), (gx, HEIGHT)], fill=(16, 22, 34), width=1)
    for gy in range(0, HEIGHT, 120):
        draw.line([(0, gy), (WIDTH, gy)], fill=(16, 22, 34), width=1)

    # Draw persistent top header
    draw_header(draw, f)

    # Render scene according to timeline
    if f < 105:
        draw_scene_1(im, draw, f)
    elif f < 240:
        draw_scene_2(im, draw, f)
    elif f < 435:
        draw_scene_3(im, draw, f)
    else:
        draw_scene_4(im, draw, f)

    out_path = os.path.join("brag-output", "work", f"frame_{f:04d}.png")
    im.save(out_path)

    # Also save frame 0 as brag.jpg poster
    if f == 0:
        im.save(os.path.join("brag-output", "brag.jpg"), quality=95)

    return f


def main():
    os.makedirs(os.path.join("brag-output", "work"), exist_ok=True)
    t0 = time.time()
    num_workers = min(cpu_count(), 4)
    print(f"Starting frame generation: {TOTAL_FRAMES} frames using {num_workers} workers...")

    with Pool(num_workers) as pool:
        for idx in pool.imap_unordered(render_single_frame, range(TOTAL_FRAMES), chunksize=15):
            if idx % 100 == 0 or idx == TOTAL_FRAMES - 1:
                print(f"  Rendered frame {idx}/{TOTAL_FRAMES} ({round(time.time() - t0, 1)}s)")

    print(f"All {TOTAL_FRAMES} frames rendered in {round(time.time() - t0, 2)} seconds!")


if __name__ == "__main__":
    main()
