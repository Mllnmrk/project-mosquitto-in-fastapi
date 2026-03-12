#!/usr/bin/env python3
"""
POS MQTT Performance Test Client
Simulates sending 1000 transactions and measures the overall throughput and message turn-around (push/pull) time.
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import uuid
from datetime import datetime
import threading

class POSTerminalSimulator:
    def __init__(self, store_id: str, terminal_id: str):
        self.store_id = store_id
        self.terminal_id = terminal_id
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.base_topic = f"pos/{store_id}/{terminal_id}"
        self.connected = False
        
        # Tracking metrics
        self.sent_times = {}
        self.latencies = {}  # id -> latency in seconds
        self.first_ack_time = None
        self.last_ack_time = None
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ {self.terminal_id} connected")
            # Subscribe to the ack topic to receive backend confirmations
            ack_topic = f"{self.base_topic}/ack"
            self.client.subscribe(ack_topic)
        else:
            print(f"❌ Connection failed: {rc}")
            
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            orig_id = payload.get("original_id")
            
            # If this is an ack for a transaction we sent, record the turnaround time
            if orig_id and orig_id in self.sent_times:
                current_time = time.time()
                if self.first_ack_time is None:
                    self.first_ack_time = current_time
                self.last_ack_time = current_time
                
                turnaround_time = current_time - self.sent_times[orig_id]
                self.latencies[orig_id] = turnaround_time
        except Exception as e:
            print(f"Failed to parse message: {e}")
        
    def connect(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()
        
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        
    def send_transaction(self):
        """Simulate a sale transaction"""
        txn_id = str(uuid.uuid4())
        transaction = {
            "id": txn_id,
            "quantity": str(random.randint(1, 10)),
            "price": str(round(random.uniform(10.00, 100.00), 2)),
            "discount": str(round(random.uniform(0.00, 10.00), 2)),
            "vat": str(round(random.uniform(1.00, 5.00), 2))
        }
        
        topic = f"{self.base_topic}/transactions"
        
        # Record the exact time before publishing
        self.sent_times[txn_id] = time.time()
        
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
    
    # Record overall starting time
    overall_start_time = time.time()
    push_start_time = overall_start_time
    
    for i in range(num_transactions):
        msg_info = terminal.send_transaction()
        msg_infos.append(msg_info)
        
        if (i + 1) % 100 == 0:
            print(f"Queued {i + 1} transactions...")
            
    print("\nWaiting for all messages to be published to broker...")
    # Ensure all published messages reached broker
    for msg_info in msg_infos:
        msg_info.wait_for_publish()
        
    push_end_time = time.time()
    push_duration = push_end_time - push_start_time
        
    print(f"All {num_transactions} sent to broker in {push_duration:.4f} seconds! Awaiting ACKs from backend API...")
    
    # Wait until all acks are received, max timeout (e.g., 10 seconds)
    timeout = 10
    start_wait = time.time()
    while len(terminal.latencies) < num_transactions and (time.time() - start_wait) < timeout:
        time.sleep(0.1)
        
    # Record overall ending time
    overall_end_time = time.time()
    
    duration = overall_end_time - overall_start_time
    tps = num_transactions / duration if duration > 0 else 0
    
    pull_duration = 0
    if terminal.first_ack_time and terminal.last_ack_time:
        pull_duration = terminal.last_ack_time - terminal.first_ack_time
        
    pull_wait_time = overall_end_time - push_end_time
    
    print("\n--- Performance Results ---")
    print(f"Total Transactions: {num_transactions}")
    print(f"Acks Received: {len(terminal.latencies)}")
    print(f"Push Duration: {push_duration:.4f} seconds (queueing & publishing)")
    print(f"Pull Duration: {pull_duration:.4f} seconds (from first to last ack received)")
    print(f"Pull Wait Time: {pull_wait_time:.4f} seconds (waiting after push completed)")
    print(f"Overall Completion Time: {duration:.4f} seconds")
    
    print(f"\nPush Throughput: {num_transactions / push_duration:.2f} messages/second" if push_duration > 0 else "\nPush Throughput: N/A")
    if pull_duration > 0:
        print(f"Pull Throughput: {len(terminal.latencies) / pull_duration:.2f} messages/second")
    print(f"Overall Throughput: {tps:.2f} transactions/second")
    
    if terminal.latencies:
        # Calculate push/pull round-trip time metrics
        all_lats = list(terminal.latencies.values())
        avg_lat = sum(all_lats) / len(all_lats)
        min_lat = min(all_lats)
        max_lat = max(all_lats)
        
        print("\n--- Turnaround Time (Push + Ack Pull Latency) ---")
        print(f"Average: {avg_lat*1000:.2f} ms")
        print(f"Min: {min_lat*1000:.2f} ms")
        print(f"Max: {max_lat*1000:.2f} ms")
    else:
        print("\nNo Acks received back! The backend API may be offline or slow.")
        
    terminal.disconnect()

if __name__ == "__main__":
    main()
