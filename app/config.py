from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # MQTT Configuration
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_KEEPALIVE: int = 60
    MQTT_QOS: int = 1  # At least once delivery for POS transactions
    
    # POS Topic Structure
    POS_ROOT_NAMESPACE: str = "pos"
    POS_WILDCARD_ALL_STORES: str = "pos/+/+/+"  # Subscribe to all stores
    POS_WILDCARD_ALL_TERMINALS: str = "pos/store001/+/+"  # Example: specific store
    
    # API Configuration
    API_TITLE: str = "POS MQTT Gateway API"
    API_VERSION: str = "1.0.0"
    
    # Data Retention
    MAX_TRANSACTIONS_PER_TERMINAL: int = 1000
    MAX_HEARTBEAT_AGE_MINUTES: int = 5
    
    class Config:
        env_file = ".env"


settings = Settings()