# monitor.py — Firmware Integrity Monitor
# Runs on Raspberry Pi Pico W
# Requests SHA-256 hash from ESP32 over UART and compares
# against stored baseline to detect firmware tampering
# Maps to MITRE ATT&CK T1195.002 — Supply Chain Compromise

from machine import UART, Pin
import time

# UART setup — GP0=TX, GP1=RX, 9600 baud
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# Load stored baseline hash from Pico W flash
with open("baseline.txt", "r") as f:
    baseline_hash = f.read().strip()

print("Firmware Integrity Monitor started")
print("Baseline:", baseline_hash)

# Request firmware hash from ESP32
uart.write("SEND_FIRMWARE\n")
print("Waiting for hash from ESP32...")

# Receive 64 character SHA-256 hash string
received_hash = ""
timeout = time.time() + 30

while time.time() < timeout:
    if uart.any():
        data = uart.read()
        try:
            received_hash += data.decode("utf-8").strip()
        except:
            pass
        if len(received_hash) >= 64:
            break
    time.sleep(0.1)

# Take only first 64 characters (SHA-256 hex digest length)
received_hash = received_hash[:64]
print("Received hash:", received_hash)

# Compare against baseline — any mismatch = tampering detected
if received_hash == baseline_hash:
    print("STATUS: PASS — Firmware unmodified!")
else:
    print("STATUS: ALERT — Tampering detected!")
    print("Expected:", baseline_hash)
    print("Got:     ", received_hash)
