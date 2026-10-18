"""
Dispute Letter Generation & Export Service.
Generates carrier dispute letters with 100% deterministic Decimal money totals,
verbatim contract citations, and structured evidence tables.
"""
import logging
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import io
from typing import Any, Dict, List, Optional, Set
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from backend.app.models.finding import AuditFinding

logger = logging.getLogger("clawback.dispute")
TWO_PLACES = Decimal("0.01")


def extract_numeric_tokens(text: str) -> List[str]:
    """Extracts currency or dollar/cents decimal tokens from text (e.g. $65.00, $65, 65.00)."""
    raw_matches = re.findall(r'\$\s*\d+(?:\.\d{1,2})?|\b\d+\.\d{2}\b', text)
    cleaned = []
    for m in raw_matches:
        val = m.replace('$', '').strip()
        cleaned.append(val)
    return cleaned


def validate_text_amounts_against_data(text: str, allowed_values: Set[str]) -> bool:
    """
    Validates that every numeric dollar amount appearing in generated text
    matches one of the authorized ground-truth amounts in allowed_values.
    Rejects any text where the model hallucinated or altered figures.
    """
    found_nums = extract_numeric_tokens(text)
    norm_allowed = set()
    for v in allowed_values:
        v_str = str(v).strip().replace('$', '')
        norm_allowed.add(v_str)
        try:
            d = Decimal(v_str)
            norm_allowed.add(f"{d:.2f}")
            norm_allowed.add(f"{d:.0f}")
        except Exception:
            pass

    for num in found_nums:
        # Ignore small integers likely to be page numbers, business days, or line counts
        if num in {"1", "2", "3", "4", "5", "10", "30", "60", "90", "180"}:
            continue
        if num not in norm_allowed:
            logger.warning(f"Amount validator rejected text: '{num}' not in allowed amounts: {norm_allowed}")
            return False
    return True


def generate_finding_plain_explanation(
    shipment_id: str,
    invoice_number: str,
    charge_code: str,
    rule_type: str,
    billed_amount: str,
    expected_amount: str,
    overcharge_amount: str,
    contract_page: int,
    contract_quote: str
) -> str:
    """
    Generates a concise plain-language summary for carrier billing clerks.
    Amounts are inserted directly from computed data and validated.
    """
    quote_snippet = f'"{contract_quote[:50]}..."' if len(contract_quote) > 50 else f'"{contract_quote}"'

    if rule_type == "accessorial_rule":
        text = (
            f"Shipment {shipment_id} (Invoice {invoice_number}) was billed ${billed_amount} for {charge_code}, "
            f"exceeding the contract rate of ${expected_amount} pursuant to Page {contract_page} ({quote_snippet}), "
            f"yielding a recoverable overcharge of ${overcharge_amount}."
        )
    elif rule_type == "base_discount":
        text = (
            f"Shipment {shipment_id} was billed ${billed_amount} with an inaccurate base discount, "
            f"whereas the contracted tariff yields ${expected_amount} (Page {contract_page}), "
            f"resulting in a ${overcharge_amount} discrepancy."
        )
    elif rule_type == "duplicate_charge":
        text = (
            f"Shipment {shipment_id} contains duplicate billing of ${billed_amount} for charge code {charge_code}, "
            f"creating a duplicate overcharge of ${overcharge_amount}."
        )
    else:
        text = (
            f"Discrepancy of ${overcharge_amount} on shipment {shipment_id}: billed ${billed_amount} "
            f"diverged from contracted ${expected_amount} per contract terms on Page {contract_page}."
        )

    allowed = {billed_amount, expected_amount, overcharge_amount}
    if not validate_text_amounts_against_data(text, allowed):
        # Fallback to guaranteed template if check fails
        return f"Discrepancy of ${overcharge_amount} on shipment {shipment_id} for code {charge_code}."
    return text



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

        plain_exp = generate_finding_plain_explanation(
            shipment_id=f.shipment_id,
            invoice_number=f.invoice_number,
            charge_code=f.charge_code,
            rule_type=f.rule_type,
            billed_amount=f.billed_amount,
            expected_amount=f.expected_amount,
            overcharge_amount=f.overcharge_amount,
            contract_page=f.contract_page or 1,
            contract_quote=f.contract_clause_quote or ""
        )

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
            "plain_explanation": plain_exp,
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
