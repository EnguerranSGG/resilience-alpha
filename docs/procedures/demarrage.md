# Procédure de démarrage

Voir le README racine pour le détail. Rappel :

```bash
./scripts/check-environment.sh
./scripts/bootstrap.sh          # .env + secrets
make up                         # socle sans RAG
make smoke
```

Arrêt : `make down` (volumes conservés). Reset destructif : `make reset`.

RAG : `make rag-up && make rag-pull && make rag-index` — optionnel, gourmand.
