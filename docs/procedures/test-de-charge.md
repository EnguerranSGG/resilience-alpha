# Procédure de test de charge autorisée

Outil : Locust, dépôt `security/attack-tests/`. **Aucun lancement automatique.**

1. Lire [security/attack-tests/README.md](../../security/attack-tests/README.md).
2. Cible = passerelle du groupe, URL privée, listée explicitement.
3. Durée ≤ 300 s, utilisateurs ≤ 50, débit borné par les garde-fous.
4. Saisir `LAB-ONLY` pour confirmer.
5. Arrêt immédiat : Ctrl+C.
6. Archiver les CSV **hors Git** avec date, versions, IP, profil NGINX.

Ce n'est pas un outil offensif généraliste. Usage hors labo = faute.
