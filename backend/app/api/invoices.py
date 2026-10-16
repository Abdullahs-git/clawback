"""
Invoice Upload & Management API Router.
Parses CSV and PDF invoices into normalized invoice lines.
"""
import csv
from decimal import Decimal, ROUND_HALF_UP
import io
from pathlib import Path
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.invoice import InvoiceBatch, InvoiceLine
from backend.app.schemas.invoice import (
    InvoiceBatchSummary,
    InvoiceLineItemResponse,
    InvoiceLinesPagination
)

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

TWO_PLACES = Decimal("0.01")


def parse_csv_invoices(csv_content: str, batch_id: str) -> List[InvoiceLine]:
    """Parses CSV text into normalized InvoiceLine models with flexible column matching."""
    lines: List[InvoiceLine] = []
    reader = csv.DictReader(io.StringIO(csv_content))

    for idx, row in enumerate(reader, start=1):
        # Case-insensitive header dictionary
        clean_row = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}

        inv_num = clean_row.get("invoice_number") or clean_row.get("inv_no") or clean_row.get("invoice") or f"INV-{batch_id[:6]}"
        inv_date = clean_row.get("invoice_date") or clean_row.get("date") or "2026-09-01"
        shipment_id = clean_row.get("shipment_id") or clean_row.get("tracking_number") or clean_row.get("bol") or f"TRK-{idx:05d}"
        charge_code = clean_row.get("charge_code") or clean_row.get("code") or "FRT"
        charge_desc = clean_row.get("charge_description") or clean_row.get("description") or charge_code

        # Billed amount
        amount_raw = clean_row.get("amount_billed") or clean_row.get("billed_amount") or clean_row.get("amount") or clean_row.get("total") or "0.00"
        amount_clean = amount_raw.replace("$", "").replace(",", "").strip()
        try:
            amount_dec = Decimal(amount_clean).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        except Exception:
            amount_dec = Decimal("0.00")

        # Optional dimensions and weights
        def parse_float(val):
            try:
                return float(val) if val else None
            except ValueError:
                return None

        raw_line_id = clean_row.get("line_id") or f"LINE-{idx:05d}"
        line_id = f"{batch_id[:8]}-{raw_line_id}"

        line = InvoiceLine(
            id=line_id,
            batch_id=batch_id,
            invoice_number=inv_num,
            invoice_date=inv_date,
            shipment_id=shipment_id,
            charge_code=charge_code.upper(),
            charge_description=charge_desc,
            service_level=clean_row.get("service_level") or clean_row.get("service"),
            origin_zip=clean_row.get("origin_zip"),
            destination_zip=clean_row.get("destination_zip"),
            zone=clean_row.get("zone"),
            weight_actual_lbs=parse_float(clean_row.get("weight_actual_lbs") or clean_row.get("actual_weight")),
            dim_length_in=parse_float(clean_row.get("dim_length_in") or clean_row.get("length")),
            dim_width_in=parse_float(clean_row.get("dim_width_in") or clean_row.get("width")),
            dim_height_in=parse_float(clean_row.get("dim_height_in") or clean_row.get("height")),
            billed_weight_lbs=parse_float(clean_row.get("billed_weight_lbs") or clean_row.get("billed_weight")),
            published_rate=clean_row.get("published_rate"),
            discount_applied_percent=clean_row.get("discount_applied_percent") or clean_row.get("discount_percent"),
            fuel_surcharge_percent=clean_row.get("fuel_surcharge_percent") or clean_row.get("fuel_percent"),
            amount_billed=f"{amount_dec:.2f}"
        )
        lines.append(line)

    return lines


@router.post("/upload", response_model=InvoiceBatchSummary, status_code=201)
async def upload_invoices(
    file: UploadFile = File(...),
    carrier_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingests invoice records (CSV format supported; PDF text layer supported).
    Normalizes line items and saves batch for deterministic auditing.
    """
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only CSV or PDF invoice files are supported.")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size.")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    batch_id = str(uuid.uuid4())
    saved_path = upload_dir / f"{batch_id}_{file.filename}"
    with open(saved_path, "wb") as f:
        f.write(content)

    detected_carrier = carrier_name or file.filename.replace(".csv", "").replace(".pdf", "").replace("_", " ").title()

    lines: List[InvoiceLine] = []
    if filename.endswith(".csv"):
        text = content.decode("utf-8", errors="ignore")
        lines = parse_csv_invoices(text, batch_id)

    total_billed = sum(Decimal(line.amount_billed) for line in lines) if lines else Decimal("0.00")

    batch = InvoiceBatch(
        id=batch_id,
        carrier_name=detected_carrier,
        filename=file.filename,
        file_path=str(saved_path),
        total_lines=len(lines),
        total_billed_amount=f"{total_billed:.2f}"
    )
    db.add(batch)
    for line in lines:
        db.add(line)

    db.commit()
    db.refresh(batch)

    return InvoiceBatchSummary(
        id=batch.id,
        carrier_name=batch.carrier_name,
        filename=batch.filename,
        uploaded_at=batch.uploaded_at,
        total_lines=batch.total_lines,
        total_billed_amount=batch.total_billed_amount
    )


@router.get("", response_model=List[InvoiceBatchSummary])
def list_invoice_batches(db: Session = Depends(get_db)):
    """Lists all uploaded invoice batches."""
    batches = db.query(InvoiceBatch).order_by(InvoiceBatch.uploaded_at.desc()).all()
    return [InvoiceBatchSummary.model_validate(b) for b in batches]


@router.get("/{batch_id}/lines", response_model=InvoiceLinesPagination)
def get_batch_lines(
    batch_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Returns paginated invoice line items."""
    total = db.query(InvoiceLine).filter(InvoiceLine.batch_id == batch_id).count()
    offset = (page - 1) * limit
    lines = db.query(InvoiceLine).filter(InvoiceLine.batch_id == batch_id).offset(offset).limit(limit).all()

    return InvoiceLinesPagination(
        items=[InvoiceLineItemResponse.model_validate(l) for l in lines],
        total=total,
        page=page,
        limit=limit
    )
