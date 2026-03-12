#!/usr/bin/env python3
"""
Standalone test script for MQTT pub/sub
Run this in a separate terminal to test publishing/subscribing
"""

import paho.mqtt.client as mqtt
import json
import time
import sys

def on_message(client, userdata, msg):
    print(f"\n📨 Received on {msg.topic}: {msg.payload.decode()}")

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to all test topics
    client.subscribe("test/#")
    client.subscribe("sensors/data")
    client.subscribe("chat/room/1")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_start()

def publish_test():
    """Interactive publish menu"""
    while True:
        print("\n--- MQTT Test Client ---")
        print("1. Publish to sensors/data")
        print("2. Publish to chat/room/1")
        print("3. Publish to custom topic")
        print("4. Exit")
        
        choice = input("Select option: ")
        
        if choice == "1":
            temp = input("Temperature: ")
            msg = {"sensor": "temp_1", "value": float(temp), "unit": "celsius"}
            client.publish("sensors/data", json.dumps(msg))
            print(f"Published: {msg}")
            
        elif choice == "2":
            user = input("Your name: ")
            text = input("Message: ")
            msg = {"user": user, "text": text, "timestamp": time.time()}
            client.publish("chat/room/1", json.dumps(msg))
            print(f"Published: {msg}")
            
        elif choice == "3":
            topic = input("Topic: ")
            message = input("Message (JSON or plain text): ")
            try:
                # Try to parse as JSON
                msg = json.loads(message)
            except:
                msg = {"text": message}
            client.publish(topic, json.dumps(msg))
            print(f"Published to {topic}: {msg}")
            
        elif choice == "4":
            break

    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    print("MQTT Test Client - Listening for messages...")
    print("Run this in multiple terminals to test pub/sub")
    try:
        publish_test()
    except KeyboardInterrupt:
        print("\nExiting...")
        client.loop_stop()
        client.disconnect()