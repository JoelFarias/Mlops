# Deploy do churn na AWS EC2

## Arquitetura

`Dockerfile.api` gera uma imagem com o código do front, do back e o pacote do
modelo. `compose.yaml` inicia dois containers com essa mesma imagem:

- `frontend`: Streamlit, porta 8501, inferência pelo backend por padrão.
- `backend`: FastAPI, porta 8000 acessível pela rede Docker e pelo localhost
  da EC2. Carrega uma única vez o modelo exportado.

No modo público, `compose.publico.yaml` mantém os dois serviços no localhost
da EC2 e Nginx publica somente o frontend por HTTPS. A demonstração não exige
login. O seletor de URL da API e os controles de recarga não aparecem para o
visitante; a recarga também retorna 403 no backend desse ambiente.

O banco e os caminhos do MLflow Windows não são necessários na EC2. O CSV do
frontend é enviado no pacote e montado somente para leitura. A chave SSH, o
histórico Git, o banco MLflow e os ambientes virtuais ficam fora do pacote.

## 1. Criar a instância

Configuração inicial recomendada para demonstração e pouco tráfego:

| Campo | Valor |
| --- | --- |
| Nome | `mlops-churn` |
| AMI | Ubuntu Server 24.04 LTS, x86_64 |
| Tipo | `t3.medium` (2 vCPUs e 4 GiB de RAM) |
| Armazenamento | 30 GB gp3 |
| Chave | novo par de chaves, formato `.pem`, salvo no computador |
| Rede | subnet pública, IPv4 público habilitado e saída para a internet |
| Entrada SSH | TCP 22, origem **Meu IP** |
| Entrada HTTP | TCP 80, origem `0.0.0.0/0`, desafio do certificado e redirecionamento |
| Entrada HTTPS | TCP 443, origem `0.0.0.0/0`, demonstração pública |

Confira a estimativa de custo da região na AWS antes de iniciar a instância.
A regra de SSH usa o IP público do administrador. As portas 5000, 8000 e
8501 não devem ter regras de entrada no Security Group.

Referências: [tipos T3](https://aws.amazon.com/ec2/instance-types/t3/),
[Security Groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html).

## 2. Exportar e testar localmente

Na raiz deste projeto, usando Python 3.12 e as dependências de treinamento:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m churn.exportar
docker compose build backend
docker compose up -d --no-build --pull never --wait --wait-timeout 180
docker compose exec -T backend python scripts/verificar-deploy.py
```

Execute a exportação apenas se `artifacts/modelo` ainda não existir. O arquivo
`artifacts/modelo/deploy.json` identifica a versão incluída na imagem.
O modelo precisa ter sido promovido pelo treinamento; o exportador não
promove nem retreina modelos.

## 3. Publicar do Windows

Com a EC2 em execução, substitua o IP e o caminho da chave:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy-ec2.ps1 `
  -Publico `
  -HostEc2 203.0.113.10 `
  -Usuario ubuntu `
  -Chave "C:\Users\seu-usuario\Downloads\mlops-churn.pem"
```

O script empacota somente os arquivos necessários, envia por SCP, instala
Docker e Compose pelo repositório oficial em uma Ubuntu nova e constrói a
imagem **uma vez**. Depois, inicia os dois serviços, aguarda os healthchecks,
compara os IDs das imagens e executa uma previsão real. Cada envio usa uma
pasta de release separada em `~/mlops-churn/releases/`.

O modo `-Publico` também instala Nginx e prepara uma página que atende somente
o desafio do certificado na porta 80. Após conferir as regras do Security
Group, conecte por SSH, entre na pasta de release impressa e execute:

```bash
bash scripts/configurar-https.sh IP-PUBLICO ativar
```

O instalador valida o desafio em staging antes de emitir o certificado
Let's Encrypt para o IP e ativa HTTPS. Os certificados de IP duram cerca de
seis dias; o timer `churn-https.timer` verifica a renovação a cada 12 horas.
A porta 80 precisa continuar aberta para a renovação automática.

Para aplicar firewall no host e restringir SSH ao IP da conexão atual:

```bash
bash scripts/proteger-host.sh
```

Abra uma segunda conexão SSH para testar o acesso. Nessa nova conexão, execute
`sudo systemctl stop churn-firewall-retorno.timer` para cancelar o retorno
automático. Se uma regra bloquear o administrador, o timer desativa o firewall
após três minutos. Mantenha também a regra SSH do Security Group em **Meu IP**.

Para gerar e revisar o pacote sem conectar à AWS:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy-ec2.ps1 -SomentePacote
```

Referências da instalação:
[Docker no Ubuntu](https://docs.docker.com/engine/install/ubuntu/) e
[inicialização com healthchecks](https://docs.docker.com/compose/how-tos/startup-order/).

## 4. Acessar e operar

Abra `https://IP-PUBLICO` de qualquer rede. A demonstração pública não exige login.
Exemplos de clientes: `1069-XAIEM`, `7590-VHVEG` e `0902-XKXPN`.

Na EC2, entre na pasta da release para consultar os serviços:

```bash
sudo docker compose ps
sudo docker compose logs --tail 80
curl --fail http://127.0.0.1:8000/pronto
curl --fail http://127.0.0.1:8000/modelo
sudo nginx -t
sudo systemctl list-timers churn-https.timer
sudo journalctl -u churn-https.service --since today
```

Os containers usam `restart: unless-stopped`, e o instalador habilita o Docker
no boot. A tag da imagem e os arquivos Compose ficam salvos no `.env` da release.
`/saude` indica processo ativo; `/pronto` exige o modelo carregado.
Para uma nova versão, exporte o modelo e faça outro deploy. As pastas de
releases e as imagens anteriores são preservadas para permitir recuperação.

Os containers rodam como usuário sem privilégios, com filesystem somente para
leitura, capacidades removidas e limites de CPU, memória e processos. O Nginx
mantém TLS 1.2/1.3, limita 10 requisições dinâmicas/s por IP com burst de 50,
até 20 conexões dinâmicas por IP e até 50 conexões dinâmicas simultâneas.
Arquivos estáticos usam limite separado de 100 requisições/s com burst de 300
e cache de um ano, permitindo que o navegador carregue os módulos em paralelo.
Mensagens WebSocket
compartilham a conexão; o limite HTTP não conta cada mensagem de inferência.
Os limites de recursos dos containers reduzem o impacto de sobrecarga, mas
não substituem proteção contra DDoS volumétrico.

Use somente dados apropriados para divulgação pública. Se o IP da EC2 mudar
após parar/iniciar a instância, atualize o endereço no deploy e emita um novo
certificado. A chave `.pem`, o CSV, os modelos, `.env` e certificados não devem
ser enviados ao Git. A renovação pode ser testada com Certbot `renew --dry-run`.

Referências: [certificados de IP no Certbot](https://letsencrypt.org/2026/03/11/shorter-certs-certbot),
[limite de requisições do Nginx](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html).
