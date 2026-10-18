"""
Contracts & Rules API Router.
Handles contract PDF upload, rule extraction via Gemma on AMD,
and human-in-the-loop rule approval/rejection.
"""
import re
from pathlib import Path
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.contract import Contract, ContractRule
from backend.app.schemas.contract import (
    ContractSummaryResponse,
    ContractDetailResponse,
    ContractRuleResponse,
    ContractRuleUpdate,
    ContractBatchRulesUpdate
)
from backend.app.services.extraction import extract_contract_rules
from backend.app.services.rate_limiter import check_upload_rate_limit, check_llm_rate_limit

router = APIRouter(prefix="/api/contracts", tags=["Contracts & Rules"])


@router.post("/upload", response_model=ContractDetailResponse, status_code=201)
async def upload_contract(
    request: Request,
    file: UploadFile = File(...),
    carrier_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Uploads a carrier contract PDF, extracts rules using Gemma on AMD,
    verifies source quotes against the document text, and persists rules for human review.
    Enforces rate limits, magic byte validation, and filename sanitization.
    """
    check_upload_rate_limit(request)
    check_llm_rate_limit(request)

    clean_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', Path(file.filename or "contract.pdf").name)
    if not clean_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF contracts are supported.")

    content = await file.read()
    max_mb = 5 if getattr(settings, "DEMO_MODE", False) else settings.MAX_UPLOAD_SIZE_MB
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {max_mb}MB"
        )

    # Validate PDF magic bytes
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF format: missing PDF header signature.")

    # Save uploaded file
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / f"{uuid.uuid4()}_{clean_filename}"
    with open(saved_path, "wb") as f:
        f.write(content)

    # Extract rules via Gemma pipeline
    carrier_hint = carrier_name or clean_filename.replace(".pdf", "").replace("_", " ").title()
    extraction = await extract_contract_rules(
        pdf_bytes=content,
        filename=clean_filename,
        carrier_hint=carrier_hint,
        db=db,
        cache_key=f"contract_{carrier_hint.lower().replace(' ', '_')}"
    )

    detected_carrier = extraction.get("carrier_name") or carrier_hint
    contract_id = str(uuid.uuid4())

    contract = Contract(
        id=contract_id,
        carrier_name=detected_carrier,
        filename=file.filename,
        file_path=str(saved_path),
        contract_reference=extraction.get("contract_reference"),
        effective_date=extraction.get("effective_date"),
        expiration_date=extraction.get("expiration_date"),
    )
    db.add(contract)

    # Persist extracted rules
    rules_out = []
    for r in extraction.get("rules", []):
        raw_id = r.get("id") or f"RULE-{uuid.uuid4().hex[:6].upper()}"
        rule_id = f"{contract_id[:8]}-{raw_id}"
        rule_obj = ContractRule(
            id=rule_id,
            contract_id=contract_id,
            type=r.get("type", "base_discount"),
            description=r.get("description", "Extracted rule"),
            parameters=r.get("parameters", {}),
            source_page=r.get("source_page", 1),
            source_quote=r.get("source_quote", ""),
            confidence=r.get("confidence", 1.0),
            status=r.get("status", "proposed"),
            rejection_reason=r.get("rejection_reason")
        )
        db.add(rule_obj)
        rules_out.append(rule_obj)

    db.commit()
    db.refresh(contract)

    return ContractDetailResponse(
        id=contract.id,
        carrier_name=contract.carrier_name,
        filename=contract.filename,
        contract_reference=contract.contract_reference,
        effective_date=contract.effective_date,
        expiration_date=contract.expiration_date,
        uploaded_at=contract.uploaded_at,
        rules=[ContractRuleResponse.model_validate(r) for r in rules_out]
    )


@router.get("", response_model=List[ContractSummaryResponse])
def list_contracts(db: Session = Depends(get_db)):
    """Lists all uploaded contracts with rule counts."""
    contracts = db.query(Contract).order_by(Contract.uploaded_at.desc()).all()
    out = []
    for c in contracts:
        total_rules = len(c.rules)
        approved_rules = sum(1 for r in c.rules if r.status == "approved")
        out.append(
            ContractSummaryResponse(
                id=c.id,
                carrier_name=c.carrier_name,
                filename=c.filename,
                uploaded_at=c.uploaded_at,
                rule_count=total_rules,
                approved_rule_count=approved_rules
            )
        )
    return out


@router.get("/{contract_id}", response_model=ContractDetailResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    """Gets contract details and full list of extracted rules."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return ContractDetailResponse(
        id=contract.id,
        carrier_name=contract.carrier_name,
        filename=contract.filename,
        contract_reference=contract.contract_reference,
        effective_date=contract.effective_date,
        expiration_date=contract.expiration_date,
        uploaded_at=contract.uploaded_at,
        rules=[ContractRuleResponse.model_validate(r) for r in contract.rules]
    )


@router.patch("/{contract_id}/rules/{rule_id}", response_model=ContractRuleResponse)
def update_contract_rule(
    contract_id: str,
    rule_id: str,
    payload: ContractRuleUpdate,
    db: Session = Depends(get_db)
):
    """
    Human-in-the-loop endpoint: approve, reject, or edit an extracted rule.
    """
    rule = db.query(ContractRule).filter(
        ContractRule.id == rule_id,
        ContractRule.contract_id == contract_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")

    if payload.status is not None:
        rule.status = payload.status
    if payload.parameters is not None:
        rule.parameters = payload.parameters
    if payload.description is not None:
        rule.description = payload.description
    if payload.rejection_reason is not None:
        rule.rejection_reason = payload.rejection_reason

    db.commit()
    db.refresh(rule)
    return ContractRuleResponse.model_validate(rule)


@router.post("/{contract_id}/rules/batch")
def batch_update_rules(
    contract_id: str,
    payload: ContractBatchRulesUpdate,
    db: Session = Depends(get_db)
):
    """Batch approve or reject all selected rules."""
    new_status = "approved" if payload.action == "approve" else "rejected"
    updated = db.query(ContractRule).filter(
        ContractRule.contract_id == contract_id,
        ContractRule.id.in_(payload.rule_ids)
    ).update({"status": new_status}, synchronize_session="fetch")

    db.commit()
    return {"updated_count": updated}


@router.get("/{contract_id}/text")
def get_contract_text(contract_id: str, db: Session = Depends(get_db)):
    """Extracts and returns page text for the contract PDF to support contract viewer quote grounding."""
    from pathlib import Path
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")

    pages = []
    if contract.file_path and Path(contract.file_path).exists():
        try:
            import pypdf
            reader = pypdf.PdfReader(contract.file_path)
            for i, p in enumerate(reader.pages):
                pages.append({
                    "page_number": i + 1,
                    "text": p.extract_text() or ""
                })
        except Exception:
            pass

    return {
        "contract_id": contract.id,
        "carrier_name": contract.carrier_name,
        "filename": contract.filename,
        "pages": pages
    }
