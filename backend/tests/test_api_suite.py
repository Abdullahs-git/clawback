"""
Full API Test Suite for Clawback.
Tests every API route: health, AMD status, contract upload & rules review,
invoice ingestion, deterministic audit execution, and dispute letter export.
"""
import io
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from backend.app.main import app
from backend.app.database import Base, engine


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup


@pytest.fixture
def client():
    return TestClient(app)


def create_sample_contract_pdf() -> bytes:
    """Generates a small in-memory PDF contract containing verifiable clauses."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(50, 750, "FREIGHT TRANSPORTATION SERVICES AGREEMENT")
    c.drawString(50, 730, "Carrier: Apex Freight Logistics")
    c.drawString(50, 710, "Effective: 2026-01-01")
    c.showPage()  # Page 1

    # Page 2
    c.drawString(50, 750, "Section 3: Rate Schedules and Discounts")
    c.drawString(50, 730, "Shipper shall receive an agreed base discount of forty-five percent (45.0%) off all published standard linehaul rates.")
    c.showPage()

    # Page 3
    c.drawString(50, 750, "Section 4: Accessorial Terms")
    c.drawString(50, 730, "Residential delivery surcharges shall be waived in full and shall not be assessed on any shipment.")
    c.drawString(50, 710, "Where requested, liftgate service charges shall not exceed forty dollars ($40.00) per occurrence.")
    c.showPage()

    # Page 4
    c.drawString(50, 750, "Section 5: Fuel and Dimensional Divisor")
    c.drawString(50, 730, "The applicable fuel surcharge index is agreed and fixed at eleven and one-half percent (11.5%) of net linehaul freight.")
    c.drawString(50, 710, "Cubic dimensional weight calculations shall strictly utilize a divisor of one hundred sixty-six (166).")
    c.showPage()

    # Page 5
    c.drawString(50, 750, "Section 6: Minimums and Billing Integrity")
    c.drawString(50, 730, "The minimum charge floor per shipment after discount application shall be forty-five dollars ($45.00).")
    c.drawString(50, 710, "Carrier warrants that no individual shipment BOL or tracking number shall be invoiced more than once.")
    c.showPage()

    # Page 6
    c.drawString(50, 750, "Section 7: Dispute Deadlines")
    c.drawString(50, 730, "Disputes and overcharge claims must be formally submitted in writing within one hundred eighty (180) days of invoice date.")
    c.showPage()

    c.save()
    buf.seek(0)
    return buf.getvalue()


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "Clawback"


def test_amd_status(client):
    resp = client.get("/api/amd-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "model_name" in data
    assert "endpoint_host" in data
    assert data["mode"] in ["live", "replay"]


def test_full_pipeline_flow(client):
    # 1. Upload Contract PDF
    pdf_bytes = create_sample_contract_pdf()
    files = {"file": ("apex_contract.pdf", pdf_bytes, "application/pdf")}
    data = {"carrier_name": "Apex Freight Logistics"}

    upload_resp = client.post("/api/contracts/upload", files=files, data=data)
    assert upload_resp.status_code == 201
    contract = upload_resp.json()
    contract_id = contract["id"]
    assert contract["carrier_name"] == "Apex Freight Logistics"
    assert len(contract["rules"]) >= 5

    # Check quote verification safeguard
    for rule in contract["rules"]:
        assert rule["status"] in ["proposed", "rejected"]
        if rule["status"] == "rejected":
            assert rule["rejection_reason"] is not None

    # 2. Approve Proposed Rules
    rule_ids = [r["id"] for r in contract["rules"] if r["status"] == "proposed"]
    assert len(rule_ids) > 0

    batch_approve_resp = client.post(
        f"/api/contracts/{contract_id}/rules/batch",
        json={"action": "approve", "rule_ids": rule_ids}
    )
    assert batch_approve_resp.status_code == 200
    assert batch_approve_resp.json()["updated_count"] == len(rule_ids)

    # 3. Upload Invoices CSV with known planted discrepancies
    csv_content = """invoice_number,invoice_date,shipment_id,charge_code,published_rate,amount_billed,fuel_surcharge_percent
