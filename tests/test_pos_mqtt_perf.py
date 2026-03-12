#!/usr/bin/env python3
"""
POS MQTT Performance Test Client
Simulates sending 1000 transactions and measures the overall time taken.
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import uuid
from datetime import datetime

class POSTerminalSimulator:
    def __init__(self, store_id: str, terminal_id: str):
        self.store_id = store_id
        self.terminal_id = terminal_id
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.base_topic = f"pos/{store_id}/{terminal_id}"
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ {self.terminal_id} connected")
        else:
            print(f"❌ Connection failed: {rc}")
        
    def connect(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()
        
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        
    def send_transaction(self):
        """Simulate a sale transaction"""
        transaction = {
            "id": str(uuid.uuid4()),
            "quantity": str(random.randint(1, 10)),
            "price": str(round(random.uniform(10.00, 100.00), 2)),
            "discount": str(round(random.uniform(0.00, 10.00), 2)),
            "vat": str(round(random.uniform(1.00, 5.00), 2))
        }
        
        topic = f"{self.base_topic}/transactions"
        # Publish with QoS=1 (at least once)
        msg_info = self.client.publish(topic, json.dumps(transaction), qos=1)
        return msg_info

def main():
    terminal = POSTerminalSimulator("store_perf", "term_perf_01")
    terminal.connect()
    
    # Wait for the connection to establish
    time.sleep(1)
    if not terminal.connected:
        print("Failed to connect to MQTT broker.")
        return
    
    num_transactions = 1000
    print(f"\n--- Starting simulation of {num_transactions} transactions ---")
    
    msg_infos = []
    
    # Record starting time
    start_time = time.time()
    
    for i in range(num_transactions):
        msg_info = terminal.send_transaction()
        msg_infos.append(msg_info)
        
        if (i + 1) % 100 == 0:
            print(f"Queued {i + 1} transactions...")
            
    print("\nWaiting for all messages to be published to broker...")
    
    # Ensure all published messages are acknowledged by the broker
    # Paho-MQTT's wait_for_publish() blocks until the message is sent and acknowledged
    for msg_info in msg_infos:
        msg_info.wait_for_publish()
        
    # Record ending time
    end_time = time.time()
    
    duration = end_time - start_time
    tps = num_transactions / duration if duration > 0 else 0
    
    print("\n--- Performance Results ---")
    print(f"Total Transactions: {num_transactions}")
    print(f"Total Time Taken: {duration:.4f} seconds")
    print(f"Transactions per second (TPS): {tps:.2f}")
    
    terminal.disconnect()

if __name__ == "__main__":
    main()
