from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio

from .mqtt_client import mqtt_client
from .pubsub_service import message_store, setup_subscriptions

app = FastAPI(
    title="FastAPI MQTT Pub/Sub",
    description="Simple MQTT pub/sub with Mosquitto",
    version="1.0.0"
)

# Request/Response models
class PublishRequest(BaseModel):
    topic: str
    message: Dict[str, Any]
    qos: Optional[int] = 0

class SubscriptionRequest(BaseModel):
    topic: str

@app.on_event("startup")
async def startup_event():
    """Connect to MQTT broker on startup"""
    mqtt_client.connect()
    setup_subscriptions()

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from MQTT broker on shutdown"""
    mqtt_client.disconnect()

@app.get("/")
async def root():
    return {
        "message": "FastAPI MQTT Pub/Sub Server",
        "endpoints": {
            "publish": "POST /publish",
            "subscribe": "POST /subscribe",
            "messages": "GET /messages/{topic}",
            "topics": "GET /topics"
        }
    }

@app.post("/publish")
async def publish_message(request: PublishRequest):
    """Publish a message to an MQTT topic"""
    success = mqtt_client.publish(request.topic, request.message, request.qos)
    if success:
        return {"status": "published", "topic": request.topic, "message": request.message}
    else:
        raise HTTPException(status_code=500, detail="Failed to publish message")

@app.post("/subscribe")
async def subscribe_topic(request: SubscriptionRequest):
    """Subscribe to an MQTT topic"""
    def callback(payload):
        message_store.add(request.topic, payload)
    
    mqtt_client.subscribe(request.topic, callback)
    return {"status": "subscribed", "topic": request.topic}

@app.get("/messages/{topic}")
async def get_messages(topic: str, last_n: int = 10):
    """Get last N messages from a topic"""
    messages = message_store.get(topic, last_n)
    return {
        "topic": topic,
        "count": len(messages),
        "messages": messages
    }

@app.get("/topics")
async def get_topics():
    """Get all topics with stored messages"""
    return {
        "topics": message_store.get_all_topics()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.client.is_connected()
    }