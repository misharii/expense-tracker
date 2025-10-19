from abc import ABC, abstractmethod
from typing import Optional
import re
from datetime import datetime


class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, message: str) -> bool:
        """Check if this parser can handle the message"""
        pass

    @abstractmethod
    def parse(self, message: str) -> Optional[dict]:
        """Parse the message and return transaction data"""
        pass

    @staticmethod
    def extract_amount(text: str) -> tuple[Optional[float], Optional[str]]:
        """Extract amount and currency from text"""
        # Pattern: مبلغ:SAR 100 or بمبلغ 5.80 USD
        patterns = [
            r"مبلغ[:：\s]*([A-Z]{3})\s*([\d,]+\.?\d*)",
            r"بمبلغ\s*([\d,]+\.?\d*)\s*([A-Z]{3})",
            r"مبلغ[:：\s]*([\d,]+\.?\d*)\s*([A-Z]{3})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if groups[0].isalpha():
                    currency, amount_str = groups[0], groups[1]
                else:
                    amount_str, currency = groups[0], groups[1]

                amount = float(amount_str.replace(",", ""))
                return amount, currency

        return None, None

    @staticmethod
    def extract_card_number(text: str) -> Optional[str]:
        """Extract last 4 digits of card"""
        patterns = [
            r"بطاقة[:：\s]*(\d{4})",
            r"\*(\d{4})",
            r"(\d{4})[:：]\d{2}",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Parse Arabic date format to datetime"""
        # Format: 25-10-3 22:19 or 13/10/25 20:53
        formats = [
            "%y-%m-%d %H:%M",
            "%d/%m/%y %H:%M",
            "%y-%m-%d",
            "%d/%m/%y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None