from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.sql import func



class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    raw_vendor_name = Column(String(255), unique=True, nullable=False)
    real_name = Column(String(255), nullable=True)
    classification = Column(String(100), nullable=True)
    logo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="vendor")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    raw_message = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    card_last4 = Column(String(10), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    datetime = Column(DateTime, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    direction = Column(String(20), nullable=True)  # incoming/outgoing
    bank = Column(String(50), nullable=False)
    source_account = Column(String(20), nullable=True)
    destination_account = Column(String(20), nullable=True)
    fees = Column(Float, nullable=True, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vendor = relationship("Vendor", back_populates="transactions")