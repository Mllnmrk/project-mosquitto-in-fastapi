from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class TransactionResponse(BaseModel):
    id: str
    store_id: str
    terminal_id: str
    quantity: str
    price: str
    discount: str
    vat: str
    total: str
    received_at: Optional[datetime]
    processed_at: Optional[datetime]


class PublishRequest(BaseModel):
    topic: str  # e.g., "pos/store001/terminal03/transactions"
    message: Dict[str, Any]
    qos: Optional[int] = 1


class StoreStatsResponse(BaseModel):
    store_id: str
    total_sales: float
    transaction_count: int
    last_transaction: Optional[datetime]
    active_terminals: int
    offline_terminals: int


class TerminalStatusResponse(BaseModel):
    terminal_id: str
    online: bool
    last_seen: Optional[datetime]
    status: Optional[str]