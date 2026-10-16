"""
Dispute Letters API Router.
Generates, edits, approves, and exports formal carrier dispute letters.
"""
from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.finding import AuditFinding
from backend.app.models.dispute import DisputeLetter
from backend.app.schemas.dispute import (
    DisputeGenerateRequest,
    DisputeLetterUpdate,
    DisputeLetterResponse
)
from backend.app.services.dispute import (
    generate_dispute_letter_content,
    render_dispute_letter_markdown,
    render_dispute_letter_pdf
)

router = APIRouter(prefix="/api/disputes", tags=["Dispute Letters"])


@router.post("/generate", response_model=DisputeLetterResponse, status_code=201)
def generate_dispute(payload: DisputeGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates a formal carrier dispute letter with itemized evidence table.
    All figures are injected from deterministic engine calculations.
    """
    query = db.query(AuditFinding).filter(
        AuditFinding.batch_id == payload.batch_id,
        AuditFinding.carrier_name == payload.carrier_name
    )

    if payload.finding_ids:
        query = query.filter(AuditFinding.id.in_(payload.finding_ids))

    findings = query.all()
    if not findings:
        raise HTTPException(
            status_code=400,
            detail=f"No audit findings found for carrier {payload.carrier_name} in batch {payload.batch_id}."
        )

    letter_dict = generate_dispute_letter_content(
        carrier_name=payload.carrier_name,
        shipper_name=payload.shipper_name or "Shipper Logistics Operations",
        findings=findings
    )

    letter_id = str(uuid.uuid4())
    dispute_letter = DisputeLetter(
        id=letter_id,
        batch_id=payload.batch_id,
        carrier_name=letter_dict["carrier_name"],
        carrier_contact_email=f"disputes@{payload.carrier_name.lower().replace(' ', '')}.com",
        shipper_name=letter_dict["shipper_name"],
        date_generated=letter_dict["date_generated"],
        earliest_deadline_date=letter_dict["earliest_deadline_date"],
        total_claim_amount=letter_dict["total_claim_amount"],
        total_disputed_items=letter_dict["total_disputed_items"],
        subject_line=letter_dict["subject_line"],
        body_markdown=letter_dict["body_markdown"],
        evidence_table=letter_dict["evidence_table"],
        status="draft"
    )
    db.add(dispute_letter)

    # Mark findings status
    for f in findings:
        f.status = "included_in_dispute"

    db.commit()
    db.refresh(dispute_letter)

    return DisputeLetterResponse.model_validate(dispute_letter)


@router.get("", response_model=List[DisputeLetterResponse])
def list_disputes(db: Session = Depends(get_db)):
    """Lists all generated dispute letters."""
    letters = db.query(DisputeLetter).order_by(DisputeLetter.created_at.desc()).all()
    return [DisputeLetterResponse.model_validate(l) for l in letters]


@router.get("/{letter_id}", response_model=DisputeLetterResponse)
def get_dispute(letter_id: str, db: Session = Depends(get_db)):
    """Gets details for a dispute letter."""
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found.")
    return DisputeLetterResponse.model_validate(letter)


@router.patch("/{letter_id}", response_model=DisputeLetterResponse)
def update_dispute(
    letter_id: str,
    payload: DisputeLetterUpdate,
    db: Session = Depends(get_db)
):
    """
    Edits or approves a dispute letter.
    Human in the loop: requires explicit approval before export.
    """
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found.")

    if payload.subject_line is not None:
        letter.subject_line = payload.subject_line
    if payload.body_markdown is not None:
        letter.body_markdown = payload.body_markdown
    if payload.status is not None:
        letter.status = payload.status
        if payload.status == "approved":
            letter.approved_at = datetime.now(timezone.utc)
            letter.approved_by = payload.approved_by or "Logistics Manager"

    db.commit()
    db.refresh(letter)
    return DisputeLetterResponse.model_validate(letter)


@router.get("/{letter_id}/export")
def export_dispute(
    letter_id: str,
    format: str = Query("markdown", pattern="^(markdown|pdf)$"),
    db: Session = Depends(get_db)
):
    """Exports approved dispute letter as Markdown or PDF."""
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found.")

    letter_dict = {
        "id": letter.id,
        "carrier_name": letter.carrier_name,
        "shipper_name": letter.shipper_name,
        "date_generated": letter.date_generated,
        "subject_line": letter.subject_line,
        "body_markdown": letter.body_markdown,
        "total_claim_amount": letter.total_claim_amount,
        "total_disputed_items": letter.total_disputed_items,
        "evidence_table": letter.evidence_table or []
    }

    if format == "pdf":
        pdf_bytes = render_dispute_letter_pdf(letter_dict)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=dispute_{letter.carrier_name.lower().replace(' ', '_')}_{letter.date_generated}.pdf"}
        )
    else:
        md_text = render_dispute_letter_markdown(letter_dict)
        return Response(
            content=md_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=dispute_{letter.carrier_name.lower().replace(' ', '_')}_{letter.date_generated}.md"}
        )