INV-1001,2026-09-01,TRK-5001,FRT,100.00,75.00,
INV-1001,2026-09-01,TRK-5001,RES,,25.00,
INV-1002,2026-09-02,TRK-5002,FSC,,20.00,20.0
INV-1003,2026-09-03,TRK-5003,FRT,100.00,55.00,
INV-1003,2026-09-03,TRK-5003,FRT,100.00,55.00,
"""
    csv_file = {"file": ("invoices_batch.csv", csv_content.encode("utf-8"), "text/csv")}
    inv_resp = client.post("/api/invoices/upload", files=csv_file, data={"carrier_name": "Apex Freight Logistics"})
    assert inv_resp.status_code == 201
    batch = inv_resp.json()
    batch_id = batch["id"]
    assert batch["total_lines"] == 5

    # 4. Run Deterministic Audit
    audit_resp = client.post(
        "/api/audit/run",
        json={"batch_id": batch_id, "contract_id": contract_id}
    )
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["lines_audited"] == 5
    assert audit_data["discrepancies_count"] >= 3
    assert Decimal(audit_data["total_overcharge_amount"]) > Decimal("0.00")

    # 5. Query Findings
    findings_resp = client.get(f"/api/audit/findings?batch_id={batch_id}")
    assert findings_resp.status_code == 200
    overview = findings_resp.json()
    assert len(overview["findings"]) >= 3
    assert Decimal(overview["total_overcharge"]) > Decimal("0.00")

    first_finding = overview["findings"][0]
    finding_id = first_finding["finding_id"]

    # Verify Finding Drilldown & Traceability
    detail_resp = client.get(f"/api/audit/findings/{finding_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["contract_clause_quote"] != ""
    assert detail["calculation_math"] != ""
    assert Decimal(detail["overcharge_amount"]) > Decimal("0.00")

    # 6. Generate Dispute Letter
    dispute_resp = client.post(
        "/api/disputes/generate",
        json={
            "batch_id": batch_id,
            "carrier_name": "Apex Freight Logistics",
            "shipper_name": "Acme Manufacturing"
        }
    )
    assert dispute_resp.status_code == 201
    letter = dispute_resp.json()
    letter_id = letter["id"]
    assert letter["status"] == "draft"
    assert Decimal(letter["total_claim_amount"]) == Decimal(overview["total_overcharge"])

    # 7. Approve Dispute Letter
    patch_resp = client.patch(
        f"/api/disputes/{letter_id}",
        json={"status": "approved", "approved_by": "Finance Director"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "approved"

    # 8. Export Dispute Letter (Markdown & PDF)
    md_export = client.get(f"/api/disputes/{letter_id}/export?format=markdown")
    assert md_export.status_code == 200
    assert "FORMAL NOTICE OF BILLING DISCREPANCY" in md_export.text
    assert "Schedule A" in md_export.text

    pdf_export = client.get(f"/api/disputes/{letter_id}/export?format=pdf")
    assert pdf_export.status_code == 200
    assert pdf_export.headers["content-type"] == "application/pdf"
    assert len(pdf_export.content) > 1000


def test_scanned_pdf_rejection(client):
    """Uploading a PDF with no extractable text layer triggers the scanned image error."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    # Blank page without text
    c.showPage()
    c.save()
    buf.seek(0)
    scanned_bytes = buf.getvalue()

    files = {"file": ("scanned_invoice.pdf", scanned_bytes, "application/pdf")}
    data = {"carrier_name": "Scanned Carrier"}

    resp = client.post("/api/contracts/upload", files=files, data=data)
    assert resp.status_code == 400
    assert "Scanned image detected. Upload a text PDF or CSV." in resp.json()["detail"]


def test_invalid_file_extension(client):
    """Non-PDF upload should return 400."""
    files = {"file": ("test.docx", b"dummy content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    resp = client.post("/api/contracts/upload", files=files)
    assert resp.status_code == 400
    assert "Only PDF contracts are supported" in resp.json()["detail"]


def test_contract_not_found(client):
    resp = client.get("/api/contracts/non-existent-id")
    assert resp.status_code == 404


def test_demo_seed_and_benchmark_endpoints(client):
    seed_resp = client.post("/api/demo/seed")
    assert seed_resp.status_code == 200
    assert seed_resp.json()["status"] == "success"

    bench_resp = client.get("/api/benchmark")
    assert bench_resp.status_code == 200
    b_data = bench_resp.json()
    assert "audit_engine" in b_data
    assert b_data["audit_engine"]["detected_dollars"] == "9130.51"


def test_live_test_call_endpoint(client):
    resp = client.post("/api/amd/live-test-call")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "latency_ms" in data
    assert "tokens_per_second" in data
    assert "extracted_data" in data


def test_charge_normalization_api_endpoints(client):
    # Test raw list normalization
    resp = client.post(
        "/api/invoices/normalize-descriptions",
        json=["RESI DLVRY", "LIFT GATE SVC", "FUEL SURCHARGE"]
    )
    assert resp.status_code == 200
    mappings = resp.json()["mappings"]
    assert mappings["RESI DLVRY"]["canonical_code"] == "RES"
    assert mappings["LIFT GATE SVC"]["canonical_code"] == "LFG"
    assert mappings["FUEL SURCHARGE"]["canonical_code"] == "FUEL"


def test_contract_text_and_batch_rules(client):
    # Upload contract
    pdf_bytes = create_sample_contract_pdf()
    files = {"file": ("text_test_contract.pdf", pdf_bytes, "application/pdf")}
    upload_resp = client.post("/api/contracts/upload", files=files)
    assert upload_resp.status_code == 201
    cid = upload_resp.json()["id"]

    # 1. Fetch text
    text_resp = client.get(f"/api/contracts/{cid}/text")
    assert text_resp.status_code == 200
    t_data = text_resp.json()
    assert len(t_data["pages"]) >= 6
    assert "Section 3" in t_data["pages"][1]["text"]

    # 2. Batch rule approval
    rules = upload_resp.json()["rules"]
    rule_ids = [r["id"] for r in rules]
    batch_resp = client.post(
        f"/api/contracts/{cid}/rules/batch",
        json={"action": "approve", "rule_ids": rule_ids}
    )
    assert batch_resp.status_code == 200
    assert batch_resp.json()["updated_count"] == len(rule_ids)

    # 3. Individual rule patch
    patch_resp = client.patch(
        f"/api/contracts/{cid}/rules/{rule_ids[0]}",
        json={"status": "rejected", "rejection_reason": "Manually rejected by test auditor"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "rejected"


