import paho.mqtt.client as mqtt
import json
import logging
from typing import Callable, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.client = mqtt.Client()
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.subscriptions: Dict[str, Callable] = {}
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            # Resubscribe to all topics on reconnect
            for topic in self.subscriptions.keys():
                self.client.subscribe(topic)
                logger.info(f"📡 Resubscribed to: {topic}")
        else:
            logger.error(f"❌ Connection failed with code {rc}")
    
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"📨 Received on '{topic}': {payload}")
            
            if topic in self.subscriptions:
                self.subscriptions[topic](payload)
        except json.JSONDecodeError:
            logger.warning(f"📨 Received non-JSON on '{topic}': {msg.payload.decode()}")
            if topic in self.subscriptions:
                self.subscriptions[topic](msg.payload.decode())
    
    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"⚠️ Disconnected from broker (code: {rc})")
    
    def connect(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("🔌 Disconnected from MQTT broker")
    
    def publish(self, topic: str, message: dict, qos: int = 0):
        """Publish a message to a topic"""
        payload = json.dumps(message)
        result = self.client.publish(topic, payload, qos=qos)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"📤 Published to '{topic}': {message}")
            return True
        else:
            logger.error(f"Failed to publish to '{topic}'")
            return False
    
    def subscribe(self, topic: str, callback: Callable[[Any], None], qos: int = 0):
        """Subscribe to a topic with a callback function"""
        self.subscriptions[topic] = callback
        self.client.subscribe(topic, qos=qos)
        logger.info(f"👂 Subscribed to: {topic}")
    
    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        if topic in self.subscriptions:
            del self.subscriptions[topic]
            self.client.unsubscribe(topic)
            logger.info(f"🚫 Unsubscribed from: {topic}")

# Global client instance
mqtt_client = MQTTClient()