from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from decimal import Decimal
import time

from .config import settings
from .mqtt.client import pos_mqtt_client
from .db.memory_db import pos_store
from .models.schemas import (
    TransactionResponse, PublishRequest, StoreStatsResponse, 
    TerminalStatusResponse
)
from .models.pos_models import POSTransaction
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Real-time POS Transaction Processing Gateway"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    pos_mqtt_client.connect()

@app.on_event("shutdown")
async def shutdown():
    pos_mqtt_client.disconnect()

@app.get("/")
async def root():
    return {
        "service": "POS MQTT Gateway",
        "version": settings.API_VERSION,
        "mqtt_broker": f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}",
        "endpoints": [
            "GET /stores/{store_id}/transactions",
            "GET /stores/{store_id}/stats",
            "GET /stores/{store_id}/terminals/status",
            "POST /publish",
            "GET /health"
        ]
    }

@app.get("/stores/{store_id}/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    store_id: str,
    terminal_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get transactions for a store or specific terminal"""
    transactions = pos_store.get_transactions(store_id, terminal_id, limit)
    
    result = []
    for tx in transactions:
        tx_dict = tx.model_dump()
        tx_dict["total"] = str(tx.calculate_total())
        result.append(tx_dict)
    
    return result

@app.get("/stores/{store_id}/stats", response_model=StoreStatsResponse)
async def get_store_stats(store_id: str):
    """Get store statistics"""
    stats = pos_store.get_store_stats(store_id)
    terminals = pos_store.get_terminal_status(store_id)
    
    active = sum(1 for t in terminals if t["online"])
    offline = len(terminals) - active
    
    return {
        "store_id": store_id,
        **stats,
        "active_terminals": active,
        "offline_terminals": offline
    }

@app.get("/stores/{store_id}/terminals/status", response_model=List[TerminalStatusResponse])
async def get_terminal_status(
    store_id: str,
    terminal_id: Optional[str] = None
):
    """Get status of terminals in a store"""
    return pos_store.get_terminal_status(store_id, terminal_id)

@app.post("/publish")
async def publish_message(request: PublishRequest):
    """Manually publish a message to MQTT topic"""
    # --- PULL: measure time to receive and parse the request ---
    pull_start = time.perf_counter()
    topic = request.topic
    message = request.message
    qos = request.qos
    pull_end = time.perf_counter()
    pull_duration_ms = round((pull_end - pull_start) * 1000, 3)
    logger.info(f"📥 [PULL] Request received for topic '{topic}' — pull duration: {pull_duration_ms} ms")

    # --- PUSH: measure time to publish to MQTT broker ---
    push_start = time.perf_counter()
    success = pos_mqtt_client.publish(topic, message, qos)
    push_end = time.perf_counter()
    push_duration_ms = round((push_end - push_start) * 1000, 3)

    if success:
        logger.info(f"📤 [PUSH] Message published to '{topic}' — push duration: {push_duration_ms} ms")
        return {
            "status": "published",
            "topic": topic,
            "pull_duration_ms": pull_duration_ms,
            "push_duration_ms": push_duration_ms,
        }
    raise HTTPException(status_code=500, detail="Failed to publish")

@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "mqtt_connected": pos_mqtt_client.client.is_connected(),
        "stores_tracked": len(pos_store._store_stats),
        "terminals_online": sum(
            1 for store in pos_store._store_stats.keys()
            for t in pos_store.get_terminal_status(store) if t["online"]
        )
    }