/**
 * RESILIENCE-ALPHA — ESP8266 LED Controller
 * Consigne Additionnelle 1 : indicateur LED bicolore pour face-auth
 *
 * Pinout (NodeMCU v2) :
 *   D5 / GPIO14 → LED verte (anode, résistance 220Ω vers GND)
 *   D6 / GPIO12 → LED rouge (anode, résistance 220Ω vers GND)
 *
 * États gérés via POST /led {"state":"..."}  :
 *   OFF          → éteint
 *   GREEN_BLINK  → vert clignotant (visage reconnu, attente MDP)
 *   GREEN_SOLID  → vert fixe 30 s puis OFF (MDP correct)
 *   RED_BLINK    → rouge clignotant (mauvais MDP)
 *   RED_SOLID    → rouge fixe 30 s puis OFF (visage non reconnu / bloqué)
 */

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

// ── Constantes ──────────────────────────────────────────────────────────────
#ifndef WIFI_SSID
#define WIFI_SSID "RESILIENCE-G13"
#endif
#ifndef WIFI_PASS
#define WIFI_PASS "Resilience2026!"
#endif
#ifndef LED_GREEN
#define LED_GREEN 14   // D5
#endif
#ifndef LED_RED
#define LED_RED   12   // D6
#endif
#ifndef AUTO_OFF_MS
#define AUTO_OFF_MS 30000UL   // durée état SOLID avant extinction
#endif

#define BLINK_INTERVAL 250   // ms entre chaque transition clignotant

// ── Variables d'état ────────────────────────────────────────────────────────
enum LedState { OFF, GREEN_BLINK, GREEN_SOLID, RED_BLINK, RED_SOLID };

volatile LedState currentState = OFF;
unsigned long     stateStartMs  = 0;
unsigned long     lastBlinkMs   = 0;
bool              blinkPhase    = false;

AsyncWebServer server(80);

// ── Helpers LED ─────────────────────────────────────────────────────────────
void ledsOff() {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED,   LOW);
}

void applyState(LedState s) {
    currentState = s;
    stateStartMs = millis();
    blinkPhase   = false;
    ledsOff();

    if (s == GREEN_SOLID) {
        digitalWrite(LED_GREEN, HIGH);
    } else if (s == RED_SOLID) {
        digitalWrite(LED_RED, HIGH);
    }
    // BLINK states are handled in loop()
}

// ── Setup ────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    pinMode(LED_GREEN, OUTPUT);
    pinMode(LED_RED,   OUTPUT);
    ledsOff();

    // Connexion WiFi
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.print("Connexion WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\nConnecté — IP : %s\n", WiFi.localIP().toString().c_str());

    // ── POST /led ─────────────────────────────────────────────────────────────
    server.on("/led", HTTP_POST, [](AsyncWebServerRequest* req) {}, nullptr,
        [](AsyncWebServerRequest* req, uint8_t* data, size_t len, size_t, size_t) {

            StaticJsonDocument<128> doc;
            DeserializationError err = deserializeJson(doc, data, len);
            if (err) {
                req->send(400, "application/json", "{\"error\":\"JSON invalide\"}");
                return;
            }

            const char* stateStr = doc["state"] | "OFF";
            LedState    next     = OFF;

            if      (strcmp(stateStr, "GREEN_BLINK") == 0) next = GREEN_BLINK;
            else if (strcmp(stateStr, "GREEN_SOLID") == 0) next = GREEN_SOLID;
            else if (strcmp(stateStr, "RED_BLINK")   == 0) next = RED_BLINK;
            else if (strcmp(stateStr, "RED_SOLID")   == 0) next = RED_SOLID;

            applyState(next);
            Serial.printf("LED → %s\n", stateStr);

            req->send(200, "application/json", "{\"ok\":true}");
        }
    );

    // ── GET /health ───────────────────────────────────────────────────────────
    server.on("/health", HTTP_GET, [](AsyncWebServerRequest* req) {
        String body = "{\"status\":\"ok\",\"ip\":\"" + WiFi.localIP().toString() + "\"}";
        req->send(200, "application/json", body);
    });

    server.begin();
    Serial.println("Serveur HTTP démarré sur port 80");
}

// ── Loop ─────────────────────────────────────────────────────────────────────
void loop() {
    unsigned long now = millis();

    // Extinction automatique des états SOLID après AUTO_OFF_MS
    if ((currentState == GREEN_SOLID || currentState == RED_SOLID) &&
        (now - stateStartMs >= AUTO_OFF_MS)) {
        applyState(OFF);
        Serial.println("LED → OFF (auto)");
        return;
    }

    // Gestion clignotement non-bloquant
    if (currentState == GREEN_BLINK || currentState == RED_BLINK) {
        if (now - lastBlinkMs >= BLINK_INTERVAL) {
            lastBlinkMs = now;
            blinkPhase  = !blinkPhase;
            ledsOff();
            if (blinkPhase) {
                if (currentState == GREEN_BLINK) digitalWrite(LED_GREEN, HIGH);
                else                             digitalWrite(LED_RED,   HIGH);
            }
        }
    }
}
