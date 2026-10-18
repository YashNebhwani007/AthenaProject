"""Generate high-resolution animated demonstration GIF for Athena README and documentation."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_frame(
    step: int,
    step_desc: str,
    active_tab: str = "workspace",
) -> Image.Image:
    """Render a single high-fidelity frame of the Athena dark-mode user interface."""
    width, height = 1200, 750
    img = Image.new("RGB", (width, height), color=(10, 13, 20))
    draw = ImageDraw.Draw(img)

    # Fonts - fallback to default if TTF not available
    try:
        font_logo = ImageFont.truetype("arialbd.ttf", 22)
        font_title = ImageFont.truetype("arialbd.ttf", 18)
        font_h2 = ImageFont.truetype("arialbd.ttf", 15)
        font_body = ImageFont.truetype("arial.ttf", 13)
        font_bold = ImageFont.truetype("arialbd.ttf", 13)
        font_small = ImageFont.truetype("arial.ttf", 11)
        font_mono = ImageFont.truetype("consola.ttf", 12)
    except Exception:
        font_logo = font_title = font_h2 = font_body = font_bold = font_small = font_mono = ImageFont.load_default()

    # Colors
    c_card = (17, 24, 39)
    c_card_border = (45, 55, 72)
    c_text_main = (248, 250, 252)
    c_text_sub = (148, 163, 184)
    c_accent_indigo = (99, 102, 241)
    c_accent_cyan = (6, 182, 212)
    c_accent_emerald = (16, 185, 129)
    c_accent_amber = (245, 158, 11)

    # 1. Top Navigation Header
    draw.rectangle([0, 0, width, 56], fill=(15, 23, 42), outline=c_card_border)
    # Brand logo badge
    draw.rounded_rectangle([20, 12, 54, 44], radius=6, fill=c_accent_indigo)
    draw.text((29, 17), "A", fill=(255, 255, 255), font=font_logo)
    draw.text((64, 18), "ATHENA", fill=c_text_main, font=font_title)

    # Subtitle tag
    draw.rounded_rectangle([160, 18, 330, 38], radius=10, fill=(30, 41, 59))
    draw.text((172, 22), "Evidence-Grounded Agent", fill=c_accent_cyan, font=font_small)

    # Navigation tabs
    draw.rounded_rectangle([400, 14, 550, 42], radius=6, fill=(30, 41, 59) if active_tab == "workspace" else (15, 23, 42))
    draw.text((415, 20), "⚡ Analysis Workspace", fill=c_text_main, font=font_bold)
    draw.rounded_rectangle([565, 14, 730, 42], radius=6, fill=(30, 41, 59) if active_tab == "benchmark" else (15, 23, 42))
    draw.text((580, 20), "📊 Benchmark Evaluation", fill=c_text_sub, font=font_body)

    # Right header status
    draw.rounded_rectangle([1020, 16, 1180, 40], radius=12, fill=(16, 185, 129, 40), outline=c_accent_emerald)
    draw.text((1035, 21), "● System Ready", fill=c_accent_emerald, font=font_small)

    # Three-Panel Layout Coordinates
    left_x, left_w = 20, 280
    center_x, center_w = 315, 570
    right_x, right_w = 900, 280

    # ================= LEFT PANEL: Dataset Profile =================
    draw.rounded_rectangle([left_x, 70, left_x + left_w, 730], radius=10, fill=c_card, outline=c_card_border)
    draw.text((left_x + 16, 86), "Active Dataset", fill=c_text_main, font=font_h2)
    draw.rounded_rectangle([left_x + 16, 116, left_x + left_w - 16, 170], radius=8, fill=(30, 41, 59))
    draw.text((left_x + 28, 126), "Telco Customer Churn", fill=c_text_main, font=font_bold)
    draw.text((left_x + 28, 146), "1,000 rows • 8 columns • CSV", fill=c_text_sub, font=font_small)

    # Column inspection table
    draw.text((left_x + 16, 190), "Schema & Missingness", fill=c_text_sub, font=font_bold)
    cols = [
        ("customer_id", "STRING", "0.0%"),
        ("contract", "STRING", "0.0%"),
        ("monthly_charges", "FLOAT", "0.0%"),
        ("total_charges", "FLOAT", "0.0%"),
        ("tenure", "INTEGER", "0.0%"),
        ("churn", "STRING (target)", "0.0%"),
    ]
    y_pos = 215
    for c_name, c_type, c_null in cols:
        draw.text((left_x + 16, y_pos), c_name, fill=c_text_main, font=font_body)
        draw.text((left_x + 155, y_pos), c_type, fill=c_accent_cyan if "target" in c_type else c_text_sub, font=font_small)
        # progress bar
        draw.rectangle([left_x + 16, y_pos + 18, left_x + left_w - 16, y_pos + 21], fill=(51, 65, 85))
        draw.rectangle([left_x + 16, y_pos + 18, left_x + left_w - 16, y_pos + 21], fill=c_accent_emerald)
        y_pos += 34

    # Data Quality card
    draw.rounded_rectangle([left_x + 16, 440, left_x + left_w - 16, 540], radius=8, fill=(15, 23, 42), outline=c_card_border)
    draw.text((left_x + 28, 452), "Data Quality Profile", fill=c_text_main, font=font_bold)
    draw.text((left_x + 28, 474), "✓ No duplicate rows detected", fill=c_accent_emerald, font=font_small)
    draw.text((left_x + 28, 494), "✓ Missingness < 1% across features", fill=c_accent_emerald, font=font_small)
    draw.text((left_x + 28, 514), "✓ ID columns excluded from model", fill=c_accent_emerald, font=font_small)

    # ================= CENTER PANEL: Query & Report =================
    draw.rounded_rectangle([center_x, 70, center_x + center_w, 205], radius=10, fill=c_card, outline=c_card_border)
    draw.text((center_x + 16, 86), "Analytical Inquiry", fill=c_text_main, font=font_h2)

    # Query Input Box
    draw.rounded_rectangle([center_x + 16, 116, center_x + center_w - 110, 156], radius=6, fill=(10, 13, 20), outline=c_accent_indigo)
    query_text = "What is the overall churn rate across all customers?"
    draw.text((center_x + 28, 126), query_text, fill=c_text_main, font=font_body)

    # Run button
    btn_color = c_accent_indigo if step < 4 else (71, 85, 105)
    draw.rounded_rectangle([center_x + center_w - 100, 116, center_x + center_w - 16, 156], radius=6, fill=btn_color)
    btn_label = "Running..." if (1 <= step <= 3) else "Ask Athena"
    draw.text((center_x + center_w - 92, 126), btn_label, fill=(255, 255, 255), font=font_bold)

    # Prompt suggestions
    draw.text((center_x + 16, 172), "Quick Prompts:", fill=c_text_sub, font=font_small)
    draw.rounded_rectangle([center_x + 100, 168, center_x + 310, 188], radius=4, fill=(30, 41, 59))
    draw.text((center_x + 108, 172), "Charges difference test (p < 0.05)", fill=c_text_sub, font=font_small)
    draw.rounded_rectangle([center_x + 320, 168, center_x + 480, 188], radius=4, fill=(30, 41, 59))
    draw.text((center_x + 328, 172), "Train predictive model", fill=c_text_sub, font=font_small)

    # Report View Box
    draw.rounded_rectangle([center_x, 220, center_x + center_w, 730], radius=10, fill=c_card, outline=c_card_border)

    if step == 0:
        draw.text((center_x + 170, 420), "Enter a question or select a prompt to begin analysis.", fill=c_text_sub, font=font_body)
    else:
        # Report Title & Verification Badge
        draw.text((center_x + 20, 238), "Verified Analytical Report", fill=c_text_main, font=font_h2)

        if step >= 3:
            # Verification badge
            draw.rounded_rectangle([center_x + center_w - 165, 235, center_x + center_w - 20, 260], radius=12, fill=(16, 185, 129, 35), outline=c_accent_emerald)
            draw.text((center_x + center_w - 153, 240), "✓ Verified (5/5 Checks)", fill=c_accent_emerald, font=font_bold)

        # TL;DR callout
        draw.rounded_rectangle([center_x + 20, 275, center_x + center_w - 20, 340], radius=8, fill=(30, 41, 59), outline=c_accent_indigo)
        draw.text((center_x + 32, 285), "Executive Summary (TL;DR)", fill=c_accent_cyan, font=font_bold)
        tldr_text = (
            "The customer churn rate across the 1,000 active customer cohort is 26.5%\n"
            "(265 churned accounts out of 1,000 total subscribers)."
            if step >= 2 else "Analyzing cohort metrics in DuckDB..."
        )
        draw.text((center_x + 32, 305), tldr_text, fill=c_text_main, font=font_body)

        # Grounded Findings Section
        draw.text((center_x + 20, 360), "Grounded Findings & Evidence", fill=c_text_main, font=font_bold)

        # Finding card 1
        draw.rounded_rectangle([center_x + 20, 385, center_x + center_w - 20, 455], radius=6, fill=(15, 23, 42), outline=c_card_border)
        draw.text((center_x + 32, 396), "Finding 1: Baseline Population Churn Rate", fill=c_text_main, font=font_bold)

        # Finding text with Evidence Chip
        draw.text((center_x + 32, 420), "Observed churn rate is 0.265 (265 customers)", fill=c_text_sub, font=font_body)
        draw.rounded_rectangle([center_x + 310, 417, center_x + 420, 437], radius=4, fill=(16, 185, 129, 40), outline=c_accent_emerald)
        draw.text((center_x + 320, 422), "t1.churn_rate 🔍", fill=c_accent_emerald, font=font_small)

        # Interactive Visualization Box
        draw.text((center_x + 20, 475), "Analytical Visualization (Plotly)", fill=c_text_main, font=font_bold)
        draw.rounded_rectangle([center_x + 20, 500, center_x + center_w - 20, 640], radius=6, fill=(10, 13, 20), outline=c_card_border)

        # Draw a simulated Plotly bar chart
        draw.rectangle([center_x + 120, 530, center_x + 210, 615], fill=c_accent_indigo)
        draw.text((center_x + 130, 620), "Retained (73.5%)", fill=c_text_sub, font=font_small)
        draw.text((center_x + 145, 510), "735", fill=c_text_main, font=font_bold)

        draw.rectangle([center_x + 290, 565, center_x + 380, 615], fill=c_accent_cyan)
        draw.text((center_x + 300, 620), "Churned (26.5%)", fill=c_text_sub, font=font_small)
        draw.text((center_x + 325, 545), "265", fill=c_text_main, font=font_bold)

        # Recommendations
        draw.text((center_x + 20, 655), "Evidence-Linked Recommendations", fill=c_text_main, font=font_bold)
        draw.rounded_rectangle([center_x + 20, 680, center_x + center_w - 20, 720], radius=6, fill=(15, 23, 42), outline=c_card_border)
        draw.text((center_x + 32, 690), "• Prioritize proactive retention on month-to-month contracts. [Supported by f1]", fill=c_text_sub, font=font_small)

    # ================= RIGHT PANEL: Live Execution Trace =================
    draw.rounded_rectangle([right_x, 70, right_x + right_w, 730], radius=10, fill=c_card, outline=c_card_border)
    draw.text((right_x + 16, 86), "Execution Trace", fill=c_text_main, font=font_h2)
    draw.text((right_x + 16, 108), "Real-time tool invocation log", fill=c_text_sub, font=font_small)

    steps_data = [
        ("t1", "profile_dataset", "ok", "42ms", "Rows: 1,000, Cols: 8, Nulls: 0%"),
        ("t2", "run_sql", "ok", "18ms", "SELECT avg(churn='Yes') -> 0.265"),
        ("t3", "make_plot", "ok", "85ms", "Plotly bar spec generated"),
        ("t4", "verifier_v1_v5", "ok", "12ms", "All 5 mathematical rules passed"),
    ]

    curr_y = 135
    for i, (tid, tool, status, dur, out_summary) in enumerate(steps_data):
        if i > step:
            break

        is_current = (i == step)
        box_border = c_accent_cyan if is_current else c_card_border
        draw.rounded_rectangle([right_x + 14, curr_y, right_x + right_w - 14, curr_y + 80], radius=6, fill=(20, 30, 48) if is_current else (15, 23, 42), outline=box_border)

        status_color = c_accent_emerald if status == "ok" else c_accent_amber
        draw.text((right_x + 24, curr_y + 8), f"[{tid}] {tool}", fill=c_text_main, font=font_bold)
        draw.text((right_x + right_w - 65, curr_y + 8), dur, fill=c_text_sub, font=font_small)

        # status pill
        draw.rounded_rectangle([right_x + 24, curr_y + 32, right_x + 72, curr_y + 48], radius=8, fill=(16, 185, 129, 30))
        draw.text((right_x + 32, curr_y + 34), "✓ ok", fill=status_color, font=font_small)

        draw.text((right_x + 24, curr_y + 56), out_summary, fill=c_text_sub, font=font_small)
        curr_y += 92

    # Status indicator badge on bottom
    draw.rounded_rectangle([right_x + 14, 675, right_x + right_w - 14, 715], radius=6, fill=(30, 41, 59))
    draw.text((right_x + 24, 688), f"Status: {step_desc}", fill=c_accent_cyan, font=font_small)

    return img


def main() -> None:
    frames: list[Image.Image] = []
    durations: list[int] = []

    steps = [
        (0, "Ready - Dataset loaded", 1200),
        (1, "Step 1: Running dataset profiler...", 1400),
        (2, "Step 2: Executing deterministic SQL...", 1500),
        (3, "Step 3: Verifying claim grounding (5/5 rules)...", 1600),
        (4, "Complete: Verified report generated with interactive chart", 3000),
    ]

    for step_idx, desc, dur in steps:
        frame = create_frame(step_idx, desc)
        frames.append(frame)
        durations.append(dur)

    out_path = Path("docs/demo.gif")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"Generated demo GIF at {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
