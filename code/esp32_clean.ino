// esp32_clean.ino — Clean Firmware (Known Good State)
// Runs on ESP32 DevKit v1
// Computes SHA-256 hash of own flash memory using mbedtls
// Sends 64 character hash string to Pico W over UART on request
// This is the UNMODIFIED baseline firmware
// Maps to MITRE ATT&CK T1195.002 — Supply Chain Compromise

#include <Arduino.h>
#include <esp_flash.h>
#include "mbedtls/md.h"

void setup() {
  Serial.begin(115200);   // USB serial for debugging
  Serial2.begin(9600, SERIAL_8N1, 16, 17); // UART2: RX=GPIO16, TX=GPIO17
  Serial.println("ESP32 ready...");
}

void loop() {
  // Wait for SEND_FIRMWARE request from Pico W
  if (Serial2.available()) {
    String request = Serial2.readStringUntil('\n');
    request.trim();
    
    if (request == "SEND_FIRMWARE") {
      Serial.println("Request received - computing hash...");
      
      // Initialise SHA-256 context using mbedtls
      mbedtls_md_context_t ctx;
      mbedtls_md_init(&ctx);
      mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 0);
      mbedtls_md_starts(&ctx);
      
      // Read flash memory in 256 byte chunks and hash progressively
      uint8_t buffer[256];
      uint32_t flash_size = 0x11000; // 69632 bytes
      
      for (uint32_t addr = 0; addr < flash_size; addr += 256) {
        esp_flash_read(esp_flash_default_chip, buffer, addr, 256);
        mbedtls_md_update(&ctx, buffer, 256);
      }
      
      // Finalise hash and get 32 byte digest
      uint8_t hash[32];
      mbedtls_md_finish(&ctx, hash);
      mbedtls_md_free(&ctx);
      
      // Convert to 64 character hex string
      String hashStr = "";
      for (int i = 0; i < 32; i++) {
        if (hash[i] < 16) hashStr += "0";
        hashStr += String(hash[i], HEX);
      }
      
      // Send hash to Pico W over UART
      Serial.println("Hash: " + hashStr);
      Serial2.println(hashStr);
    }
  }
}
