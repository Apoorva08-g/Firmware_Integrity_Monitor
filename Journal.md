# Journal

## Week 1 
### What I did:
- Read about the MITRE ATT&CK T1195 (Supply Chain Compromise)
- Learned about SolarWinds attack — attackers inserted malicious 
  code into a software update before it reached 18,000 organisations
- Learned UART communication basics — TX/RX crossover, baud rate
- Studied firmware and flash memory concepts
- Installed MicroPython, Thonny, Arduino IDE

### Key concepts learned:
- UART: TX of one device connects to RX of the other
- Firmware lives in flash memory and runs before any OS
- Supply chain attacks happen before the product reaches the victim

##  Week 2 & 3

### What I did:
- Wired ESP32 and Pico W together using jumper wires
- Flashed MicroPython onto Pico W using BOOTSEL method
- Wrote and uploaded UART test code on ESP32
- Wrote UART receiver code on Pico W
- Successfully received "HELLO FROM ESP32" on Pico W
- Dumped ESP32 flash memory using esptool.py
- Generated SHA-256 baseline hash of clean firmware
- Stored baseline hash on Pico W flash as baseline.txt
- Wrote main monitor.py on Pico W
- Achieved first PASS status

### Problems hit and fixed:

**Problem 1: Breadboard centre gap**
- Symptom: Pico W receiving no data from ESP32
- Cause: Male ends of jumper wires were on opposite sides of the breadboard centre gap, not electrically connected
- Fix: Removed breadboard entirely, joined male ends directly together and taped them
- Lesson: Always verify physical connections before debugging software

**Problem 2: ESP32 boot mode error**
- Symptom: esptool.py giving "Wrong boot mode detected (0x13)"
- Cause: ESP32 boots into running mode by default, needs to be manually put into download mode for flashing
- Fix: Hold BOOT button on ESP32 when dots appear during upload
- Lesson: Microcontrollers have hardware boot modes fundamental to embedded security work

**Problem 3: esptool.py not recognised**
- Symptom: esptool.py is not recognized as internal or external command
- Cause: Python packages not always added to Windows PATH
- Fix: Use python -m esptool instead of esptool.py directly
- Lesson: Understanding how OS finds executables, relevant to malware that hides by manipulating PATH

**Problem 4: spi_flash_read not declared**
- Symptom: Arduino compilation error on flash read function
- Cause: Function deprecated in newer ESP32 Arduino library
- Fix: Switched to esp_flash_read with esp_flash.h header
- Lesson: Libraries change over time — always check version compatibility

**Problem 5: MicroPython hexdigest error**
- Symptom: AttributeError: sha256 object has no attribute hexdigest
- Cause: MicroPython is stripped down — hexdigest() does not exist
- Fix: Used h.digest() then manually converted bytes to hex string
- Lesson: Embedded environments have constraints — cannot assume 
  standard library functions exist

**Problem 6: MemoryError on Pico W**
- Symptom: memory allocation failed, allocating 160769 bytes
- Cause: Trying to store entire firmware binary in Pico W RAM (only 264KB)
- Fix: Switched to chunk-based streaming hashing — hash data as it arrives instead of storing it all
- Lesson: Memory constraints are fundamental to IoT security, same boundary issues attackers exploit in buffer overflows

**Problem 7: Hash mismatch due to data size**
- Symptom: ALERT every time even with clean firmware
- Cause: Baseline hash created from full 4MB dump but ESP32 only sending fraction over UART, hashing different amounts
- Fix: Regenerated baseline from same byte count as what ESP32 sends
- Lesson: Consistency is critical in integrity checking, any difference in input produces false positives

**Problem 8: COM port busy error**
- Symptom: Could not open COM5, access denied, PermissionError
- Cause: Arduino Serial Monitor was holding the COM port
- Fix: Close Serial Monitor before running esptool commands
- Lesson: Only one process can hold a serial port at a time

**Problem 9: Timeout too short**
- Symptom: Only 288 bytes received out of expected 3424
- Cause: Pico W timing out before all data arrived over UART
- Fix: Reduced baud rate to 9600, smaller 64 byte chunks, added delay(200) between chunks on ESP32
- Lesson: UART has no flow control — sender can outpace receiver causing data loss. Same reason TLS exists.

### Code changes made this session:
- ESP32 baud rate: 115200 → 9600 (more reliable transfer)
- ESP32 chunk size: 256 bytes → 64 bytes (more stable)
- Added delay(200) between chunks on ESP32
- Pico timeout increased from 10s → 30s → 60s
- Baseline hash regenerated multiple times as data size was refined


