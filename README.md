# MDEBacnet


MDEBacnet is a **local BACnet/IP simulation and testing framework** used to stand up multiple BACnet devices, expose points (analog), and validate communication with external BACnet clients (ex: Ignition, other BACnet stacks, or test scripts).

The project is designed to:

* Run **multiple BACnet devices on different UDP ports**
* Simulate real control-system data (tank levels, pressures, switches, etc.)
* Allow **parallel testing** against tools like Ignition without collisions
* Be easy to launch, stop, and reset during development

---

## High‑Level Architecture

```
┌────────────┐      BACnet/IP     ┌────────────────┐
│ Ignition   │  <──────────────>  │ Python Device  │
│ / Client   │                    │ (Port 47809)   │
└────────────┘                    └────────────────┘
                                  ┌────────────────┐
                                  │ Python Device  │
                                  │ (Port 47810)   │
                                  └────────────────┘
```

Each Python process:

* Hosts **one BACnet device**
* Listens on a **unique UDP port**
* Uses a **unique device instance number**
* Exposes BACnet objects backed by Python state

---

## Repository Structure

```
MDEBacnet/
│
├── RunScripts/            # 🔑 Main launcher (starts all devices)
    ├──  runAll.py         # Runs All the scripts from the other folders
├── PPF/
    ├──  PPFServer.py      # Creates a Bacnet Device to simulate all the values of the PPF on Port 47809
├── PadADriver/
    ├──  PadALisnter.py    # Waits for a connection for the VSA vm and ingests those values into a shared /tmp file
    ├──  PadAServer.py     # Sets up a Bacnet Device to read from the /tmp values, decode them and send over UDP via 47810
├── OnVM\
    ├──  mars-monitor.py   # An adapted version of the mars-10.py file that runs the simulator and sends over the network, must be on the VM and connected via VPN to work. Also must check current VPN provided IP!
├── requirements.txt
└── README.md
```

---

## Core Concepts

### 1. One Device = One Process

Each BACnet device **must**:

* Run in its **own Python process**
* Bind to a **unique UDP port**
* Use a **unique BACnet device instance ID**

Example:

| Device                             | UDP Port   | Device Instance |
| -----------------------------------| ---------- | --------------- |
| Device A   (Ignition Bacnet Driver)| 47808      | IDK             |
| Device B   (PPFServer)             | 47809      | 3001            |
| Device C   (PadAServer             | 47810      | 3002            |

⚠️ **Duplicate device instance IDs WILL cause undefined behavior** (clients may connect to the wrong device).

---

### 2. BACnet Objects

Each device defines BACnet objects such as:

* `AnalogInputObject`
* `AnalogDeviceObject`


# IN the VM
These objects are **backed by Python attributes** that update over time or via external control.

Example mapping:

```python
CB7 Analog In 04 Mon  →  sensor_dp_mon
CB7 Discrete In 03   →  sw_open_vent
```

---

### 3. Simulation Models

Simulation logic currently lives in `/PPF/PPFServer.py` and is responsible for:

* Updating sensor values
* Enforcing constraints
* Mimicking real‑world behavior (levels, pressures, states)

BACnet objects simply **reflect model state**.

---

## `runAll.py` (IMPORTANT)

`runAll.py` is the **recommended way to start the system**.

What it does:

* Launches **multiple BACnet devices**
* Ensures each runs in a **separate process**
* Assigns ports correctly
* Keeps startup consistent


✅ `runAll.py` guarantees:

* Clean startup
* Predictable ports
* Repeatable testing

---

## How To Run

### 1. Create & Activate Virtual Environment

```bash
python3 -m venv bacnetenv
source bacnetenv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run ALL Devices (Recommended)

```bash
python3 runAll.py
```

This will:

* Start all BACnet devices
* Print which ports are in use
* Keep processes alive until stopped (ctrl^c)

---

### 4. Run a Single Device (Debug Only)

```bash
python3 PPFServer.py
```

⚠️ Only do this for debugging. Do **not** mix manual runs with `runAll.py`.



## Ignition Setup (Quick)

This project is designed to be tested locally using **Ignition’s BACnet/IP driver**.

### 1. Log into Ignition Gateway

Open your browser and go to:

```
http://localhost:8088
```

Log in to the **Gateway Web Interface**.

---

### 2. Create a BACnet/IP Driver

1. Go to **Config → Networking → BACnet**
2. Click **Create new BACnet/IP Driver**
3. Set:

| Field      | Value          |
| ---------- | -------------- |
| Name       | ignitionBacnet |
| Local Port | 47808          |

4. Save the driver

📌 This port must be **different** from all Python devices.

---

### 3. Create BACnet Device Connections

For each Python device:

1. Under the BACnet driver, click **Create new BACnet Device**
2. Set:

| Field                | Example                  |
| -------------------- | ------------------------ |
| Remote Address       | 127.0.0.1                |
| Remote Port          | 47809 (or 47810, etc)    |
| Remote Device Number | 2001 (must match Python) |

3. Save and wait for status = **Connected**

Repeat for all running devices.

---

### 4. Browse Tags in Designer

1. Launch **Ignition Designer**
2. Open **Tag Browser**
3. Expand:

```
BACnet → ignitionBacnet → <Device Name>
```

4. Drag BACnet points into your project

You should now see live updates from the Python simulation.

---


---

## Connecting from Ignition (or other BACnet Client)

Example configuration:

| Field                | Value          |
| -------------------- | -------------- |
| Local Device         | ignitionBacnet |
| Remote Address       | 127.0.0.1      |
| Remote Port          | 47809          |
| Remote Device Number | 3001           |

📌 Make sure:

* Port matches the Python device
* Device number is unique
* No other process is already bound to that port

---

## Common Issues & Fixes

### ❌ Always connects to the wrong port

Cause:

* Duplicate device instance IDs

Fix:

* Ensure **every device has a unique ID**

---

### ❌ Device doesn’t respond

Checklist:

* Is the process running?
* Is the UDP port free?
* Is the device ID correct?

```bash
ps aux | grep python
netstat -anu | grep 478
```

---

### ❌ Stale BACnet behavior

Cause:

* Old Python processes still alive

Fix:

```bash
pkill -f device_
pkill -f runAll.py
```

Then restart cleanly.

---

## Design Philosophy

* **Simple > clever**
* One responsibility per process
* Explicit configuration
* Easy to kill and restart

This mirrors how real control systems isolate controllers.

---

## Notes

* BACnet/IP uses **UDP**, not TCP
* Ports matter more than IP locally
* Device instance numbers must be globally unique per network

---

## Future Extensions

* Writeable outputs
* Time‑based simulations
* Remote deployment

---

## TL;DR

```bash
# setup
python3 -m venv bacnetenv
source bacnetenv/bin/activate
pip install -r requirements.txt

# run everything
python3 runAll.py
```
This is the only command you should need 90% of the time.













