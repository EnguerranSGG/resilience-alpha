# Mesures préventives et correctives

| Mesure | Type | Composant | Couvre | Statut |
|---|---|---|---|---|
| Point d'entrée unique, réseaux internes | préventive | Compose | SR1, ER4 | READY |
| WAF ModSecurity / CRS | préventive | gateway | injections (hors scénario) | SCAFFOLDED |
| Rate limit profil `normal` | préventive | NGINX | SR1 | SCAFFOLDED (à calibrer) |
| Rate limit profil `mitigation` | corrective | Ansible + NGINX | ER1 | READY (mécanisme) |
| Isolation Forest | détective | ml-detector | ER1 | SCAFFOLDED (pas de modèle réel) |
| Politique multi-signaux | préventive (faux positifs) | remediation | ER3 | READY (unitaire) |
| Idempotence | préventive | payment-api | ER2 | READY |
| Vérification métier post-action | corrective | remediation | ER1, ER2 | READY (unitaire) |
| SOPS / secrets hors Git | préventive | security/secrets | ER4 | SCAFFOLDED |
| Locust borné, confirmation `LAB-ONLY` | préventive | attack-tests | SR5 | READY |

- [ ] TODO(P5) Après les essais de mercredi, ne conserver que les mesures **effectivement observées**.
