#!/usr/bin/env bash
# Executar na raiz do pacote em uma EC2 Ubuntu nova.
set -euo pipefail

cd "$(dirname "$0")/.."
modo=${1:-local}
ip_publico=${2:-}
. /etc/os-release
if [[ "$ID" != ubuntu ]]; then
    echo "Este instalador requer Ubuntu. Sistema encontrado: $ID" >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    sudo -n apt-get update
    sudo -n apt-get install -y ca-certificates curl
    sudo -n install -m 0755 -d /etc/apt/keyrings
    sudo -n curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    sudo -n chmod a+r /etc/apt/keyrings/docker.asc
    sudo -n tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
    sudo -n apt-get update
    sudo -n apt-get install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
fi

sudo -n systemctl enable --now docker
sudo -n docker compose version
test -s artifacts/modelo/MLmodel
test -s data/raw/churn.csv

# A mesma tag imutável identifica a imagem usada pelos dois serviços.
export CHURN_IMAGEM="churn:$(basename "$PWD")"
printf 'CHURN_IMAGEM=%s\n' "$CHURN_IMAGEM" > .env
if [[ "$modo" == publico ]]; then
    test -n "$ip_publico"
    printf 'COMPOSE_FILE=compose.yaml:compose.publico.yaml\nCHURN_ENDERECO_PUBLICO=%s\n' "$ip_publico" >> .env
fi
sudo -n docker compose build backend

compose() {
    sudo -n docker compose "$@"
}

if ! compose up --detach --no-build --pull never --wait --wait-timeout 180; then
    compose logs --tail 80
    exit 1
fi

backend_id=$(compose ps --quiet backend)
frontend_id=$(compose ps --quiet frontend)
backend_image=$(sudo -n docker inspect --format '{{.Image}}' "$backend_id")
frontend_image=$(sudo -n docker inspect --format '{{.Image}}' "$frontend_id")
test "$backend_image" = "$frontend_image"
compose exec -T backend python scripts/verificar-deploy.py
compose ps
printf '\nImagem compartilhada: %s\nFrontend: porta 8501\n' "$backend_image"
