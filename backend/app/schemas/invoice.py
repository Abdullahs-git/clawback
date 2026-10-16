"""
Pydantic v2 schemas for invoices.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class InvoiceLineItemBase(BaseModel):
    line_id: str
    invoice_number: str
    invoice_date: str
    shipment_id: str
    charge_code: str
    charge_description: Optional[str] = None
    service_level: Optional[str] = None
    origin_zip: Optional[str] = None
    destination_zip: Optional[str] = None
    zone: Optional[str] = None
    weight_actual_lbs: Optional[float] = None
    dim_length_in: Optional[float] = None
    dim_width_in: Optional[float] = None
    dim_height_in: Optional[float] = None
    billed_weight_lbs: Optional[float] = None
    published_rate: Optional[str] = None
    discount_applied_percent: Optional[str] = None
    fuel_surcharge_percent: Optional[str] = None
    amount_billed: str


class InvoiceLineItemResponse(InvoiceLineItemBase):
    id: str
    batch_id: str

    class Config:
        from_attributes = True


class InvoiceBatchSummary(BaseModel):
    id: str
    carrier_name: str
    filename: str
    uploaded_at: datetime
    total_lines: int
    total_billed_amount: str

    class Config:
        from_attributes = True


class InvoiceLinesPagination(BaseModel):
    items: List[InvoiceLineItemResponse]
    total: int
    page: int
    limit: int
