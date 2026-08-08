// esp32_tampered.ino — Tampered Firmware (Simulated Attack)
// Runs on ESP32 DevKit v1
// Simulates a supply chain attack where attacker has injected
// malicious code — hardcoded C2 server and data exfiltration
// Used to demonstrate ALERT detection by Pico W verifier
// Maps to MITRE ATT&CK T1195.002 — Supply Chain Compromise

#include <Arduino.h>
#include <esp_flash.h>
#include "mbedtls/md.h"

// ATTACKER INJECTED CODE — simulates supply chain implant
// In real SolarWinds attack, similar strings were embedded
// in legitimate software update packages
const char* C2_SERVER = "http://malicious-attacker.com/exfil";
const char* STOLEN_DATA = "DEVICE_ID_12345_SECRET_KEY_ABCDEF";

void exfiltrate_data() {
  // Simulates silent data exfiltration to C2 server at boot
  Serial.println("Connecting to C2...");
  Serial.println(C2_SERVER);
  Serial.println(STOLEN_DATA);
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 16, 17);
  exfiltrate_data(); // backdoor runs silently at boot
  Serial.println("ESP32 ready...");
}

void loop() {
  if (Serial2.available()) {
    String request = Serial2.readStringUntil('\n');
    request.trim();
    
    if (request == "SEND_FIRMWARE") {
      Serial.println("Request received - computing hash...");
      
      mbedtls_md_context_t ctx;
      mbedtls_md_init(&ctx);
      mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 0);
      mbedtls_md_starts(&ctx);
      
      uint8_t buffer[256];
      uint32_t flash_size = 0x11000;
      
      for (uint32_t addr = 0; addr < flash_size; addr += 256) {
        esp_flash_read(esp_flash_default_chip, buffer, addr, 256);
        mbedtls_md_update(&ctx, buffer, 256);
      }
      
      uint8_t hash[32];
      mbedtls_md_finish(&ctx, hash);
      mbedtls_md_free(&ctx);
      
      String hashStr = "";
      for (int i = 0; i < 32; i++) {
        if (hash[i] < 16) hashStr += "0";
        hashStr += String(hash[i], HEX);
      }
      
      Serial.println("Hash: " + hashStr);
      Serial2.println(hashStr);
    }
  }
}
