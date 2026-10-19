# Règles de l'équipe

1. **Données** : aucune donnée financière ou personnelle réelle. Montants, comptes et descriptions sont fictifs.
2. **Secrets** : jamais dans Git, une PR, une capture d'écran, un message ou une vidéo. Régénérer après toute fuite supposée.
3. **Tests offensifs** : uniquement contre les machines du laboratoire du groupe, via `security/attack-tests/run-loadtest.sh`, avec garde-fous actifs. Pas de scan ni de test sur le réseau de l'école ou sur Internet.
4. **IA** : aucun service d'IA externe pour le RAG ; modèles locaux via Ollama uniquement. Aucune donnée sensible dans les invites.
5. **Preuves** : un résultat n'est présenté que s'il a été réellement obtenu ; conserver la sortie brute, la date, le commit et la configuration. Aucune donnée synthétique présentée comme réelle.
6. **Exposition** : aucun service d'administration publié sur le hotspot (voir [exposition-reseau.md](exposition-reseau.md)).
7. **Revue** : toute modification de `infrastructure/nginx`, `infrastructure/ansible`, `remediation/` ou de la politique passe par une PR relue par un second membre.
