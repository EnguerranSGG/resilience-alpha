# RESILIENCE-ALPHA — Workshop M2 Bac+5 EPSI 2026

Démonstrateur de remédiation autonome zero-touch contre une attaque DDoS de type flood.

---

## Prérequis

| Composant | Version |
|---|---|
| Docker Desktop (Windows) | ≥ 4.28 |
| Python | 3.13 |
| Windows Hotspot | activé, SSID `RESILIENCE-G<n>` |
| ESP8266 (NodeMCU v2) | flashé avec `esp8266/` |

---

## Démarrage rapide

```powershell
# 1. Copier la configuration
copy .env.example .env
# Ajuster ESP8266_IP et GATEWAY_BIND_ADDR si nécessaire

# 2. Générer les secrets (JWT keys, MDP BDD)
bash scripts/generate-secrets.sh

# 3. Démarrer la stack
docker compose --env-file .env -f infrastructure/docker/compose.yml up -d --build

# 4. Vérifier (attendre ~30 s)
docker compose -f infrastructure/docker/compose.yml ps
```

Grafana : http://127.0.0.1:3000 (admin / voir secrets/grafana_password.txt)  
API Gateway : http://192.168.137.1:8080

---

## Lancer une attaque (démonstration)

```powershell
# Depuis le dossier security/attack-tests/
$env:PYTHON="C:/Users/remid/AppData/Local/Programs/Python/Python313/python.exe"
$env:PYTHONIOENCODING="utf-8"
bash run-loadtest.sh
```

Séquence attendue (dashboard Grafana) :
1. NORMAL → SUSPECT (~10 s)
2. SUSPECT → MITIGATING (~20 s, 5 fenêtres consécutives)
3. MITIGATING → RECOVERED (~7 s)

---

## Entraîner le modèle ML sur données réelles

```powershell
# Collecte (dans le conteneur ml-detector)
docker exec resilience-alpha-ml-detector-1 `
  python3 -m anomaly_detection.collect `
  --prometheus http://prometheus:9090 --minutes 60 --label 0 --out /tmp/normal.csv

# Entraînement
docker exec resilience-alpha-ml-detector-1 `
  python3 -m anomaly_detection.train --data /tmp/normal.csv /tmp/attack.csv

# Le modèle est rechargé automatiquement (hot-reload par mtime)
```

---

## Flash ESP8266 (LED bicolore)

1. Ouvrir `esp8266/` dans CLion (détection automatique PlatformIO)
2. Modifier le SSID/MDP dans `platformio.ini` si nécessaire
3. `PlatformIO › Upload`

LED sur D5 (GPIO14) = vert, D6 (GPIO12) = rouge.

---

## Structure du projet

```
apps/
  payment-api/      Service paiement (FastAPI + PostgreSQL)
  auth-service/     Authentification JWT
  frontend/         Interface web
  face-auth/        Reconnaissance faciale MFA + contrôle LED
ai/
  anomaly-detection/ Modèle Isolation Forest + collecte Prometheus
security/
  attack-tests/     Scripts Locust (loadtest)
  waf/              Configuration Nginx rate-limiting
infrastructure/
  docker/           docker-compose.yml + .env
  grafana/          Dashboards JSON + alertes
  prometheus/       Règles d'enregistrement
  ansible/          Playbooks remédiation
esp8266/            Firmware NodeMCU LED bicolore (PlatformIO)
```

---

## Génération du rendu Code.zip

```powershell
.\scripts\make-archive.ps1 -Group 13
```

Produit `Workshop2026-M2-G13-Code.zip` sans secrets ni binaires modèles.
