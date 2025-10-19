from app.parsers.base import BaseParser
from typing import Optional
import re


class AlRajhiParser(BaseParser):
    BANK_NAME = "AL_RAJHI"

    TRANSACTION_TYPES = {
        "شراء": "purchase",
        "حوالة داخلية": "internal_transfer",
        "حوالة محلية": "local_transfer",
        "مدفوعات وزارة الداخلية": "government_payment",
        "راتب": "salary",
    }

    def can_parse(self, message: str) -> bool:
        keywords = ["شراء", "حوالة", "مدفوعات", "راتب"]
        has_keyword = any(keyword in message for keyword in keywords)
        has_details = any(
            x in message for x in ["من:", "لدى:", "مبلغ:", "الى:"]
        )
        return has_keyword and has_details

    def parse(self, message: str) -> Optional[dict]:
        try:
            # Normalize message (join multi-line into single line)
            message = " ".join(message.split())

            # Determine transaction type
            trans_type = self._determine_type(message)

            # Extract common fields
            amount, currency = self.extract_amount(message)
            if not amount:
                return None

            card_number = self.extract_card_number(message)
            vendor_name = self._extract_vendor(message)
            date_str = self._extract_date(message)
            transaction_date = self.parse_date(date_str) if date_str else None

            if not transaction_date:
                return None

            # Extract accounts
            source_acc = self._extract_account(message, "من:")
            dest_acc = self._extract_account(message, "الى:")

            # Extract fees if present
            fees = self._extract_fees(message)

            # Determine direction
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
                "fees": fees,
            }
        except Exception as e:
            print(f"Al Rajhi parsing error: {str(e)}")
            return None

    def _determine_type(self, message: str) -> str:
        for arabic_type, english_type in self.TRANSACTION_TYPES.items():
            if arabic_type in message:
                return english_type
        return "unknown"

    def _extract_vendor(self, message: str) -> Optional[str]:
        # Pattern: لدى:STC Pay or الجهة:المخالفات
        patterns = [
            r"لدى[:：\s]+([^\s]+(?:\s+[A-Z]+)*)",  # لدى:RAYG CO
            r"الجهة[:：\s]+([^\s]+[^\s]*?)(?:\s+الخدمة:|$)",
            r"من[:：\s]+([^\s]+(?:\s+[^\s]+)*?)(?:\s+في:|من:\d|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                vendor = match.group(1).strip()
                # Exclude account numbers and common non-vendor words
                if not re.match(r"^\d+$", vendor) and len(vendor) > 2:
                    # Clean up
                    vendor = re.sub(r"\s+في$", "", vendor)
                    return vendor

        return None

    def _extract_date(self, message: str) -> Optional[str]:
        # Pattern: في:25-10-3 23:00 or في 25-10-3 23:00
        match = re.search(r"في[:：\s]+([\d\-]+\s+[\d:]+)", message)
        return match.group(1) if match else None

    def _extract_account(self, message: str, keyword: str) -> Optional[str]:
        pattern = rf"{keyword}[:：\s]*(\d{{4}})"
        match = re.search(pattern, message)
        return match.group(1) if match else None

    def _extract_fees(self, message: str) -> float:
        # Pattern: الرسوم:SAR 0.58
        match = re.search(r"الرسوم[:：\s]*SAR\s*([\d.]+)", message)
        return float(match.group(1)) if match else 0

    def _determine_direction(
        self, message: str, trans_type: str
    ) -> Optional[str]:
        if "واردة" in message or trans_type == "salary":
            return "incoming"
        elif "صادرة" in message:
            return "outgoing"
        elif trans_type == "purchase" or trans_type == "government_payment":
            return "outgoing"
        return None