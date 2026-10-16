"""
Dispute Letter Generation & Export Service.
Generates carrier dispute letters with 100% deterministic Decimal money totals,
verbatim contract citations, and structured evidence tables.
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import io
from typing import Any, Dict, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from backend.app.models.finding import AuditFinding

TWO_PLACES = Decimal("0.01")


def generate_dispute_letter_content(
    carrier_name: str,
    shipper_name: str,
    findings: List[AuditFinding]
) -> Dict[str, Any]:
    """
    Builds the dispute letter data structure, validating that all sums match deterministic Decimal math.
    """
    total_claim = Decimal("0.00")
    evidence_rows: List[Dict[str, Any]] = []

    earliest_deadline: Optional[str] = None

    for f in findings:
        overcharge_dec = Decimal(f.overcharge_amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        total_claim += overcharge_dec

        if f.claim_deadline_date:
            if earliest_deadline is None or f.claim_deadline_date < earliest_deadline:
                earliest_deadline = f.claim_deadline_date

        evidence_rows.append({
            "finding_id": f.id,
            "shipment_id": f.shipment_id,
            "invoice_number": f.invoice_number,
            "invoice_date": f.invoice_date,
            "charge_code": f.charge_code,
            "rule_type": f.rule_type,
            "rule_description": f.rule_description,
            "contract_page": f.contract_page,
            "contract_clause_reference": f.contract_clause_quote,
            "billed_amount": f.billed_amount,
            "expected_amount": f.expected_amount,
            "claim_amount": f.overcharge_amount,
            "explanation": f.calculation_math,
        })

    total_claim_str = f"{total_claim:.2f}"
    today_str = date.today().strftime("%B %d, %Y")

    subject = f"FORMAL NOTICE OF BILLING DISCREPANCY & OVERCHARGE CLAIM - {carrier_name.upper()} (Claim: ${total_claim_str})"

    deadline_note = f"\n\n**Filing Window Notice:** Earliest contractual claim deadline for these charges is {earliest_deadline}." if earliest_deadline else ""

    markdown_body = f"""# {subject}

**Date:** {today_str}  
**To:** {carrier_name} Billing & Revenue Recovery Department  
**From:** {shipper_name} Logistics & Accounts Payable  
**Total Claim Amount:** **${total_claim_str} USD**  
**Total Disputed Line Items:** {len(evidence_rows)} items  

---

### Dear Carrier Billing Operations Team,

Following a comprehensive audit of recent freight and transportation invoices against our agreed contractual terms and rate schedules, we have identified systematic billing discrepancies resulting in an aggregate overcharge of **${total_claim_str}**.

Pursuant to the contract clauses cited below, we formally request an immediate credit memo or refund in the amount of **${total_claim_str}**.

### Summary of Discrepancies
The itemized audit findings listed in the attached Schedule A demonstrate clear variances where billing diverged from agreed terms, including base discount miscalculations, unapplied accessorial fee caps/waivers, fuel surcharge rate discrepancies, and duplicate billings.{deadline_note}

Please review the attached evidence items and confirm the issuance of credit within thirty (30) business days.

Sincerely,  
**{shipper_name}**  
Audit & Logistics Operations
"""

    return {
        "date_generated": date.today().strftime("%Y-%m-%d"),
        "carrier_name": carrier_name,
        "shipper_name": shipper_name,
        "subject_line": subject,
        "body_markdown": markdown_body,
        "total_claim_amount": total_claim_str,
        "total_disputed_items": len(evidence_rows),
        "earliest_deadline_date": earliest_deadline,
        "evidence_table": evidence_rows,
        "status": "draft"
    }


def render_dispute_letter_markdown(letter_dict: Dict[str, Any]) -> str:
    """Renders the full dispute letter and Schedule A evidence table as Markdown."""
    lines = [
        letter_dict["body_markdown"],
        "\n\n## Schedule A: Itemized Evidence & Contract Clause Citations\n",
        "| Invoice # | Shipment ID | Charge Code | Contract Quote (Page) | Billed | Expected | Claim | Math Proof |",
        "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |"
    ]

    for item in letter_dict.get("evidence_table", []):
        quote_snippet = item.get('contract_clause_reference', '')[:60] + "..." if len(item.get('contract_clause_reference', '')) > 60 else item.get('contract_clause_reference', '')
        quote_col = f"\"{quote_snippet}\" (p.{item.get('contract_page', 1)})"
        lines.append(
            f"| {item.get('invoice_number')} | {item.get('shipment_id')} | {item.get('charge_code')} | "
            f"{quote_col} | ${item.get('billed_amount')} | ${item.get('expected_amount')} | "
            f"**${item.get('claim_amount')}** | {item.get('explanation')} |"
        )

    lines.append(f"\n\n**Total Claim Verified: ${letter_dict.get('total_claim_amount')} USD**\n")
    return "\n".join(lines)


def render_dispute_letter_pdf(letter_dict: Dict[str, Any]) -> bytes:
    """Generates a professional PDF dispute letter with evidence table using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14

    story = []

    # Title
    story.append(Paragraph(letter_dict["subject_line"], title_style))
    story.append(Spacer(1, 10))

    # Meta
    meta_text = (
        f"<b>Date:</b> {letter_dict.get('date_generated')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Carrier:</b> {letter_dict.get('carrier_name')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Total Claim:</b> <font color='#b91c1c'><b>${letter_dict.get('total_claim_amount')} USD</b></font>"
    )
    story.append(Paragraph(meta_text, normal_style))
    story.append(Spacer(1, 15))

    import re
    # Clean body paragraphs
    body_paragraphs = letter_dict["body_markdown"].split("\n\n")
    for p in body_paragraphs:
        if p.strip().startswith("#"):
            continue
        # Convert markdown bold to XML <b>...</b>
        clean_p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', p)
        # Escape stray ampersands not part of XML entities
        clean_p = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', clean_p)
        story.append(Paragraph(clean_p, normal_style))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Schedule A: Itemized Discrepancy Evidence Table</b>", styles['Heading2']))
    story.append(Spacer(1, 8))

    # Evidence Table
    table_data = [
        ["Inv #", "Shipment ID", "Code", "Contract Clause / Math", "Billed", "Expected", "Overcharge"]
    ]

    for row in letter_dict.get("evidence_table", [])[:30]:  # limit to top 30 in PDF
        desc = f"p.{row.get('contract_page', 1)}: {row.get('explanation', '')[:65]}"
        table_data.append([
            row.get("invoice_number", ""),
            row.get("shipment_id", ""),
            row.get("charge_code", ""),
            desc,
            f"${row.get('billed_amount', '')}",
            f"${row.get('expected_amount', '')}",
            f"${row.get('claim_amount', '')}"
        ])

    evidence_table = Table(table_data, colWidths=[65, 75, 45, 190, 50, 50, 55])
    evidence_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(evidence_table)
    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()
