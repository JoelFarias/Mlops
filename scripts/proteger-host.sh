#!/usr/bin/env bash
# Executar por SSH. A confirmacao de uma nova conexao deve cancelar o timer.
set -euo pipefail
origem_ssh=${SSH_CONNECTION%% *}
test -n "$origem_ssh"
python3 - "$origem_ssh" <<'PY'
import ipaddress, sys
ipaddress.ip_address(sys.argv[1])
PY
sudo -n tee /etc/ssh/sshd_config.d/10-churn.conf >/dev/null <<'EOF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxAuthTries 3
LoginGraceTime 30
EOF
sudo -n sshd -t
sudo -n systemctl reload ssh

if ! sudo -n ufw status | grep -q '^Status: active'; then
    # Evita bloquear o administrador se a regra de SSH falhar.
    sudo -n systemd-run --unit=churn-firewall-retorno --on-active=3min /usr/sbin/ufw disable
fi
sudo -n ufw default deny incoming
sudo -n ufw default allow outgoing
sudo -n ufw allow from "$origem_ssh" to any port 22 proto tcp
sudo -n ufw allow 80/tcp
sudo -n ufw allow 443/tcp
sudo -n ufw --force enable
sudo -n ufw status verbose
echo 'Teste uma nova conexao SSH e cancele churn-firewall-retorno.timer.'
