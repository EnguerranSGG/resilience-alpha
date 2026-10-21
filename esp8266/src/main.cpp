/**
 * RESILIENCE-ALPHA — Firmware ESP8266
 * Consigne Additionnelle 1 : indicateur LED bicolore pour le back-office MFA
 *
 * LED bicolore câblage (LED à cathode commune) :
 *   Anode verte  → D1 (GPIO5)  via résistance 220Ω
 *   Anode rouge  → D2 (GPIO4)  via résistance 220Ω
 *   Cathode      → GND
 *
 * Endpoint HTTP (port 80) :
 *   POST /led   body JSON : {"state":"<STATE>"}
 *   GET  /health           → 200 OK
 *
 * États :
 *   OFF           → LED éteinte (attente)
 *   GREEN_BLINK   → vert clignotant 500ms (visage reconnu, MDP attendu)
 *   GREEN_SOLID   → vert fixe 30s       (login réussi)
 *   RED_BLINK     → rouge clignotant 10x (MDP refusé)
 *   RED_SOLID     → rouge fixe 30s       (visage non reconnu / bloqué)
 */

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>

// ── Configuration réseau ───────────────────────────────────────────────────
#ifndef SSID_NAME
  #define SSID_NAME "RESILIENCE-G1"
#endif
#ifndef SSID_PASS
  #define SSID_PASS ""
#endif

// ── Broches LED ────────────────────────────────────────────────────────────
static constexpr uint8_t PIN_GREEN = D1;   // GPIO5
static constexpr uint8_t PIN_RED   = D2;   // GPIO4

// ── Machine à états LED ────────────────────────────────────────────────────
enum class LedState {
  OFF,
  GREEN_BLINK,
  GREEN_SOLID,
  RED_BLINK,
  RED_SOLID
};

static LedState currentState      = LedState::OFF;
static unsigned long stateEnterMs = 0;
static unsigned long lastBlinkMs  = 0;
static bool blinkOn                = false;
static int blinkCount              = 0;     // utilisé pour RED_BLINK (10x)

static constexpr unsigned long GREEN_SOLID_DURATION_MS = 30000UL;
static constexpr unsigned long RED_SOLID_DURATION_MS   = 30000UL;
static constexpr unsigned long BLINK_PERIOD_MS         = 500UL;
static constexpr int           RED_BLINK_COUNT         = 10;

// ── Serveur HTTP ───────────────────────────────────────────────────────────
ESP8266WebServer server(80);

// ── Helpers LED ────────────────────────────────────────────────────────────
void ledOff() {
  digitalWrite(PIN_GREEN, LOW);
  digitalWrite(PIN_RED,   LOW);
}

void ledGreen() {
  digitalWrite(PIN_GREEN, HIGH);
  digitalWrite(PIN_RED,   LOW);
}

void ledRed() {
  digitalWrite(PIN_GREEN, LOW);
  digitalWrite(PIN_RED,   HIGH);
}

void enterState(LedState s) {
  currentState  = s;
  stateEnterMs  = millis();
  lastBlinkMs   = millis();
  blinkOn       = false;
  blinkCount    = 0;

  switch (s) {
    case LedState::OFF:          ledOff();   break;
    case LedState::GREEN_SOLID:  ledGreen(); break;
    case LedState::RED_SOLID:    ledRed();   break;
    case LedState::GREEN_BLINK:
    case LedState::RED_BLINK:    ledOff();   break;
  }
}

// Appelé dans loop() pour gérer les timings
void updateLed() {
  unsigned long now = millis();

  switch (currentState) {

    case LedState::GREEN_SOLID:
      if (now - stateEnterMs >= GREEN_SOLID_DURATION_MS)
        enterState(LedState::OFF);
      break;

    case LedState::RED_SOLID:
      if (now - stateEnterMs >= RED_SOLID_DURATION_MS)
        enterState(LedState::OFF);
      break;

    case LedState::GREEN_BLINK:
      if (now - lastBlinkMs >= BLINK_PERIOD_MS) {
        lastBlinkMs = now;
        blinkOn = !blinkOn;
        blinkOn ? ledGreen() : ledOff();
      }
      break;

    case LedState::RED_BLINK:
      if (now - lastBlinkMs >= BLINK_PERIOD_MS) {
        lastBlinkMs = now;
        blinkOn = !blinkOn;
        if (blinkOn) {
          ledRed();
        } else {
          ledOff();
          blinkCount++;
          if (blinkCount >= RED_BLINK_COUNT)
            enterState(LedState::OFF);
        }
      }
      break;

    case LedState::OFF:
    default:
      break;
  }
}

// ── Handlers HTTP ──────────────────────────────────────────────────────────
void handleHealth() {
  String ssid = WiFi.SSID();
  String ip   = WiFi.localIP().toString();
  String body = "{\"status\":\"ok\",\"ip\":\"" + ip + "\",\"ssid\":\"" + ssid + "\"}";
  server.send(200, "application/json", body);
}

void handleLed() {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"no body\"}");
    return;
  }
  StaticJsonDocument<128> doc;
  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  if (err) {
    server.send(400, "application/json", "{\"error\":\"invalid json\"}");
    return;
  }

  const char* state = doc["state"] | "";
  String stateStr(state);

  if      (stateStr == "OFF")          enterState(LedState::OFF);
  else if (stateStr == "GREEN_BLINK")  enterState(LedState::GREEN_BLINK);
  else if (stateStr == "GREEN_SOLID")  enterState(LedState::GREEN_SOLID);
  else if (stateStr == "RED_BLINK")    enterState(LedState::RED_BLINK);
  else if (stateStr == "RED_SOLID")    enterState(LedState::RED_SOLID);
  else {
    server.send(400, "application/json", "{\"error\":\"unknown state\"}");
    return;
  }

  server.send(200, "application/json", "{\"status\":\"ok\",\"state\":\"" + stateStr + "\"}");
  Serial.println("[LED] → " + stateStr);
}

// ── Setup & Loop ───────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== RESILIENCE-ALPHA ESP8266 ===");

  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_RED,   OUTPUT);
  ledOff();

  // Connexion WiFi
  Serial.printf("Connexion à %s ...\n", SSID_NAME);
  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID_NAME, SSID_PASS);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500);
    Serial.print('.');
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nConnecté ! IP : %s\n", WiFi.localIP().toString().c_str());
    // Clignotement vert rapide = prêt
    for (int i = 0; i < 4; i++) {
      ledGreen(); delay(150);
      ledOff();   delay(150);
    }
  } else {
    Serial.println("\nWiFi KO — LED rouge fixe");
    ledRed();
  }

  // Routes HTTP
  server.on("/health", HTTP_GET,  handleHealth);
  server.on("/led",    HTTP_POST, handleLed);
  server.begin();
  Serial.println("Serveur HTTP démarré sur le port 80");
}

void loop() {
  server.handleClient();
  updateLed();
}
