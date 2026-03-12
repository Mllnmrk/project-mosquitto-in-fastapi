import paho.mqtt.client as mqtt
import json
import logging
from typing import Callable, Dict
from datetime import datetime

from ..config import settings
from ..models.pos_models import TopicStructure, POSTransaction, POSHeartbeat, POSAlert
from ..db.memory_db import pos_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class POSMQTTClient:
    """POS-specific MQTT Client"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id="pos_gateway_api", clean_session=False)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.message_handlers: Dict[str, Callable] = {
            "transactions": self._handle_transaction,
            "heartbeat": self._handle_heartbeat,
            "inventory": self._handle_inventory,
            "alerts": self._handle_alert
        }
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ Connected to MQTT broker")
            # Subscribe to all POS topics
            self.client.subscribe(settings.POS_WILDCARD_ALL_STORES, qos=settings.MQTT_QOS)
            logger.info(f"📡 Subscribed to: {settings.POS_WILDCARD_ALL_STORES}")
        else:
            logger.error(f"❌ Connection failed: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"⚠️ Disconnected (code: {rc})")
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.debug(f"📨 Message on {topic}: {payload}")
            
            # Parse topic structure
            try:
                topic_struct = TopicStructure.from_topic(topic)
            except ValueError as e:
                logger.error(f"Invalid topic format: {e}")
                return
            
            # Route to appropriate handler
            handler = self.message_handlers.get(topic_struct.message_type)
            if handler:
                handler(payload, topic_struct)
            else:
                logger.warning(f"No handler for message type: {topic_struct.message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON payload on {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_transaction(self, payload: dict, topic: TopicStructure):
        """Process transaction message"""
        try:
            transaction = POSTransaction(**payload)
            transaction.store_id = topic.store_id
            transaction.terminal_id = topic.terminal_id
            transaction.received_at = datetime.now()
            
            pos_store.add_transaction(transaction)
            
            total = transaction.calculate_total()
            logger.info(f"💰 Transaction processed: {topic.store_id}/{topic.terminal_id} - Total: ${total}")
            
            # Acknowledge receipt (optional - publish to confirmation topic)
            self.publish(
                f"pos/{topic.store_id}/{topic.terminal_id}/ack",
                {"original_id": transaction.id, "status": "received", "total": str(total)}
            )
            
        except Exception as e:
            logger.error(f"Transaction processing failed: {e}")
    
    def _handle_heartbeat(self, payload: dict, topic: TopicStructure):
        """Process heartbeat"""
        try:
            heartbeat = POSHeartbeat(
                terminal_id=topic.terminal_id,
                store_id=topic.store_id,
                status=payload.get("status", "unknown"),
                timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.now().isoformat())),
                battery_level=payload.get("battery_level"),
                version=payload.get("version")
            )
            pos_store.update_heartbeat(heartbeat)
            logger.debug(f"💓 Heartbeat from {topic.terminal_id}: {heartbeat.status}")
        except Exception as e:
            logger.error(f"Heartbeat processing failed: {e}")
    
    def _handle_inventory(self, payload: dict, topic: TopicStructure):
        """Process inventory update"""
        logger.info(f"📦 Inventory update from {topic.terminal_id}: {payload.get('item_count', 0)} items")
        # Add inventory logic here
    
    def _handle_alert(self, payload: dict, topic: TopicStructure):
        """Process alert"""
        try:
            alert = POSAlert(
                alert_id=payload.get("id", str(datetime.now().timestamp())),
                store_id=topic.store_id,
                terminal_id=topic.terminal_id,
                severity=payload.get("severity", "info"),
                message=payload.get("message", ""),
                timestamp=datetime.now(),
                resolved=False
            )
            pos_store.add_alert(alert)
            logger.warning(f"🚨 Alert from {topic.terminal_id}: {alert.message}")
        except Exception as e:
            logger.error(f"Alert processing failed: {e}")
    
    def connect(self):
        self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, settings.MQTT_KEEPALIVE)
        self.client.loop_start()
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish(self, topic: str, message: dict, qos: int = None):
        """Publish message to topic"""
        if qos is None:
            qos = settings.MQTT_QOS
        payload = json.dumps(message)
        result = self.client.publish(topic, payload, qos=qos)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"📤 Published to {topic}")
            return True
        return False


# Global client
pos_mqtt_client = POSMQTTClient()