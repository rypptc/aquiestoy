#!/usr/bin/env bash
# Sube los JSONs de .tmp/batch/ al servidor y corre importar.py

SERVER="aquiestoy"
REMOTE_DIR="/var/www/aquiestoy"
BATCH_DIR=".tmp/batch"

# -----------------------------------------------------------------------

set -e

archivos=("$BATCH_DIR"/*.json)

if [ ! -e "${archivos[0]}" ]; then
    echo "No hay archivos JSON en $BATCH_DIR"
    exit 0
fi

echo "Subiendo ${#archivos[@]} archivo(s) a $SERVER:$REMOTE_DIR/$BATCH_DIR ..."
ssh "$SERVER" "mkdir -p $REMOTE_DIR/$BATCH_DIR"
scp "${archivos[@]}" "$SERVER:$REMOTE_DIR/$BATCH_DIR/"

echo "Importando en producción..."
ssh "$SERVER" "cd $REMOTE_DIR && python3 importar.py"

echo "Listo."
