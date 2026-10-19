#!/bin/sh
# Exécuté par /docker-entrypoint.sh avant le lancement de NGINX.
/usr/local/bin/profile-watcher.sh &
