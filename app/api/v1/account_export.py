from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
import io
import csv
from openpyxl import Workbook

from app.database import get_db
from app.models.account import Account

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts Export"],
)

# Unified field list for both CSV & XLSX
EXPORT_FIELDS = [
    "Name",
    "Code",
    "Probability",
    "Account Partner",
    "Delivery Partner",
    "Department",
    "Unit",
    "Vertical",
    "Location",
    "Status",
    "Address Line1",
    "Address Line2",
    "City",
    "State",
    "Zip",
    "Country",
    "Contacts (Name/Email/Phone)",
]


def serialize_contacts(acc: Account) -> str:
    """Serialize contacts into Name/Email/Phone; Name2/Email2/Phone2 format."""
    if not acc.contacts:
        return ""

    parts = []
    for c in acc.contacts:
        name = c.name or ""
        email = c.email or ""
        phone = c.phone or ""
        # keep 3 segments for consistency
        parts.append(f"{name}/{email}/{phone}")
    return "; ".join(parts)


def serialize_account(acc: Account) -> dict:
    """Convert Account model into a flat dict matching EXPORT_FIELDS."""
    addr = acc.billing_address

    return {
        "Name": acc.name,
        "Code": acc.code,
        "Probability": acc.probability,
        "Account Partner": acc.account_partner,
        "Delivery Partner": acc.delivery_partner,
        "Department": acc.department.name if getattr(acc, "department", None) else None,
        "Unit": acc.unit.name if getattr(acc, "unit", None) else None,
        "Vertical": acc.vertical.name if getattr(acc, "vertical", None) else None,
        "Location": acc.location.name if getattr(acc, "location", None) else None,
        "Status": acc.status.name if getattr(acc, "status", None) else None,
        "Address Line1": addr.addressLine1 if addr else None,
        "Address Line2": addr.addressLine2 if addr else None,
        "City": addr.city if addr else None,
        "State": addr.state if addr else None,
        "Zip": addr.zip if addr else None,
        "Country": addr.countryCode if addr else None,
        "Contacts (Name/Email/Phone)": serialize_contacts(acc),
    }


@router.get("/export")
async def export_accounts(
    format: str = "xlsx",
    db: Session = Depends(get_db),
):
    """
    Export all active accounts as XLSX or CSV.

    Columns (same as import):

    Name
    Code
    Probability
    Account Partner
    Delivery Partner
    Department
    Unit
    Vertical
    Location
    Status
    Address Line1
    Address Line2
    City
    State
    Zip
    Country
    Contacts (Name/Email/Phone)
    """
    if format not in ("xlsx", "csv"):
        raise HTTPException(status_code=400, detail="format must be 'xlsx' or 'csv'")

    accounts: List[Account] = (
        db.query(Account)
        .options(
            # lookups
            selectinload(Account.department),
            selectinload(Account.unit),
            selectinload(Account.vertical),
            selectinload(Account.location),
            selectinload(Account.status),
            # address + contacts
            selectinload(Account.billing_address),
            selectinload(Account.contacts),
        )
        .filter(Account.is_deleted == False)
        .all()
    )

    rows = [serialize_account(acc) for acc in accounts]

    # Ensure we always have at least headers in export
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=EXPORT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=accounts.csv"},
        )

    # XLSX
    if format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.append(EXPORT_FIELDS)

        for row in rows:
            ws.append([row.get(col) for col in EXPORT_FIELDS])

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)

        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=accounts.xlsx"},
        )
