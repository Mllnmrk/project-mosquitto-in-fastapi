#!/usr/bin/env python3
"""
POS MQTT Test Client
Simulates POS terminals sending transactions
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
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"✅ {self.terminal_id} connected")
        
    def connect(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()
        
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
        self.client.publish(topic, json.dumps(transaction), qos=1)
        print(f"💰 {self.terminal_id} sent transaction: {transaction['id']}")
        return transaction
    
    def send_heartbeat(self):
        """Send status heartbeat"""
        heartbeat = {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "battery_level": random.randint(20, 100),
            "version": "2.1.0"
        }
        
        topic = f"{self.base_topic}/heartbeat"
        self.client.publish(topic, json.dumps(heartbeat), qos=0)
        print(f"💓 {self.terminal_id} heartbeat")
    
    def send_alert(self, message: str, severity: str = "warning"):
        """Send alert"""
        alert = {
            "id": str(uuid.uuid4()),
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"{self.base_topic}/alerts"
        self.client.publish(topic, json.dumps(alert), qos=1)
        print(f"🚨 {self.terminal_id} alert: {message}")


def main():
    # Simulate multiple terminals
    terminals = [
        POSTerminalSimulator("store001", "terminal03"),
        POSTerminalSimulator("store001", "terminal04"),
        POSTerminalSimulator("store002", "terminal01"),
    ]
    
    for t in terminals:
        t.connect()
    
    print("\n--- POS Terminal Simulator ---")
    print("1. Send random transactions")
    print("2. Send heartbeats")
    print("3. Send alert")
    print("4. Simulate high traffic")
    print("5. Exit")
    
    while True:
        choice = input("\nSelect: ")
        
        if choice == "1":
            for t in terminals:
                t.send_transaction()
                time.sleep(0.1)
                
        elif choice == "2":
            for t in terminals:
                t.send_heartbeat()
                
        elif choice == "3":
            tid = int(input(f"Terminal (0-{len(terminals)-1}): "))
            msg = input("Message: ")
            sev = input("Severity (info/warning/critical): ") or "warning"
            terminals[tid].send_alert(msg, sev)
            
        elif choice == "4":
            print("Simulating high traffic (10 transactions)...")
            for _ in range(10):
                random.choice(terminals).send_transaction()
                time.sleep(0.2)
                
        elif choice == "5":
            break
    
    for t in terminals:
        t.client.loop_stop()
        t.client.disconnect()


if __name__ == "__main__":
    main()