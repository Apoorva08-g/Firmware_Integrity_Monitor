# Threat Model: Firmware Integrity Monitor

## What This Protects
An ESP32 microcontroller's firmware integrity against unauthorised modification, specifically supply chain attacks where firmware is 
tampered with before or after device deployment.

## Threat Actor
External attacker with physical or supply chain access to the ESP32  before it reaches the end user.
Reference: SolarWinds (2020) where the attackers modified software during the build/distribution phase.

## What This System Detects

| Attack Scenario | Detected? | How |
|---|---|---|
| Modified firmware binary | Yes | SHA-256 mismatch |
| Added malicious function | Yes | Any byte change caught |
| C2 server strings injected | Yes | Demonstrated in simulation |
| Single byte change |  Yes | Avalanche effect of SHA-256 |

## What This System Does NOT Detect

| Limitation | Reason | Production Fix |
|---|---|---|
| Compromised Pico W | Verifier itself could be attacked | Hardware root of trust (TPM) |
| Fake hash from ESP32 | ESP32 computes its own hash | Independent flash read via JTAG/SWD |
| Replay attack | No challenge-response mechanism | Add nonce/timestamp to hash request |
| Runtime attacks | Only checks at request time | Continuous monitoring via interrupts |

## What Makes This Production Grade
- Replace UART hash reporting with direct JTAG/SWD flash reading
- Add TPM chip as hardware root of trust on verifier side
- Implement secure boot and code signing on ESP32
- Send IoC logs to SIEM (Splunk/ELK) for centralised alerting
- Write-once forensic logging for chain of custody

## MITRE ATT&CK Mapping
- T1195.002 Compromise Software Supply Chain
- T1542 Pre-OS Boot
- T1553 Subvert Trust Controls

## Real World Reference
SolarWinds 2020: Attackers compromised the build pipeline and inserted SUNBURST malware into a legitimate software update. 18,000 organisations 
installed the update. Detection took months. This project addresses the same threat at the firmware layer.
