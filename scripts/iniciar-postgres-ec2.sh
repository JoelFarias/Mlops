#!/usr/bin/env bash
# Executar com sudo na EC2 privada do PostgreSQL.
set -euo pipefail

arquivo_imagem=${1:?Informe o arquivo postgres-churn.tar}
ip_banco=${2:?Informe o IPv4 privado desta EC2}
ip_app=${3:?Informe o IPv4 privado da EC2 da aplicacao}
porta_proxy=${4:-}
imagem=churn-postgres:1.0
container=churn-postgres
pasta_config=/etc/churn-postgres

test "$EUID" -eq 0
. /etc/os-release
test "$ID" = ubuntu
python3 - "$ip_banco" "$ip_app" <<'PY'
import ipaddress
import sys

for valor in sys.argv[1:]:
    endereco = ipaddress.IPv4Address(valor)
    if not endereco.is_private or endereco.is_loopback:
        raise SystemExit("Use os IPv4 privados das duas EC2.")
PY

if ! command -v docker >/dev/null; then
    opcoes_apt=()
    if [[ -n "$porta_proxy" ]]; then
        [[ "$porta_proxy" =~ ^[0-9]{1,5}$ ]]
        proxy="socks5h://127.0.0.1:$porta_proxy/"
        opcoes_apt=(-o "Acquire::http::Proxy=$proxy" -o "Acquire::https::Proxy=$proxy")
    fi
    apt-get "${opcoes_apt[@]}" -o APT::Update::Error-Mode=any update
    DEBIAN_FRONTEND=noninteractive apt-get "${opcoes_apt[@]}" install -y +        --no-install-recommends docker.io
fi
systemctl enable --now docker
if ! docker image inspect "$imagem" >/dev/null 2>&1; then
    docker load --input "$arquivo_imagem"
fi

umask 077
install -d -m 0700 "$pasta_config"
for segredo in admin-senha leitura-senha; do
    if [[ ! -s "$pasta_config/$segredo" ]]; then
        openssl rand -hex 32 >"$pasta_config/$segredo"
    fi
done
if [[ ! -e "$pasta_config/server.crt" && ! -e "$pasta_config/server.key" ]]; then
    openssl req -x509 -newkey rsa:2048 -sha256 -noenc -days 365 +        -subj /CN=churn-postgres -addext "subjectAltName=IP:$ip_banco" +        -keyout "$pasta_config/server.key" -out "$pasta_config/server.crt"
fi
test -s "$pasta_config/server.key"
openssl verify -purpose sslserver -verify_ip "$ip_banco" \
    -CAfile "$pasta_config/server.crt" "$pasta_config/server.crt"
postgres_uid=$(docker run --rm --network none --entrypoint id "$imagem" -u postgres)
chown "$postgres_uid" "$pasta_config/server.key"
chmod 0600 "$pasta_config/server.key"
printf 'local all postgres peer\nhostssl churn churn_leitura %s/32 scram-sha-256\n' +    "$ip_app" >"$pasta_config/pg_hba.conf"
chmod 0644 "$pasta_config/server.crt" "$pasta_config/pg_hba.conf"

if docker container inspect "$container" >/dev/null 2>&1; then
    servico=$(docker inspect --format '{{index .Config.Labels "churn.servico"}}' "$container")
    test "$servico" = postgres-ec2
    docker start "$container" >/dev/null
else
    docker run --detach --name "$container" --restart unless-stopped +        --label churn.servico=postgres-ec2 --memory 384m +        --log-opt max-size=5m --log-opt max-file=3 +        --publish "$ip_banco:5432:5432" +        --mount type=volume,source=churn-postgres-dados,target=/var/lib/postgresql/data +        --mount "type=bind,source=$pasta_config/admin-senha,target=/run/secrets/postgres_admin,readonly" +        --mount "type=bind,source=$pasta_config/server.crt,target=/run/postgres/server.crt,readonly" +        --mount "type=bind,source=$pasta_config/server.key,target=/run/postgres/server.key,readonly" +        --mount "type=bind,source=$pasta_config/pg_hba.conf,target=/run/postgres/pg_hba.conf,readonly" +        --env POSTGRES_PASSWORD_FILE=/run/secrets/postgres_admin "$imagem" +        -c ssl=on -c ssl_cert_file=/run/postgres/server.crt +        -c ssl_key_file=/run/postgres/server.key -c hba_file=/run/postgres/pg_hba.conf +        -c shared_buffers=64MB -c max_connections=20 >/dev/null
fi

for tentativa in {1..60}; do
    if docker exec "$container" pg_isready -q -h 127.0.0.1 -d churn; then
        break
    fi
    if [[ "$tentativa" -eq 60 ]]; then
        docker logs --tail 40 "$container"
        exit 1
    fi
    sleep 1
done

psql_admin() {
    docker exec -i --user postgres "$container" psql -X -U postgres -d churn -v ON_ERROR_STOP=1 "$@"
}

psql_admin -q <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'churn_leitura') THEN
        CREATE ROLE churn_leitura LOGIN;
    END IF;
END
$$;
GRANT CONNECT ON DATABASE churn TO churn_leitura;
GRANT USAGE ON SCHEMA public TO churn_leitura;
GRANT SELECT ON TABLE public.clientes TO churn_leitura;
SQL
senha_leitura=$(cat "$pasta_config/leitura-senha")
printf '\\password churn_leitura\n%s\n%s\n' "$senha_leitura" "$senha_leitura" | psql_admin -q
psql_admin -Atc 'SELECT pg_reload_conf(); SELECT count(*) FROM public.clientes;'
