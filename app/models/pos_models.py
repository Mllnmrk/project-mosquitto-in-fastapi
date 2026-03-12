from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
import uuid


class POSTransaction(BaseModel):
    """POS Transaction Message Model"""
    id: str = Field(..., description="Unique transaction UUID")
    quantity: str = Field(..., description="Item quantity")
    price: str = Field(..., description="Unit price")
    discount: str = Field(..., description="Discount amount")
    vat: str = Field(..., description="VAT amount")
    
    # Metadata (added by system)
    store_id: Optional[str] = None
    terminal_id: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    @field_validator('id')
    @classmethod
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    @field_validator('quantity', 'price', 'discount', 'vat')
    @classmethod
    def validate_numeric_string(cls, v):
        try:
            Decimal(v)
            return v
        except:
            raise ValueError(f'Must be a valid numeric string')
    
    def calculate_total(self) -> Decimal:
        """Calculate total transaction amount"""
        qty = Decimal(self.quantity)
        price = Decimal(self.price)
        discount = Decimal(self.discount)
        vat = Decimal(self.vat)
        
        subtotal = (qty * price) - discount
        total = subtotal + vat
        return total.quantize(Decimal('0.01'))


class POSHeartbeat(BaseModel):
    """POS Terminal Heartbeat"""
    terminal_id: str
    store_id: str
    status: Literal["online", "offline", "maintenance"]
    timestamp: datetime
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    version: Optional[str] = None


class POSAlert(BaseModel):
    """POS Alert/Notification"""
    alert_id: str
    store_id: str
    terminal_id: str
    severity: Literal["info", "warning", "critical"]
    message: str
    timestamp: datetime
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