from app.parsers.base import BaseParser
from typing import Optional
import re


class SNBParser(BaseParser):
    BANK_NAME = "SNB"

    def can_parse(self, message: str) -> bool:
        keywords = ["حوالة", "شراء", "رصيد"]
        return any(keyword in message for keyword in keywords) and (
            "حساب" in message or "بطاقة" in message or "من:" in message
        )

    def parse(self, message: str) -> Optional[dict]:
        try:
            # Skip OTP messages
            if "الرقم السري" in message or "Not acept" in message:
                return None

            trans_type = self._determine_type(message)
            amount, currency = self.extract_amount(message)

            if not amount:
                return None

            card_number = self.extract_card_number(message)
            vendor_name = self._extract_vendor(message)
            date_str = self._extract_date(message)
            transaction_date = self.parse_date(date_str) if date_str else None

            source_acc = self._extract_account(message, "من:")
            dest_acc = self._extract_account(message, "إلى:")

            direction = self._determine_direction(message, trans_type)

            return {
                "raw_message": message.strip(),
                "amount": amount,
                "currency": currency,
                "card_last4": card_number,
                "vendor_name": vendor_name,
                "datetime": transaction_date,
                "transaction_type": trans_type,
                "direction": direction,
                "bank": self.BANK_NAME,
                "source_account": source_acc,
                "destination_account": dest_acc,
                "fees": 0,
            }
        except Exception as e:
            print(f"SNB parsing error: {str(e)}")
            return None

    def _determine_type(self, message: str) -> str:
        if "حوالة واردة" in message:
            return "internal_transfer"
        elif "شراء عبر الانترنت" in message or "شراء-POS" in message:
            return "purchase"
        elif "شراء عبر نقاط البيع" in message:
            return "purchase"
        elif "رصيد غير كافي" in message:
            return "insufficient_balance"
        return "unknown"

    def _extract_vendor(self, message: str) -> Optional[str]:
        patterns = [
            r"من\s+([^\s]+(?:\s+[^\s]+)*?)\s+في",
            r"عبر[:：\s]*([^\s]+(?:\s+[^\s]+)*?)(?:\s+في:|$)",
            r"مرسل[:：\s]*([^\s]+(?:\s+[^\s]+)*?)(?:\s+من:|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                vendor = match.group(1).strip()
                if (
                    not re.match(r"^\d+\*?$", vendor)
                    and vendor not in ["AL RAJHI BANK", "الولايات"]
                ):
                    return vendor

        return None

    def _extract_date(self, message: str) -> Optional[str]:
        match = re.search(r"في\s+([\d/]+\s+[\d:]+)", message)
        return match.group(1) if match else None

    def _extract_account(self, message: str, keyword: str) -> Optional[str]:
        pattern = rf"{keyword}[:：\s]*(\d{{4}})\*?"
        match = re.search(pattern, message)
        return match.group(1) if match else None

    def _determine_direction(
        self, message: str, trans_type: str
    ) -> Optional[str]:
        if "واردة" in message:
            return "incoming"
        elif trans_type == "purchase" or trans_type == "insufficient_balance":
            return "outgoing"
        return None