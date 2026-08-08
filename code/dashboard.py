# dashboard.py — Firmware Integrity Monitor Web Dashboard
# Runs on Raspberry Pi Pico W
# Connects to WiFi, serves live status page showing firmware
# integrity check results and alert history
# Maps to MITRE ATT&CK T1195.002 — Supply Chain Compromise

import network
import socket
import time
from machine import UART, Pin

# WiFi credentials — stored in secrets.py (not uploaded to GitHub)
from secrets import SSID, PASSWORD

# UART setup — communicates with ESP32 over serial
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# Load known-good baseline hash from Pico W flash memory
with open("baseline.txt", "r") as f:
    baseline_hash = f.read().strip()

# Global status variables updated on each firmware check
status = "UNKNOWN"
last_check = "Never"
received_hash = "None"
alert_history = []  # stores all alerts as Indicators of Compromise

def connect_wifi():
    """Connect Pico W to WiFi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting to WiFi...")
    while not wlan.isconnected():
        time.sleep(1)
        print(".")
    ip = wlan.ifconfig()[0]
    print("Connected! IP:", ip)
    return ip

def check_firmware():
    """Request SHA-256 hash from ESP32 and compare against baseline"""
    global status, last_check, received_hash
    
    # Send request to ESP32 over UART
    uart.write("SEND_FIRMWARE\n")
    received = ""
    timeout = time.time() + 30
    
    # Wait for 64 character hash string response
    while time.time() < timeout:
        if uart.any():
            data = uart.read()
            received += data.decode("utf-8").strip()
            if len(received) >= 64:
                break
        time.sleep(0.1)
    
    received_hash = received[:64]
    last_check = str(time.time())
    
    # Compare received hash against stored baseline
    if received_hash == baseline_hash:
        status = "PASS"
    else:
        # Hash mismatch — firmware has been tampered
        status = "ALERT"
        alert_history.append({
            "time": last_check,
            "expected": baseline_hash,
            "got": received_hash
        })
    
    return status

def web_page():
    """Generate HTML dashboard page"""
    # Set colour based on current status
    if status == "PASS":
        color = "#2ecc71"
        status_text = "PASS: Firmware Unmodified"
    elif status == "ALERT":
        color = "#e74c3c"
        status_text = "ALERT!! Tampering Detected!"
    else:
        color = "#f39c12"
        status_text = "? UNKNOWN — Not checked yet"
    
    # Build alert history HTML — each alert is an IoC
    alerts_html = ""
    if alert_history:
        for alert in alert_history:
            alerts_html += f"""
            <div class='alert-item'>
                <p><b>Time:</b> {alert['time']}</p>
                <p><b>Expected:</b> {alert['expected']}</p>
                <p><b>Got:</b> {alert['got']}</p>
                <p><b>MITRE:</b> T1195.002: Supply Chain Compromise</p>
            </div>
            """
    else:
        alerts_html = "<p>No alerts recorded.</p>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Firmware Integrity Monitor</title>
        <meta http-equiv='refresh' content='10'>
        <style>
            body {{ font-family: Arial; margin: 40px; background: #1a1a2e; color: #eee; }}
            h1 {{ color: #00d4ff; }}
            .status-box {{ 
                background: {color}; 
                padding: 20px; 
                border-radius: 10px; 
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .info-box {{ background: #16213e; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            .alert-item {{ background: #e74c3c22; border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
            button {{ background: #00d4ff; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px; }}
        </style>
    </head>
    <body>
        <h1>Firmware Integrity Monitor</h1>
        <h3>Hardware-based Supply Chain Attack Detector</h3>
        
        <div class='status-box'>{status_text}</div>
        
        <div class='info-box'>
            <p><b>Last Check:</b> {last_check}</p>
            <p><b>Baseline Hash:</b> {baseline_hash}</p>
            <p><b>Received Hash:</b> {received_hash}</p>
            <p><b>MITRE ATT&CK:</b> T1195.002: Supply Chain Compromise</p>
        </div>
        
        <h2>Alert History</h2>
        {alerts_html}
        
        <br>
        <form action='/check'>
            <button type='submit'>Run Manual Check</button>
        </form>
        
        <p><i>Page auto-refreshes every 10 seconds</i></p>
    </body>
    </html>
    """
    return html

# Connect to WiFi network
ip = connect_wifi()

# Run initial firmware integrity check on startup
print("Running initial check...")
check_firmware()
print("Status:", status)

# Start web server on port 80
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print(f"Dashboard running at http://{ip}")

# Main loop — serve dashboard and handle check requests
while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode("utf-8")
    
    # Trigger fresh firmware check if manual button pressed
    if "/check" in request:
        check_firmware()
    
    response = web_page()
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
    conn.send(response)
    conn.close()
