# POS MQTT Gateway

A **FastAPI** application that acts as a real-time gateway for Point-of-Sale (POS) transaction processing over **MQTT** (via Eclipse Mosquitto). POS terminals publish transactions, heartbeats, and alerts to an MQTT broker; this API stores them in memory and exposes REST endpoints to query the data.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [1. Install Eclipse Mosquitto (MQTT Broker)](#1-install-eclipse-mosquitto-mqtt-broker)
- [2. Configure Mosquitto](#2-configure-mosquitto)
- [3. Project Setup](#3-project-setup)
- [4. Run the Application](#4-run-the-application)
- [5. API Endpoints](#5-api-endpoints)
- [6. Testing](#6-testing)
- [7. Postman & cURL Examples](#7-postman--curl-examples)

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | ≥ 3.14 | Required by `pyproject.toml` |
| Poetry | ≥ 2.0 | Dependency manager |
| Eclipse Mosquitto | Latest | MQTT broker |

---

## 1. Install Poetry (Dependency Manager)

Poetry is used to manage Python dependencies and virtual environments for this project.

### Recommended — via `pipx` (all platforms)

[pipx](https://pipx.pypa.io/) installs Poetry in an isolated environment, which is the officially recommended approach.

```bash
# 1. Install pipx (if not already installed)
pip install pipx
pipx ensurepath

# 2. Install Poetry
pipx install poetry
```

> Restart your terminal after running `pipx ensurepath` so the PATH update takes effect.

### Windows — Standalone Installer (alternative)

Open **PowerShell** and run:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Then add Poetry to your PATH:
```
%APPDATA%\Python\Scripts
```

### macOS / Linux — Standalone Installer (alternative)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Verify Installation

```bash
poetry --version
# Poetry (version 2.x.x)
```

### Configure Poetry to create `.venv` inside the project (optional but recommended)

```bash
poetry config virtualenvs.in-project true
```

---

## 2. Install Eclipse Mosquitto (MQTT Broker)

### Windows

1. Download the **Windows installer** from the official site:  
   👉 **https://mosquitto.org/download/**

2. Run the installer (`mosquitto-x.x.x-install-win64.exe`).  
   Accept the defaults. Mosquitto will be installed to `C:\Program Files\mosquitto\`.

3. Add Mosquitto to your **PATH** (if not done automatically):
   - Open **System Properties → Environment Variables**
   - Add `C:\Program Files\mosquitto` to the `Path` variable

4. Verify the installation:
   ```cmd
   mosquitto -v
   ```

### macOS (via Homebrew)

```bash
brew install mosquitto
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
```

---

## 2. Configure Mosquitto

The project includes a `mosquitto.conf` file at the root. Populate it with the following minimal configuration to allow local connections:

```conf
listener 1883
allow_anonymous true
```

> **Note:** `allow_anonymous true` is fine for local development. For production, configure proper authentication.

---

## 3. Project Setup

### Install Dependencies

```bash
# Install all dependencies via Poetry
poetry install
```

### Environment Variables (Optional)

The app reads from a `.env` file. Create one at the project root to override defaults:

```env
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_KEEPALIVE=60
MQTT_QOS=1
MAX_TRANSACTIONS_PER_TERMINAL=1000
MAX_HEARTBEAT_AGE_MINUTES=5
```

---

## 4. Run the Application

### Step 1 — Start the Mosquitto Broker

**Windows (with config file):**
```cmd
mosquitto -c mosquitto.conf -v
```

**Windows (default, no config):**
```cmd
mosquitto -v
```

**macOS / Linux:**
```bash
mosquitto -c mosquitto.conf -v
```

> The `-v` flag enables verbose logging so you can see MQTT traffic in real time.

### Step 2 — Start the FastAPI Server

```bash
# Using Poetry (recommended)
poetry run fastapi dev app/main.py

# Or with uvicorn directly
poetry run uvicorn app.main:app --reload
```

The API will be available at:
- **API Root:** http://localhost:8000
- **Interactive Docs (Swagger UI):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 5. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info and available endpoints |
| `GET` | `/health` | Health check (MQTT connection status) |
| `GET` | `/stores/{store_id}/transactions` | List transactions for a store |
| `GET` | `/stores/{store_id}/stats` | Store statistics (totals, terminal counts) |
| `GET` | `/stores/{store_id}/terminals/status` | Terminal online/offline status |
| `POST` | `/publish` | Manually publish a message to an MQTT topic |

### MQTT Topic Structure

The app subscribes to the wildcard topic `pos/+/+/+`, which maps to:

```
pos/{store_id}/{terminal_id}/{message_type}
```

| Message Type | Example Topic | Description |
|---|---|---|
| `transactions` | `pos/store001/terminal01/transactions` | Sale transaction data |
| `heartbeat` | `pos/store001/terminal01/heartbeat` | Terminal health ping |
| `alerts` | `pos/store001/terminal01/alerts` | Alerts (warnings, criticals) |

---

## 6. Testing

Make sure both the **Mosquitto broker** and **FastAPI server** are running before executing any tests.

### test_mqtt.py — Interactive MQTT Pub/Sub Client

A standalone interactive client for testing basic MQTT publish/subscribe to general topics (`sensors/data`, `chat/room/1`).

```bash
poetry run python tests/test_mqtt.py
```

Follow the on-screen menu to publish messages and observe received messages.

---

### test_pos_mqtt.py — POS Terminal Simulator

Simulates **3 POS terminals** across 2 stores sending transactions, heartbeats, and alerts.

```bash
poetry run python tests/test_pos_mqtt.py
```

**Simulated terminals:**
- `store001 / terminal03`
- `store001 / terminal04`
- `store002 / terminal01`

**Menu options:**
1. Send random transactions to all terminals
2. Send heartbeats
3. Send an alert (with severity: `info`, `warning`, `critical`)
4. Simulate high traffic (10 burst transactions)
5. Exit

After running option `1`, query the API to see stored transactions:
```
GET http://localhost:8000/stores/store001/transactions
```

---

### test_pos_mqtt_perf.py — Performance Test (1000 Transactions)

Measures throughput and push/pull round-trip latency by sending **1000 transactions** to the broker and tracking acknowledgement times.

```bash
poetry run python tests/test_pos_mqtt_perf.py
```

**Sample output:**
```
--- Performance Results ---
Total Transactions: 1000
Push Duration: 0.8231 seconds
Pull Duration: 1.2045 seconds
Overall Throughput: 743.21 transactions/second

--- Turnaround Time (Push + Ack Pull Latency) ---
Average: 12.34 ms
Min: 4.21 ms
Max: 98.76 ms
```

---

## 7. Postman & cURL Examples

### Health Check

**cURL:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "mqtt_connected": true,
  "stores_tracked": 2,
  "terminals_online": 3
}
```

---

### Publish a Message to MQTT

Manually push a POS transaction to the broker via the REST API.

> **Note:** A complete sample payload is provided in [`payload.json`](./payload.json) at the project root. Use its contents as the request body for the examples below.

**cURL:**
```bash
curl -X POST http://localhost:8000/publish \
  -H "Content-Type: application/json" \
  -d @payload.json
```

**Postman:**
- **Method:** `POST`
- **URL:** `http://localhost:8000/publish`
- **Body → raw → JSON:** Copy and paste the contents of `payload.json` as the request body.

**Response:**
```json
{
  "status": "published",
  "topic": "pos/store001/terminal01/transactions",
  "pull_duration_ms": 0.123,
  "push_duration_ms": 1.456
}
```

---

### Get Transactions for a Store

**cURL:**
```bash
curl "http://localhost:8000/stores/store001/transactions?limit=10"
```

**cURL (filter by terminal):**
```bash
curl "http://localhost:8000/stores/store001/transactions?terminal_id=terminal01&limit=5"
```

**Postman:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/stores/store001/transactions`
- **Params:**
  - `limit` = `10`
  - `terminal_id` = `terminal01` *(optional)*


## Project Structure

```
project-mosquitto-in-fastapi/
├── app/
│   ├── main.py          # FastAPI app, routes, startup/shutdown
│   ├── config.py        # Settings (MQTT host, port, topics, etc.)
│   ├── mqtt/
│   │   ├── client.py    # MQTT client connection & publish logic
│   │   └── handlers.py  # Incoming message handlers
│   ├── models/          # Pydantic schemas and POS models
│   ├── db/              # In-memory data store
│   ├── services/        # Business logic
│   └── utils/           # Utilities
├── tests/
│   ├── test_mqtt.py           # Basic MQTT pub/sub test client
│   ├── test_pos_mqtt.py       # POS terminal simulator
│   └── test_pos_mqtt_perf.py  # Performance / throughput test
├── mosquitto.conf       # Mosquitto broker configuration
├── pyproject.toml       # Project metadata and dependencies
└── README.md
```
