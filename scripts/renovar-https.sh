#!/usr/bin/env bash
set -euo pipefail
/usr/bin/docker run --rm --network host \
    --mount type=bind,source=/etc/letsencrypt,target=/etc/letsencrypt \
    --mount type=bind,source=/var/lib/letsencrypt,target=/var/lib/letsencrypt \
    --mount type=bind,source=/var/log/letsencrypt,target=/var/log/letsencrypt \
    certbot/certbot:v5.9.0 renew --cert-name churn-publico --non-interactive \
    --no-random-sleep-on-renew --quiet
/usr/sbin/nginx -t
/usr/bin/systemctl reload nginx
