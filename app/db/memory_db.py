from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

from ..models.pos_models import POSTransaction, POSHeartbeat, POSAlert


class POSDataStore:
    """Thread-safe in-memory store for POS data"""
    
    def __init__(self, max_transactions: int = 1000):
        self._transactions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_transactions))
        self._heartbeats: Dict[str, POSHeartbeat] = {}
        self._alerts: Dict[str, List[POSAlert]] = defaultdict(list)
        self._store_stats: Dict[str, dict] = defaultdict(lambda: {
            "total_sales": 0,
            "transaction_count": 0,
            "last_transaction": None
        })
        self._lock = threading.RLock()
    
    def add_transaction(self, transaction: POSTransaction):
        """Store a new transaction"""
        with self._lock:
            key = f"{transaction.store_id}/{transaction.terminal_id}"
            transaction.processed_at = datetime.now()
            self._transactions[key].append(transaction)
            
            # Update stats
            stats = self._store_stats[transaction.store_id]
            stats["total_sales"] += float(transaction.calculate_total())
            stats["transaction_count"] += 1
            stats["last_transaction"] = transaction.received_at
    
    def get_transactions(self, store_id: str, terminal_id: Optional[str] = None, 
                        limit: int = 100) -> List[POSTransaction]:
        """Get transactions for a store/terminal"""
        with self._lock:
            if terminal_id:
                key = f"{store_id}/{terminal_id}"
                return list(self._transactions[key])[-limit:]
            else:
                # Get all terminals for store
                result = []
                for key, deq in self._transactions.items():
                    if key.startswith(f"{store_id}/"):
                        result.extend(deq)
                return sorted(result, key=lambda x: x.received_at or datetime.min, reverse=True)[:limit]
    
    def update_heartbeat(self, heartbeat: POSHeartbeat):
        """Update terminal heartbeat"""
        with self._lock:
            key = f"{heartbeat.store_id}/{heartbeat.terminal_id}"
            self._heartbeats[key] = heartbeat
    
    def get_terminal_status(self, store_id: str, terminal_id: Optional[str] = None):
        """Get status of terminals"""
        with self._lock:
            if terminal_id:
                key = f"{store_id}/{terminal_id}"
                hb = self._heartbeats.get(key)
                if hb:
                    is_online = (datetime.now() - hb.timestamp) < timedelta(minutes=5)
                    return {"terminal_id": terminal_id, "online": is_online, "last_seen": hb.timestamp}
                return {"terminal_id": terminal_id, "online": False, "last_seen": None}
            else:
                # All terminals for store
                result = []
                for key, hb in self._heartbeats.items():
                    if key.startswith(f"{store_id}/"):
                        is_online = (datetime.now() - hb.timestamp) < timedelta(minutes=5)
                        result.append({
                            "terminal_id": hb.terminal_id,
                            "online": is_online,
                            "last_seen": hb.timestamp,
                            "status": hb.status
                        })
                return result
    
    def add_alert(self, alert: POSAlert):
        """Store an alert"""
        with self._lock:
            key = f"{alert.store_id}/{alert.terminal_id}"
            self._alerts[key].append(alert)
    
    def get_store_stats(self, store_id: str):
        """Get store statistics"""
        with self._lock:
            return self._store_stats[store_id].copy()


# Global instance
pos_store = POSDataStore()