# Procédure de mitigation

Déclenchée uniquement si le moteur confirme :

- événement bien formé et authentifié ;
- action dans la liste blanche (`ENABLE_RATE_LIMIT`) ;
- persistance (fenêtres consécutives) ;
- dégradation Prometheus **ou** signal SIEM Loki ;
- modèle non synthétique, sauf dérogation explicite `REMEDIATION_POLICY_ACCEPT_SYNTHETIC_MODEL`.

Alors : `ansible-playbook mitigate.yml` → `request.json` → `nginx -t` → reload profil `mitigation`.

Pendant `MITIGATING`, les événements suivants ne relancent pas le playbook.
