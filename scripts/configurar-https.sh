#!/usr/bin/env bash
# preparar: instala o proxy; ativar: emite e renova o certificado público do IP.
set -euo pipefail
cd "$(dirname "$0")/.."
ip_publico=${1:?Informe o IP publico da EC2}
etapa=${2:-preparar}
python3 - "$ip_publico" <<'PY'
import ipaddress, sys
endereco = ipaddress.ip_address(sys.argv[1])
if endereco.version != 4 or not endereco.is_global:
    raise SystemExit("Informe um IPv4 publico valido.")
PY

imagem_certbot=certbot/certbot:v5.9.0
if [[ "$etapa" == preparar ]]; then
    sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
    sudo -n docker pull "$imagem_certbot"
    sudo -n install -d -m 0755 /var/lib/letsencrypt/.well-known/acme-challenge
    sudo -n install -d -m 0700 /etc/letsencrypt
    sudo -n install -d -m 0750 /var/log/letsencrypt
    if ! sudo -n test -s /etc/letsencrypt/live/churn-publico/fullchain.pem; then
        sed "s/__IP_PUBLICO__/$ip_publico/g" deploy/nginx/bootstrap.conf |
            sudo -n tee /etc/nginx/sites-available/churn.conf >/dev/null
    fi
    sudo -n ln -sfn /etc/nginx/sites-available/churn.conf /etc/nginx/sites-enabled/churn.conf
    sudo -n rm -f /etc/nginx/sites-enabled/default
    sudo -n nginx -t
    sudo -n systemctl enable --now nginx
    sudo -n systemctl reload nginx
    echo "Proxy preparado. Libere TCP 80 e 443 para 0.0.0.0/0 no Security Group."
elif [[ "$etapa" == ativar ]]; then
    certbot() {
        sudo -n docker run --rm --network host \
            --mount type=bind,source=/etc/letsencrypt,target=/etc/letsencrypt \
            --mount type=bind,source=/var/lib/letsencrypt,target=/var/lib/letsencrypt \
            --mount type=bind,source=/var/log/letsencrypt,target=/var/log/letsencrypt \
            "$imagem_certbot" "$@"
    }
    argumentos=(certonly --webroot --webroot-path /var/lib/letsencrypt
        --ip-address "$ip_publico" --cert-name churn-publico
        --preferred-profile shortlived --key-type ecdsa
        --agree-tos --register-unsafely-without-email --non-interactive)
    certbot "${argumentos[@]}" --dry-run
    certbot "${argumentos[@]}"
    sed "s/__IP_PUBLICO__/$ip_publico/g" deploy/nginx/publico.conf |
        sudo -n tee /etc/nginx/sites-available/churn.conf >/dev/null
    sudo -n nginx -t
    sudo -n systemctl reload nginx
    sudo -n install -m 0750 scripts/renovar-https.sh /usr/local/sbin/churn-renovar-https
    sudo -n install -m 0644 deploy/systemd/churn-https.service /etc/systemd/system/churn-https.service
    sudo -n install -m 0644 deploy/systemd/churn-https.timer /etc/systemd/system/churn-https.timer
    sudo -n systemctl daemon-reload
    sudo -n systemctl enable --now churn-https.timer
    echo "HTTPS ativo em https://$ip_publico"
else
    echo "Etapa invalida: use preparar ou ativar." >&2
    exit 1
fi