## Week 4

### What I did:
- Simulated firmware tampering by adding malicious C2 server strings to ESP32 code, simulates supply chain implant
- Discovered firmware difference starts at byte 65540, beyond our initial read range
- Increased flash read size to cover the difference
- Switched architecture: ESP32 now computes SHA-256 internally using mbedtls library and sends only 64 character hash over UART
- This solved all timing and consistency issues permanently
- Achieved reliable PASS with clean firmware
- Achieved reliable ALERT with tampered firmware

### Key architecture decision:
- Original approach: ESP32 sends raw flash bytes over UART,  Pico hashes them
- Problem: Timing inconsistencies, memory errors, different amounts received each run
- Final approach: ESP32 hashes internally, sends only 64 character string to Pico W
- Result: Reliable, consistent, no memory issues

### Problems hit and fixed:

**Problem 10: Hash changing every recompile**
- Symptom: Different hash produced every time Arduino sketch uploaded
- Cause: Compiler embeds timestamps and metadata into binary, same source code produces slightly different binary each compile
- Fix: ESP32 computes hash internally — only hash string travels over UART, eliminating raw binary transfer entirely
- Lesson: Binary reproducibility is why production firmware uses code signing, cryptographic signature proves firmware is unchanged 
  regardless of when it was compiled

**Problem 11: UnicodeError on Pico W**
- Symptom: UnicodeError when decoding UART data
- Cause: Raw flash bytes contain non-UTF8 characters that MicroPython cannot decode as text
- Fix: Switched to ESP32-side hashing — only readable text hash string sent over UART

**Problem 12 — Tamper not detected in first 65540 bytes**
- Symptom: compare_firmware.py showed files identical
- Cause: Malicious function compiled into flash beyond our read range
- Fix: Increased flash read size to 0x11000 to cover byte 65540

### Tamper simulation details:
- Added hardcoded C2 server address: http://malicious-attacker.com/exfil
- Added stolen data string: DEVICE_ID_12345_SECRET_KEY_ABCDEF
- Added exfiltrate_data() function called silently at boot
- Maps to MITRE ATT&CK T1195.002 — Supply Chain Compromise
- Real world parallel: SolarWinds SUNBURST malware inserted 
  into legitimate update package

### Final baseline hash:
a39a77fd06cac152f6ca696cdfc13c8998a6433eec3250e964012c197ab0b037

---

## Week 5 (WiFi Dashboard)

### What I did:
- Built WiFi web dashboard served by Pico W using MicroPython socket library
- Dashboard shows live status, baseline hash, received hash, alert history
- Page auto-refreshes every 10 seconds
- Manual check button triggers fresh firmware verification
- Green UI for PASS, red UI for ALERT
- Took 4 demo screenshots:
  - Terminal PASS
  - Terminal ALERT  
  - Browser dashboard green PASS
  - Browser dashboard red ALERT

### Problems hit and fixed:

**Problem 13: EADDRINUSE error**
- Symptom: OSError Errno 98 EADDRINUSE when restarting dashboard
- Cause: Port 80 still held from previous run not properly closed
- Fix: Added s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

**Problem 14: Factory test firmware flashed accidentally**
- Symptom: ESP32 sending "Factory test app partition" instead of hash
- Cause: Used esptool write-flash with raw dump file which overwrote Arduino sketch with factory partition data
- Fix: Always use Arduino IDE to upload sketches, never esptool write-flash for Arduino projects
- Lesson: Raw flash dumps include bootloader and partition table, not interchangeable with compiled Arduino sketches

### Project summary:
- 5 weeks from zero hardware knowledge to working supply chain attack detector
- 14 distinct bugs debugged across hardware, firmware, and software layers
- Full stack: physical wiring → UART protocol → SHA-256 cryptography 
  → MicroPython → WiFi networking → web dashboard
- Mapped to MITRE ATT&CK T1195.002 and NCSC supply chain guidance
- Built for SOC Analyst portfolio — UK job market

### Key learning outcomes:
- SHA-256 hashing and avalanche effect
- UART serial communication and flow control
- Firmware and flash memory architecture
- MicroPython memory constraints and streaming hashing
- Hardware boot modes (ESP32 download mode vs running mode)
- Binary reproducibility and code signing concepts
- Real debugging methodology across full hardware/software stack
- Threat modelling, what a system detects and what it misses
