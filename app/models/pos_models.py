from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
import uuid


class POSTransaction(BaseModel):
    """POS Transaction Message Model"""
    model_config = {"extra": "allow"}
    
    id: Optional[str] = Field(None, description="Unique transaction UUID")
    quantity: Optional[str] = Field("0", description="Item quantity")
    price: Optional[str] = Field("0", description="Unit price")
    discount: Optional[str] = Field("0", description="Discount amount")
    vat: Optional[str] = Field("0", description="VAT amount")
    
    # Metadata (added by system)
    store_id: Optional[str] = None
    terminal_id: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    def calculate_total(self) -> Decimal:
        """Calculate total transaction amount"""
        try:
            qty = Decimal(str(self.quantity or '0'))
            price = Decimal(str(self.price or '0'))
            discount = Decimal(str(self.discount or '0'))
            vat = Decimal(str(self.vat or '0'))
            
            subtotal = (qty * price) - discount
            total = subtotal + vat
            return total.quantize(Decimal('0.01'))
        except (ValueError, TypeError, Exception):
            return Decimal('0.00')


class POSHeartbeat(BaseModel):
    """POS Terminal Heartbeat"""
    model_config = {"extra": "allow"}
    terminal_id: Optional[str] = None
    store_id: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[datetime] = None
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    version: Optional[str] = None


class POSAlert(BaseModel):
    """POS Alert/Notification"""
    model_config = {"extra": "allow"}
    alert_id: Optional[str] = None
    store_id: Optional[str] = None
    terminal_id: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[datetime] = None
    resolved: bool = False


class TopicStructure(BaseModel):
    """Parsed MQTT Topic Structure"""
    root: str
    store_id: str
    terminal_id: str
    message_type: Literal["transactions", "heartbeat", "inventory", "alerts", "ack"]
    
    @classmethod
    def from_topic(cls, topic: str):
        """Parse topic string into components"""
        parts = topic.split('/')
        if len(parts) != 4:
            raise ValueError(f"Invalid topic format: {topic}")
        
        return cls(
            root=parts[0],
            store_id=parts[1],
            terminal_id=parts[2],
            message_type=parts[3]
        )