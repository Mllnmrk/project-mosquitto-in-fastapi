from typing import Dict, List, Any
from datetime import datetime
from .mqtt_client import mqtt_client

class MessageStore:
    """Simple in-memory store for received messages"""
    def __init__(self, max_messages: int = 100):
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
        self.max_messages = max_messages
    
    def add(self, topic: str, message: Any):
        if topic not in self.messages:
            self.messages[topic] = []
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        self.messages[topic].append(entry)
        
        # Keep only last N messages
        self.messages[topic] = self.messages[topic][-self.max_messages:]
    
    def get(self, topic: str, last_n: int = 10) -> List[Dict[str, Any]]:
        return self.messages.get(topic, [])[-last_n:]
    
    def get_all_topics(self) -> List[str]:
        return list(self.messages.keys())

# Global message store
message_store = MessageStore()

def handle_sensor_data(payload):
    """Callback for sensor data"""
    print(f"🌡️ Processing sensor data: {payload}")
    message_store.add("sensors/data", payload)

def handle_notifications(payload):
    """Callback for notifications"""
    print(f"🔔 Processing notification: {payload}")
    message_store.add("notifications", payload)

def setup_subscriptions():
    """Setup default subscriptions"""
    mqtt_client.subscribe("sensors/data", handle_sensor_data)
    mqtt_client.subscribe("notifications", handle_notifications)
    mqtt_client.subscribe("chat/room/+", handle_chat_message)  # Wildcard subscription

def handle_chat_message(payload):
    """Callback for chat messages"""
    print(f"💬 Chat message: {payload}")
    message_store.add("chat/messages", payload)