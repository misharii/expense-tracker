from sqlalchemy.orm import Session
from app import models, schemas
from app.parsers.alrajhi import AlRajhiParser
from app.parsers.snb import SNBParser
from typing import Optional


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.parsers = [AlRajhiParser(), SNBParser()]

    def get_or_create_vendor(self, vendor_name: str) -> Optional[int]:
        """Get existing vendor or create new one"""
        if not vendor_name:
            return None

        vendor = (
            self.db.query(models.Vendor)
            .filter(models.Vendor.raw_vendor_name == vendor_name)
            .first()
        )

        if not vendor:
            vendor = models.Vendor(raw_vendor_name=vendor_name)
            self.db.add(vendor)
            self.db.commit()
            self.db.refresh(vendor)

        return vendor.id

    def parse_and_save_message(self, message: str) -> dict:
        """Parse a single message and save to DB"""
        message = message.strip()
        if not message:
            return {"success": False, "error": "Empty message"}

        # Try each parser
        for parser in self.parsers:
            if parser.can_parse(message):
                parsed_data = parser.parse(message)

                if parsed_data:
                    # Get or create vendor
                    vendor_id = None
                    if parsed_data.get("vendor_name"):
                        vendor_id = self.get_or_create_vendor(
                            parsed_data["vendor_name"]
                        )

                    # Create transaction
                    transaction = models.Transaction(
                        raw_message=parsed_data["raw_message"],
                        amount=parsed_data["amount"],
                        currency=parsed_data["currency"],
                        card_last4=parsed_data.get("card_last4"),
                        vendor_id=vendor_id,
                        datetime=parsed_data["datetime"],
                        transaction_type=parsed_data["transaction_type"],
                        direction=parsed_data.get("direction"),
                        bank=parsed_data["bank"],
                        source_account=parsed_data.get("source_account"),
                        destination_account=parsed_data.get(
                            "destination_account"
                        ),
                        fees=parsed_data.get("fees", 0),
                    )

                    self.db.add(transaction)
                    self.db.commit()

                    return {
                        "success": True,
                        "vendor_name": parsed_data.get("vendor_name"),
                    }

        return {"success": False, "error": "No parser matched", "message": message}