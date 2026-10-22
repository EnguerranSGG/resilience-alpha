# ESP8266 LED Controller — RESILIENCE-ALPHA

## Câblage

| ESP8266 (NodeMCU v2) | Composant |
|---|---|
| D5 / GPIO14 | Anode LED verte (+ résistance 220Ω vers GND) |
| D6 / GPIO12 | Anode LED rouge (+ résistance 220Ω vers GND) |
| GND | Cathode commune LED |

## Configuration WiFi

Modifier `platformio.ini` :
```ini
build_flags =
    -DWIFI_SSID=\"RESILIENCE-G13\"   ← numéro de groupe
    -DWIFI_PASS=\"Resilience2026!\"
```

## Compilation & Flash (CLion + PlatformIO)

1. Ouvrir le dossier `esp8266/` dans CLion
2. CLion détecte `platformio.ini` automatiquement
3. **Build** : `PlatformIO › Build`
4. **Flash** : `PlatformIO › Upload`

## API HTTP (port 80)

```
POST /led
Content-Type: application/json
{"state": "GREEN_BLINK" | "GREEN_SOLID" | "RED_BLINK" | "RED_SOLID" | "OFF"}
```

```
GET /health
→ {"status":"ok","ip":"192.168.137.2"}
```

## États LED

| État | Signification | Durée |
|---|---|---|
| `GREEN_BLINK` | Visage reconnu, attente MDP | Jusqu'au prochain état |
| `GREEN_SOLID` | Accès accordé (visage + MDP OK) | 30 s puis OFF |
| `RED_BLINK` | Mauvais mot de passe | Jusqu'au prochain état |
| `RED_SOLID` | Visage non reconnu / compte bloqué | 30 s puis OFF |
