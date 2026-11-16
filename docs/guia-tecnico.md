# Guia técnico na ordem do GitHub

Abra este guia ao lado da página do repositório. A sequência segue a visualização
padrão do GitHub: **pastas primeiro, depois arquivos**, em ordem de nome.
`src/churn` aparece junto porque o GitHub compacta esse caminho.

O projeto usa a base preparada pelo professor para treinar uma Random Forest,
registrar experimentos no MLflow e disponibilizar previsões em uma aplicação.
A preparação da base não é apresentada como uma entrega deste projeto.

Este guia detalha os **54 arquivos ativos**. As áreas de histórico e material
da disciplina são identificadas para orientar a navegação, sem destrinchar o
código arquivado.

```text
.streamlit/
data/
deploy/
docs/
legado/                    referência arquivada; siga adiante
scripts/
src/churn/
tests/
.dockerignore
.gitattributes
.gitignore
Dockerfile.api
Dockerfile.postgres
Dockerfile.postgres.dockerignore
LICENSE
Makefile
README.md
compose.postgres.yaml
compose.publico.yaml
compose.yaml
pyproject.toml
requirements.runtime.txt
requirements.txt
```


## Como estudar o guia

Em cada arquivo, abra o bloco **“Entenda os termos e as perguntas”** antes de
ensaiar a frase curta. Ele explica as palavras usadas naquele trecho, dá
exemplos e mostra perguntas que podem surgir.

Você entendeu uma parte quando consegue responder, sem ler:

1. O que entra e o que sai?
2. Quem executa esse trabalho?
3. Por que isso é necessário aqui?
4. O que muda se essa parte falhar?

### Um exemplo para ligar os conceitos

Um cliente é localizado pelo código. A interface reúne suas informações e
envia uma mensagem ao serviço de previsão. O serviço usa o objeto já treinado
e devolve `0.60`. Uma regra compara esse score ao corte `0.50` e marca `Yes`.
Essa chamada não ensina outro modelo nem demonstra 60% de acerto.

**Modelo** é o objeto ajustado; **inferência** é sua aplicação; **API** é o
contrato de comunicação; **JSON** é o formato da mensagem; **limiar** é a regra
de corte. São cinco papéis diferentes no mesmo exemplo.

**Random Forest** é o algoritmo que combina várias árvores de decisão;
**MLflow** é a ferramenta usada aqui para registrar execuções e organizar
versões do modelo. Registrar não é treinar, e treinar não é fazer uma consulta.

**MLOps** reúne práticas para desenvolver, repetir, identificar e operar
sistemas de aprendizado de máquina. Neste projeto, aparece na organização do
código, no rastreamento do treino, na versão exportada e na forma de servir o
modelo. Não é o nome de uma biblioteca que treina automaticamente.

## 1. `.streamlit/`

Configuração da interface feita com Streamlit. O ponto inicial no nome da pasta
não significa código secreto: é apenas uma convenção de configuração.

### `.streamlit/config.toml`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Streamlit** é uma biblioteca Python que gera páginas com campos, botões e
  tabelas. O script roda no servidor; o navegador mostra a interface.
- **Biblioteca** é código pronto que o programa importa. A biblioteca fornece
  componentes; a sua aplicação define como usá-los.
- **TOML** é o formato desta configuração. `[theme]` agrupa opções e uma
  atribuição define um valor; não é uma função Python.

**Se perguntarem “Streamlit é o modelo?”** Não. No modo API, a interface envia
os atributos para outro processo calcular a previsão.

</details>

**Função:** define cores, fonte, apresentação da barra de ferramentas e
desativação do envio de estatísticas de uso.

**Quem usa:** o processo Streamlit. O `Dockerfile.api` copia esse arquivo para
a imagem usada pela aplicação.

**Como explicar:** “Aqui fica a configuração visual da interface. Não participa
do treinamento nem calcula a previsão.”

## 2. `data/`

Contém os dados de entrada da disciplina. A subpasta `raw/` guarda o arquivo
como ele foi fornecido pelo professor.

### `data/raw/churn.csv`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **CSV** é uma tabela em texto com campos separados por delimitador.
  Aqui cada registro representa um cliente.
- **Dataset** é o conjunto de dados. **Feature/atributo** é uma informação
  usada na previsão, como meses de permanência.
- **Alvo/rótulo** é a resposta conhecida que ensina o modelo: `Churn=Yes/No`.
  É classificação binária porque existem duas classes.
- **Hash** é um resumo calculado a partir dos bytes. MD5 e SHA-256 são
  algoritmos diferentes para calculá-lo. Não é criptografia do CSV.

**Se perguntarem “o modelo prevê só pelo código?”** O código localiza o registro;
a previsão usa os 19 atributos, sem ID e sem o alvo real.

</details>

**Função:** é a base original do professor, já disponível com o clone e com o
Download ZIP. Não é necessário buscar outra base.

São 7.043 registros e 21 colunas:

- `customerID`: identificador para localizar o cliente.
- 19 atributos: informações do perfil, contrato, serviços e cobranças.
- `Churn`: resposta conhecida na base, usada como alvo do treinamento.

O código do cliente e a resposta `Churn` não entram como atributos de previsão.
O MD5 `d390bd07b5514a2256a2396993b8b0e3` confere com o arquivo do curso.

**Quem usa:** `experimentos.py` lê o CSV para o treino. O Streamlit local o usa
para buscar clientes. A imagem do PostgreSQL também o inclui para inicializar
a tabela em um volume novo.

**Como explicar:** “Esta é a base fornecida na disciplina. Meu trabalho começa
na sua utilização: comparar configurações, rastrear a versão do modelo e
disponibilizar a previsão.”

Os exemplos atuais são `8888-XEBO` e `9465-LQYV`.

## 3. `deploy/`

Guarda configurações para a publicação: entrada HTTPS, banco e renovação do
certificado. Os scripts de operação aplicam esses arquivos nos hosts.

### `deploy/nginx/bootstrap.conf`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Nginx** é o servidor que recebe a conexão web na entrada da instalação.
- **Bootstrap** significa preparação inicial.
- **ACME/desafio** é o procedimento em que a autoridade pede uma prova de
  controle do endereço antes de emitir o certificado. O caminho especial
  atende a essa prova; não é a página da aplicação.

**Se perguntarem “essa já é a configuração definitiva do site?”** Não. Ela
prepara a emissão do certificado usado na configuração HTTPS.

**Para conferir:** [Emissão de certificados pelo ACME](https://letsencrypt.org/how-it-works/).

</details>

**Função:** configuração inicial do Nginx, antes do certificado público.
Atende em HTTP o desafio usado para emitir o certificado.

**Quem usa:** `scripts/configurar-https.sh` na etapa `preparar`.

**Como explicar:** “É a configuração inicial para provar o controle do endereço
e permitir a emissão do certificado.”

### `deploy/nginx/publico.conf`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Proxy reverso** recebe pedidos destinados à aplicação e os encaminha a um
  serviço interno. O visitante fala com Nginx; Nginx fala com Streamlit.
- **HTTP** define a troca de pedidos e respostas na web. **HTTPS** protege essa
  troca com **TLS**, que cifra a comunicação e permite verificar a identidade
  do servidor por certificado.
- **Certificado** vincula a identidade a uma chave pública por assinatura de
  uma autoridade. A chave privada correspondente fica no servidor.
  **Let's Encrypt** é a autoridade usada no procedimento.
- **WebSocket** mantém conexão com mensagens nos dois sentidos; o Streamlit
  utiliza esse canal para interações.
- **Cabeçalhos** são campos adicionais do pedido/resposta, como seu tipo de
  conteúdo. **Rate limit** limita solicitações; não impede toda sobrecarga.

**Exemplo:** navegador → Nginx → Streamlit → FastAPI. O HTTPS do visitante
termina no Nginx; isso não significa que todos os saltos internos usem HTTPS.

**Se perguntarem “o proxy calcula a previsão?”** Não. Ele encaminha tráfego;
a FastAPI atende a rota que usa o modelo.

**Para conferir:** [HTTPS e ACME](https://letsencrypt.org/how-it-works/).

</details>

**Função:** configura HTTPS e o proxy para o Streamlit, encaminha WebSocket
e define cabeçalhos, limites de requisições e limites de conexões. O HTTP comum
redireciona para HTTPS; o desafio de renovação continua disponível.

A entrada pública é o Nginx. As chamadas do frontend à FastAPI acontecem dentro
da aplicação. Rotas operacionais como `/docs` e `/prever` não são publicadas
diretamente por esse proxy.

**Quem usa:** Nginx, após a ativação do HTTPS.

**Como explicar:** “Este arquivo define a porta de entrada pública. Ele recebe
a conexão segura do navegador e a encaminha à interface.”

### `deploy/postgres/iniciar.sql`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **PostgreSQL** é o sistema que gerencia o banco. **SQL** é a linguagem para
  criar estruturas e consultar/manipular dados.
- **Tabela** tem linhas e colunas. **Schema**, no banco, é um espaço de nomes:
  em `public.clientes`, `public` é o schema e `clientes` é a tabela.
- **Chave primária** identifica cada linha de forma única e não aceita nulo.
- **NULL** representa ausência de valor; não é zero nem o texto `"NULL"`.
- **Transação** agrupa operações que confirmam juntas ou são desfeitas juntas.
  `BEGIN` e `COMMIT` delimitam esse grupo.

**Se perguntarem “esse SQL roda a cada clique?”** Não. Ele inicializa a tabela.
A consulta online usa `SELECT` no módulo de acesso ao banco.

</details>

**Função:** cria `public.clientes`, importa as 21 colunas do CSV e usa
`customerID` como chave primária. Ajusta o tipo de `TotalCharges` para número,
convertendo espaços em `NULL`.

**Quem usa:** a imagem do PostgreSQL na inicialização de um volume novo.

**Atenção:** trocar a imagem ou reiniciar o contêiner com um volume já existente
não executa novamente a importação.

**Como explicar:** “O banco recebe os clientes dessa base. Ele fornece os dados
da consulta; o modelo treinado fica em outro pacote.”

### `deploy/systemd/churn-https.service`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **systemd** é o gerenciador de serviços e tarefas do host Linux.
- **Service** descreve um comando e as condições de execução.
- **Oneshot** é uma execução pontual: o comando termina, em vez de atender
  requisições continuamente como o servidor web.

**Se perguntarem “isso roda no contêiner?”** O arquivo é instalado no host
Ubuntu e chama o script definido em sua configuração.

</details>

**Função:** define uma tarefa `oneshot` do systemd para executar o script de
renovação do HTTPS.

**Quem usa:** o systemd no host, por acionamento do timer.

**Como explicar:** “Descreve o que o servidor deve executar quando for verificar
a renovação do certificado.”

### `deploy/systemd/churn-https.timer`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Timer** dispara uma tarefa conforme uma regra de tempo.
- **Renovação** atualiza o certificado antes do vencimento.
- Verificar a cada 12 horas não significa emitir um certificado novo
  obrigatoriamente a cada 12 horas; o comando avalia a necessidade.

**Se perguntarem “service e timer são duplicados?”** Um define a tarefa;
o outro agenda quando verificar.

</details>

**Função:** agenda a verificação após a inicialização e a cada 12 horas, com
atraso aleatório de até cinco minutos.

**Quem usa:** systemd, para acionar o `service` anterior.

**Como explicar:** “O service diz o que executar; o timer diz quando executar.”

## 4. `docs/`

Documentação de instalação, funcionamento e operação. A pasta
`material-disciplina/` reúne os slides e os guias da aula; para apresentar o
fluxo ativo, siga os dois arquivos abaixo.

### `docs/deploy-ec2.md`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Deploy** coloca uma versão em um ambiente onde será executada.
- **EC2** é o serviço AWS de máquinas virtuais; **instância** é uma dessas
  máquinas. Neste desenho, os contêineres rodam dentro das EC2.
- **VPC** é a rede virtual da conta; **subnet** é uma subdivisão de rede.
- **Security Group** controla o tráfego permitido nas interfaces associadas.
  Não faz login na aplicação nem cria usuário do banco.
- **IP privado** é o endereço usado na comunicação interna prevista para o banco.
- **RDS** é o serviço gerenciado de bancos relacionais da AWS. Neste projeto,
  o banco é administrado em um contêiner numa EC2; não utiliza RDS.

**Se perguntarem “é RDS?”** Não neste desenho: é PostgreSQL em contêiner
numa segunda EC2.

**Para conferir:** [Conceitos do Amazon EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html) · [Banco gerenciado no RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html).

</details>

**Função:** manual para preparar e operar a publicação documentada, com uma EC2
para a aplicação e outra para o PostgreSQL privado.

Descreve pré-requisitos, envio do pacote, ativação do HTTPS, conexão ao banco
e verificações operacionais. É um manual: suas instruções só mudam o servidor
quando alguém executa os comandos.

**Como explicar:** “Este é o roteiro de publicação. Os arquivos descrevem a
instalação; a versão realmente executada precisa ser conferida no servidor.”

### `docs/guia-tecnico.md`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Documentação** explica a estrutura e o uso do programa.
- **Markdown** é a notação de títulos, listas, links e tabelas que o GitHub
  apresenta de forma formatada.
- Descrever um procedimento não comprova sua execução. É preciso observar
  o ambiente ou resultado para afirmar que ele foi executado.

**Se perguntarem “onde está a regra?”** Abra o arquivo citado no tópico e
mostre a função que implementa o comportamento.

</details>

**Função:** é este guia de estudo. Explica os arquivos e o papel de cada um na
ordem em que você abre o repositório.

**Como explicar:** “Este documento permite acompanhar a árvore e entender como
cada parte participa do projeto.”

## 5. `legado/`

É a área reservada ao histórico, separada do código mantido. Está fora do
pacote ativo, da suíte padrão e do contexto Docker da aplicação.

**Na apresentação:** “Aqui preservei as versões anteriores. O funcionamento
atual está em `src/churn`, e é esse fluxo que vou explicar.” Depois, siga
para `scripts/`. Não é necessário abrir as implementações arquivadas.

## 6. `scripts/`

São os procedimentos executáveis de instalação, publicação e verificação.
Usam as configurações de `deploy/`.

### `scripts/configurar-https.sh`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Script** é uma sequência de comandos em um arquivo.
- **Shell** interpreta comandos do sistema; **Bash** é o interpretador
  esperado para os arquivos `.sh` deste projeto.
- **Certbot** é a ferramenta que pede/renova certificados. O certificado é
  o resultado; a ferramenta executa o procedimento.

**Se perguntarem “por que automatizar?”** Para repetir os passos previstos e
parar quando uma etapa obrigatória falha.

</details>

**Função:** instala/prepara o Nginx e, na etapa de ativação, solicita o
certificado via Certbot. Também instala a renovação pelo systemd.

**Quem usa:** o administrador durante a preparação do host público.

**Como explicar:** “Automatiza a configuração da entrada HTTPS usando os arquivos
do Nginx e as tarefas de renovação.”

### `scripts/deploy-ec2.ps1`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **PowerShell** é a linguagem/ambiente de comandos deste script Windows.
- **SSH** fornece acesso remoto autenticado e cifrado; **SCP** transfere
  arquivos usando esse transporte.
- **tar.gz** é o pacote de arquivos compactado.
- **Release** é uma entrega identificada da aplicação.

**Se perguntarem “ele treina na EC2?”** Não. Exige o pacote do modelo já
exportado; treinamento é outro comando.

</details>

**Função:** no Windows, seleciona os arquivos necessários, gera um pacote
`tar.gz` com hash, envia por SSH/SCP e chama o inicializador da aplicação.
Cada envio recebe uma pasta de release própria.

`-SomentePacote` cria o pacote local e para antes do envio. `-Publico` inclui
a configuração pública; `-Publico -Postgres` prepara o perfil que consulta o
banco privado.

**Como explicar:** “É o procedimento de entrega do meu computador para a EC2.
O pacote reúne código, configuração e uma versão já exportada do modelo.”

### `scripts/iniciar-ec2.sh`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Host** é a máquina onde os processos/contêineres executam.
- **Build** constrói a imagem a partir do Dockerfile.
- **Healthcheck** repete uma checagem de saúde ou prontidão.
- **ID da imagem** identifica seu conteúdo; **tag** é um nome que aponta para
  uma imagem e pode ser reassociado.

**Se perguntarem “criar o contêiner já prova que funciona?”** Não. Por isso
o script espera prontidão e ainda executa uma previsão de teste.

</details>

**Função:** no Ubuntu, verifica insumos, prepara Docker se necessário, configura
o Compose da release, constrói a imagem e sobe os serviços.

Espera os healthchecks, confere que backend e frontend usam a mesma imagem e
chama o script de verificação. Com PostgreSQL, verifica a consulta de um cliente
antes de atualizar os serviços.

**Como explicar:** “Faz a aplicação subir no host e verifica se os componentes
necessários respondem.”

### `scripts/iniciar-postgres-ec2.sh`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Volume** é armazenamento separado do contêiner que pode continuar existindo
  depois que ele é removido/recriado.
- **Usuário de leitura** recebe permissão de consultar, em vez de administrar
  o banco.
- **TLS do banco** protege a conexão PostgreSQL. É outra conexão e outro
  certificado, distintos do HTTPS do site.

**Se perguntarem “nova imagem atualiza a tabela?”** Não automaticamente.
Com dados existentes no volume, a carga inicial não é repetida.

</details>

**Função:** prepara o host privado do PostgreSQL: Docker, imagem, volume, TLS,
regra de acesso e usuário de leitura.

**Quem usa:** o administrador da instalação do banco. A API utiliza a conexão
configurada; esse instalador não é executado a cada consulta.

**Como explicar:** “Prepara o banco privado para fornecer os dados dos clientes
à aplicação.”

### `scripts/proteger-host.sh`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Firewall** filtra conexões de rede conforme regras.
- **UFW** é a ferramenta que configura o firewall do host.
- **Autenticação por chave SSH** comprova posse da chave privada associada à
  chave pública autorizada. Ela não é o certificado HTTPS.

**Se perguntarem “por que prever retorno?”** Uma regra incorreta pode bloquear
o próprio administrador. O script prevê recuperação nas condições descritas.

</details>

**Função:** configura SSH por chave e firewall, usando o IP da conexão do
administrador. Inclui a medida de retorno prevista para evitar perda de acesso.

**Como explicar:** “É uma rotina administrativa de proteção do host. Não faz
parte do cálculo do risco do cliente.”

### `scripts/renovar-https.sh`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Validar configuração** pergunta ao Nginx se os arquivos têm uma configuração
  aceitável antes de tentar aplicá-los.
- **Reload** solicita ao serviço que adote sua configuração.
- Renovar HTTPS não retreina o modelo nem publica código novo.

**Se perguntarem “certificado vencido muda a previsão?”** Não muda o cálculo,
mas pode impedir a conexão confiável do visitante ao site.

</details>

**Função:** executa a verificação de renovação do certificado e valida/recarrega
o Nginx.

**Quem usa:** o service do systemd, acionado periodicamente pelo timer.

**Como explicar:** “Mantém a validade da entrada HTTPS ao longo do tempo.”

### `scripts/verificar-deploy.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Smoke test** é uma checagem curta do caminho essencial.
- **Liveness** pergunta se o processo responde. **Readiness** pergunta se está
  pronto para a tarefa; aqui, precisa ter modelo carregado.
- **Timeout** limita o tempo de espera de uma operação.

**Se perguntarem “isso verifica tudo?”** Não. Os casos detalhados estão na
suíte; essa rotina verifica o caminho essencial da instalação.

</details>

**Função:** faz um smoke test HTTP da instalação: verifica prontidão do modelo,
metadados, saúde do Streamlit e uma previsão. Se o PostgreSQL estiver
configurado, busca `8888-XEBO` no banco e usa seus atributos.

**Como explicar:** “Não basta o contêiner existir. Esta rotina verifica se uma
consulta e uma previsão conseguem ser respondidas.”

**Limite:** ele só comprova uma instalação quando é executado contra ela.
A existência do script no GitHub não é prova de que o serviço público está
rodando.

## 7. `src/churn/`

É o pacote Python ativo. O GitHub mostra primeiro suas subpastas `api/` e
`frontend/`; depois aparecem os módulos de configuração e treinamento.

### `src/churn/api/static/index.html`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **HTML** descreve os elementos da página; **CSS** define sua apresentação.
- **JavaScript** lê o formulário e envia o pedido.
- **JSON** é um formato textual de dados, como `{"tenure":12}`.
- **POST** é o método HTTP usado para enviar os atributos no corpo do pedido;
  **GET** é usado nas rotas de consulta do projeto.

**Se perguntarem “quem prevê?”** O JavaScript envia a mensagem; o processo
FastAPI executa o modelo e devolve o resultado.

</details>

Dentro de `api/`, a pasta `static/` aparece antes dos arquivos Python.

**Função:** formulário HTML alternativo, servido em `GET /` da API local.
Permite digitar os 19 atributos manualmente; o JavaScript envia `POST /prever`
e apresenta a resposta.

**Como explicar:** “Este é um cliente simples da API para preencher atributos
manualmente. A interface de consulta por código é feita com Streamlit.”

### `src/churn/api/__init__.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Módulo** é uma unidade de código Python, normalmente um arquivo `.py`.
- **Pacote** organiza módulos sob um nome, como `churn.api`.
- **Importar** disponibiliza código de outro módulo. Aqui se expõe `app`.

**Se perguntarem “quem recebe a rede?”** O Uvicorn inicia o servidor usando
a aplicação FastAPI de `aplicacao.py`.

</details>

**Função:** identifica o pacote da API e reexporta a instância `app`.

**Como explicar:** “É a entrada do pacote Python da API; as rotas estão no
arquivo seguinte.”

### `src/churn/api/aplicacao.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **API** é a interface pela qual um programa pede algo a outro. Aqui usa HTTP:
  um pedido chega a uma rota e recebe uma resposta.
- **Endpoint/rota** combina endereço e método, como `POST /prever`.
- **FastAPI** organiza rotas, validação e documentação; **Uvicorn** é o servidor
  que atende conexões e executa essa aplicação.
- **Código HTTP** resume a resposta: 200, sucesso; 403, operação proibida;
  422, entrada fora do contrato; 500, falha interna; 503, indisponibilidade.
- **Lifespan** é o ciclo de inicialização/encerramento. Carrega o modelo uma vez
  por processo. **Threadpool** é um grupo de linhas de execução para atender
  funções bloqueantes sem rodá-las diretamente no loop assíncrono.
- **Thread** é uma linha de execução dentro do processo. **Bloqueante** é uma
  operação que ocupa essa execução até terminar.
- **Loop assíncrono** coordena tarefas e suas esperas; permite avançar em outras
  tarefas enquanto uma operação aguarda. Não torna um cálculo pesado paralelo
  automaticamente. Aqui a previsão síncrona é executada no threadpool.

**Se perguntarem “por que separar API e tela?”** A API oferece um contrato
que pode atender vários clientes, além daquela interface.

**Se perguntarem “estar vivo é estar pronto?”** `/saude` pode responder mesmo
com `modelo_carregado=false`. `/pronto` exige o modelo para prever.

**Para conferir:** [FastAPI e pedidos HTTP](https://fastapi.tiangolo.com/tutorial/body/) · [Execução concorrente no FastAPI](https://fastapi.tiangolo.com/async/).

</details>

**Função:** cria o FastAPI, carrega o serviço na inicialização e define as
rotas. A dependência `obter_servico` impede a previsão quando o modelo está
indisponível.

| Método e rota | Papel |
| --- | --- |
| `GET /` | Formulário HTML de entrada manual |
| `GET /docs` | Swagger/OpenAPI da API local |
| `GET /saude` e `GET /health` | Processo HTTP responde; mostra se há modelo |
| `GET /pronto` | 200 quando o modelo está carregado; 503 sem ele |
| `GET /modelo` | Nome, versão, alias, origem e limiar do serviço |
| `GET /clientes?codigo=8888-XEBO` | Busca os atributos no PostgreSQL |
| `POST /prever` | Recebe atributos e calcula classe e score |
| `POST /modelo/recarregar` | Tenta carregar uma versão novamente; bloqueada quando desabilitada |

`/saude` e `/pronto` respondem a perguntas diferentes: “o processo responde?”
e “o modelo está disponível?”. O Compose usa `/pronto` como healthcheck.

Entrada inválida pode causar 422; falta do serviço do modelo causa 503; erro
durante a execução da previsão é tratado com 500. A recarga desabilitada retorna
403. As rotas síncronas executam o trabalho bloqueante no threadpool do FastAPI.

**Como explicar:** “Aqui estão o contrato de acesso à aplicação e os caminhos
HTTP para consultar, prever e verificar o serviço.”

### `src/churn/api/clientes.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **SELECT** é a instrução SQL de consulta.
- **Consulta parametrizada** envia a instrução separada do valor do código.
  O valor ocupa um parâmetro, em vez de ser concatenado como SQL.
- **Injeção de SQL** ocorre quando uma entrada passa a ser interpretada como
  instrução. A separação entre consulta e valor ajuda a impedir isso.
- **DSN** é a configuração de conexão. Aqui ela é lida de um arquivo montado,
  não escrita com a senha no módulo.

**Se perguntarem “essa busca atualiza o modelo ou o cliente?”** O módulo
consulta atributos; não grava uma previsão nem executa treinamento.

**Para conferir:** [Parâmetros SQL no Psycopg](https://www.psycopg.org/psycopg3/docs/basic/params.html).

</details>

**Função:** busca o registro no PostgreSQL com SQL parametrizado. Normaliza o
código, aplica timeouts e devolve somente os campos definidos no contrato
de consulta.

O `customerID` identifica o registro; o rótulo real `Churn` não é devolvido como
atributo de previsão.

**Como explicar:** “É a ligação entre a API e o banco privado. O código recebido
serve para localizar os atributos do cliente.”

### `src/churn/api/esquemas.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Schema/contrato**, aqui, declara campos, tipos e valores permitidos da
  mensagem. Não é o espaço `public` do banco.
- **Pydantic** valida os objetos conforme a declaração. `Literal` restringe
  categorias; `Field` declara faixas; `extra="forbid"` rejeita campos extras.
- **Payload** é o conteúdo enviado na requisição. Para `/prever`, são os
  19 atributos, sem ID e sem a resposta real.

**Se perguntarem “por que rejeitar customerID?”** A localização do cliente
já aconteceu; a previsão recebe atributos, não um identificador.

**Para conferir:** [Modelos Pydantic](https://docs.pydantic.dev/latest/concepts/models/).

</details>

**Função:** declara modelos Pydantic para o JSON de entrada e as respostas.

`ClienteChurn` exige os 19 atributos, com tipos, faixas e categorias. Campos
extras são rejeitados. `ClienteConsulta` acrescenta o ID à resposta de busca.
Os outros modelos descrevem previsão, saúde e metadados do modelo.

| Grupo de atributos | Campos |
| --- | --- |
| Perfil | `gender`, `SeniorCitizen`, `Partner`, `Dependents` |
| Tempo, contrato e cobrança | `tenure`, `Contract`, `PaperlessBilling`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges` |
| Telefonia | `PhoneService`, `MultipleLines` |
| Internet e adicionais | `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies` |

**Como explicar:** “Define exatamente o que a API aceita e devolve. Isso evita
que entrada inesperada seja interpretada silenciosamente.”

### `src/churn/api/servico.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Inferência** aplica o modelo treinado a uma entrada.
- **Score** é o número produzido pelo modelo. Usamos o score da classe churn
  de `predict_proba` como probabilidade estimada.
- **Limiar** é o corte de decisão: com 0,50, score 0,60 vira `Yes` e 0,20 vira
  `No`. Alterar o corte não treina outra floresta.
- No scikit-learn, a floresta calcula a média das probabilidades das árvores.
  Cada árvore estima pela proporção de classes na folha alcançada.
  Não é apenas contar quantas árvores disseram “sim”.
- **Calibração** verifica se scores correspondem a frequências reais.
  Por exemplo, em um conjunto adequado com scores próximos de 60%, deveria
  haver aproximadamente 60% de cancelamentos. Isso não foi demonstrado aqui.

**Se perguntarem “60% é a acurácia?”** Não. É a estimativa daquela entrada.
Acurácia compara várias decisões com seus rótulos reais.

**Borda da regra da API:** valor exatamente no corte recebe `Yes`, pois usa
`>=`. O `predict` nativo da biblioteca tem seu próprio desempate entre classes.

**Para conferir:** [Probabilidades da Random Forest](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier.predict_proba).

</details>

**Função:** carrega o pipeline e mantém modelo, origem, versão e limiar em
`ServicoChurn`. Para prever, monta um DataFrame, chama `predict_proba` e encontra
a probabilidade da classe 1 em `classes_`.

Há dois caminhos de carga:

- Com `MODELO_URI`: usa o pacote exportado e lê seus metadados de `deploy.json`.
- Sem ele: resolve o alias no Registry e carrega a versão numérica consultada.

A regra individual é `probabilidade >= limiar`. O padrão é 0,50. Uma resposta
`{"churn":"Yes","probabilidade":0.60,"limiar":0.50}` significa que o score passou
do corte; não significa acurácia de 60% nem certeza de cancelamento.

**Como explicar:** “É o componente que tem o modelo em memória e executa a
previsão. Cada clique usa esse modelo, sem refazer o treinamento.”

### `src/churn/frontend/__init__.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Frontend** é a camada de interação com o usuário.
- **Backend** é o serviço que executa a lógica solicitada pela interface.
- Streamlit é a interface; FastAPI é o backend no modo API. O Python do
  Streamlit também roda no servidor: frontend não significa que todo o seu
  código execute no navegador.

**Se perguntarem “o modelo vai para o visitante?”** Não nesse desenho. A página
é mostrada no navegador e o cálculo acontece no processo configurado.

</details>

Agora abra a pasta `frontend/`.

**Função:** identifica o pacote Python da interface.

**Como explicar:** “Organiza os módulos que cuidam da tela e de sua comunicação
com o modelo ou com a API.”

### `src/churn/frontend/app.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Estado de sessão** guarda informações daquela interação de usuário, como
  a consulta que precisa continuar aparecendo.
- **Cache** reaproveita resultados para evitar trabalho repetido.
  `cache_data` atende aos dados; `cache_resource` conserva recursos como o
  modelo no processo do modo local.
- **Reexecução da tela** é o comportamento do Streamlit ao interagir; não
  significa executar `fit` ou treinar outra floresta.
- As chamadas HTTP saem do processo Streamlit para a API interna.

**Se perguntarem “pode continuar mostrando o cliente anterior?”** O código
limpa/atualiza o estado ao trocar de modo ou realizar outra consulta. Os testes
exercitam consultas sucessivas.

**Para conferir:** [Cache no Streamlit](https://docs.streamlit.io/develop/concepts/architecture/caching).

</details>

**Função:** monta o Streamlit, recebe o código do cliente, dispara a consulta e
mostra informações e resultado. Usa estado de sessão para manter a consulta na
tela e caches para dados/modelo quando aplicável.

| Configuração da interface | Comportamento |
| --- | --- |
| `CHURN_API_URL` | Endereço de backend usado nas chamadas |
| `CHURN_MODO_INFERENCIA` | Escolha inicial entre inferência local e API |
| `CHURN_MODO_PUBLICO` | Força modo API e esconde URL/controles de recarga |
| `CHURN_CLIENTES_VIA_API` | Busca clientes pela API em vez de abrir o CSV |

**Como explicar:** “É a tela que o usuário vê. Ela recebe a consulta e mostra a
resposta da inferência.”

### `src/churn/frontend/dados.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **DataFrame** é uma tabela do pandas, com linhas e colunas.
- **Serializar para JSON** é representar os dados no formato textual da
  mensagem. Tipos numéricos são preparados para essa representação.
- **Tradução de apresentação** muda o texto visível, como `Female` para
  `Feminino`, sem mudar a categoria enviada ao modelo.

**Se perguntarem “por que não enviar a linha inteira?”** Ela traz ID e alvo
real. O payload seleciona só o que o contrato da previsão exige.

</details>

**Função:** carrega os clientes no modo CSV, busca o código sem diferenciar
maiúsculas e monta o payload de 19 campos. Remove identificador e alvo, converte
tipos numéricos e traduz valores apenas para apresentação na tabela.

**Como explicar:** “Pega o registro escolhido e o transforma na entrada da API.
O dado conhecido de cancelamento não é enviado ao modelo.”

### `src/churn/frontend/inferencia.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Inferência local** significa calcular no processo Streamlit. Não significa
  enviar o modelo para o navegador.
- **Contrato de resposta** é o conjunto dos campos devolvidos: `churn`,
  `probabilidade` e `limiar`.

**Se perguntarem “API e modo local precisam de regras diferentes?”** Podem
usar a mesma versão e compartilham a regra de decisão; muda onde executam e
como se chega ao serviço.

</details>

**Função:** permite que o próprio Streamlit carregue e consulte o modelo no
modo local. Reaproveita `ServicoChurn` e devolve o mesmo formato de resposta da
API.

**Como explicar:** “Oferece uma alternativa de execução local. No Compose e no
perfil público, a inferência é feita pela FastAPI.”

### `src/churn/__init__.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Pacote Python** agrupa módulos sob o nome `churn`.
- Este arquivo participa da organização/importação; não contém uma instrução
  para treinar ou subir serviços.
- O prefixo `churn.` identifica onde encontrar os módulos.

**Se perguntarem “um arquivo vazio não serve para nada?”** Pode ter função
na organização do pacote sem possuir lógica de negócio.

</details>

Volte a `src/churn/` para os arquivos que vêm depois das duas subpastas.

**Função:** identifica o pacote principal. Está vazio.

**Como explicar:** “Marca a organização do código como pacote Python.”

### `src/churn/configuracao.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Configuração** é um valor de ambiente separado da lógica, como caminho ou
  limiar.
- **Variável de ambiente** é um valor disponibilizado ao processo ao iniciá-lo.
  `LIMIAR_CHURN=0.7` pode trocar o corte usado pela API.
- **Path/pathlib** representa caminhos de arquivos. Permite construir o
  caminho da base sem fixar a pasta de uma pessoa.
- **URI** identifica um recurso. Uma URL HTTP é uma forma de referência;
  `sqlite:///...` e `models:/churn/1` têm significados diferentes.

**Se perguntarem “.env é lido automaticamente por qualquer Python?”** Não.
O Compose lê o arquivo para sua configuração; a classe atual não declarou
`env_file` e recebe variáveis do ambiente do processo.

</details>

**Função:** centraliza caminhos e parâmetros com Pydantic Settings. Calcula a
raiz do projeto a partir do arquivo, permitindo construir o caminho do CSV sem
depender de uma pasta específica de uma pessoa.

| Configuração | Uso |
| --- | --- |
| `CAMINHO_DADOS` | Arquivo de entrada do treino/consulta Python |
| `MLFLOW_TRACKING_URI` | Backend do Tracking e Registry; SQLite por padrão |
| `NOME_MODELO` e `ALIAS_MODELO` | Identidade consultada no Registry |
| `MODELO_URI` | Pacote já exportado para execução |
| `LIMIAR_CHURN` | Corte individual entre 0 e 1 |
| `RECARGA_MODELO_HABILITADA` | Permissão da rota de recarga |
| `POSTGRES_CLIENTES_DSN_ARQUIVO` | Caminho do arquivo de conexão ao banco |

**Como explicar:** “Reúne as escolhas de ambiente em um lugar, em vez de
espalhar caminhos e configurações pelo código.”

### `src/churn/dados.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Leitura** leva a tabela do arquivo para um objeto de trabalho.
- **Validação** confere regras declaradas e pode interromper a execução.
  Não é ensinar o modelo nem escolher uma configuração.
- **Conversão de tipo** permite interpretar `"100.5"` como número, não texto.
- **lazy=True**, aqui, reúne violações. Não significa “pular a validação”.

**Se perguntarem “por que validar uma base pronta?”** Para manter um contrato
se o arquivo for alterado. Não é uma entrega sua de preparação da base.

</details>

**Função:** `carregar_dados` lê o CSV; a função chamada `limpar_dados` aplica os
ajustes de representação que o código já mantém e verifica o contrato Pandera.
Na busca de experimentos, essa chamada é usada como barreira de validação.

A base foi fornecida preparada. Esta etapa protege a entrada do treino se
chegar um arquivo alterado ou incompatível; não é uma atividade de tratamento
da base que você precise apresentar como trabalho seu.

**Como explicar:** “Lê a base da disciplina e confere se ela atende às regras
esperadas antes de começar o treinamento.”

<a id="treinamento-e-mlflow"></a>

### `src/churn/experimentos.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Modelo treinado** é o objeto cujo estado foi ajustado usando exemplos.
- **Treino** ajusta padrões; **validação** compara escolhas; **teste** mede a
  escolha final em dados reservados.
- **Hiperparâmetro** é uma escolha antes do ajuste, como quantidade de árvores.
  Os pontos de divisão que uma árvore aprende fazem parte do estado aprendido.
- **Grid** é o conjunto de combinações: 3 quantidades × 3 profundidades = 9.
- **Estratificar** preserva aproximadamente as proporções de `Yes/No` nas
  partições. Não é uma separação temporal.
- **Semente (seed)** inicia o gerador pseudoaleatório. `42` fixa o sorteio;
  não é uma configuração “mais inteligente”. Reproduzir também depende dos
  dados, das versões e de outras condições.
- **Overfitting** é ajustar muito bem ao treino e generalizar pior.
  Profundidade limita parte da complexidade; acerto alto no treino sozinho
  não demonstra desempenho em dados reservados.

**Métricas usando os clientes do seu teste:**

- **Positivo** é churn. **Verdadeiro positivo**: alertou e cancelou (274).
- **Falso positivo**: alertou e permaneceu (137).
- **Falso negativo**: cancelou sem alerta (184).
- **Verdadeiro negativo**: permaneceu e não foi sinalizado (814).
- **Acurácia:** `(274 + 814) / 1409 = 77,22%`; todos os acertos.
- **Recall/sensibilidade:** `274 / (274 + 184) = 59,83%`; os cancelamentos
  encontrados.
- **Precisão:** `274 / (274 + 137) = 66,67%`; os alertas corretos. Nesse
  contexto, precisão não é sinônimo de acurácia.
- **F1:** média harmônica de precisão e recall,
  `2 × precisão × recall / (precisão + recall)`. Penaliza um deles ficar baixo.
- **ROC:** relaciona recall e a taxa de falsos positivos ao variar o corte.
  **AUC:** área sob essa curva, que resume a ordenação dos scores.
  AUC 0,8269 corresponde a cerca de 83% de pares bem ordenados entre um
  cancelamento e uma permanência, com meio crédito para empate.
- **Matriz de confusão:** tabela dos quatro tipos de resultado.

**Se perguntarem “por que não escolher pelo teste?”** Isso usaria os dados de
teste para decidir a configuração. Aqui, a validação escolhe e o teste mede e
aplica o mínimo de promoção ao candidato já selecionado.

**O que são runs e experimentos?** Um run é uma execução registrada; um
experimento agrupa runs. A busca padrão tem um pai e nove filhos.

**Params, metrics, tags, artifacts:** escolhas de entrada, medições,
metadados e arquivos gerados. `git_commit` é uma tag; acurácia é uma métrica;
o pipeline salvo é um artefato. **SQLite** guarda metadados locais do MLflow;
não é o banco de clientes da aplicação.

**Para conferir:** [Partições de avaliação](https://scikit-learn.org/1.7/modules/cross_validation.html) · [Métricas de classificação](https://scikit-learn.org/1.7/modules/model_evaluation.html) · [Tracking no MLflow](https://mlflow.org/docs/latest/ml/tracking/).

</details>

**Função:** é o comando principal para treinar, comparar, avaliar e registrar.

1. Lê a base e verifica o contrato.
2. Separa `customerID` e `Churn` dos 19 atributos; transforma o alvo em 0/1.
3. Divide 60% para treino, 20% para validação e 20% para teste, com
   estratificação e semente 42. São 4.225 / 1.409 / 1.409 registros.
4. Compara nove configurações: árvores em 100/200/500 e profundidade livre/8/16.
5. Escolhe a maior ROC AUC de validação. Empate mantém a primeira configuração
   na ordem do `ParameterGrid`.
6. Mede apenas a configuração escolhida no teste reservado.
7. Registra uma versão de `churn` e muda `champion` se `test_roc_auc >= 0.80`.
   Caso contrário, mantém o alias anterior.

**Por que dividir?** Treino ensina os padrões; validação escolhe a configuração;
teste avalia o modelo escolhido com dados reservados. O vencedor não é
retreinado juntando treino e validação nessa implementação.

**O que o MLflow guarda?** Um run pai da busca, nove runs filhos, parâmetros,
métricas, pipelines e as tags `data_sha256` e `git_commit`. Só o filho vencedor
recebe métricas de teste. `selecao.json` registra a decisão no run pai.

**Como explicar:** “Este é o centro da experimentação. Aqui escolho o modelo
por um critério definido e guardo as condições que geraram cada resultado.”

**Resultados na base da disciplina:**

| Medida | Valor e significado |
| --- | --- |
| Configuração escolhida | 500 árvores e profundidade máxima 8 |
| ROC AUC na validação | 0,8216; foi o critério para escolher a configuração |
| ROC AUC no teste | 0,8269; capacidade de ordenar o risco no teste |
| Acurácia no teste | 77,22%; 1.088 classificações corretas de 1.409 |
| Recall de churn | 59,83%; identificou 274 dos 458 cancelamentos |
| Precisão dos alertas | 66,67%; 274 dos 411 alertas eram cancelamentos |
| F1 | 0,6306; combina precisão e recall |

A acurácia inclui clientes que permaneceram. Prever “não cancela” para todos
já acertaria 67,49% do teste e não sinalizaria nenhum cancelamento. No resultado
do modelo, 184 cancelamentos passaram sem alerta e houve 137 falsos alarmes.

**Como falar do resultado:** “O modelo ajuda a ordenar o risco, mas não encontra
todos os cancelamentos: identificou 274 dos 458 casos do teste.”

O limite 0,80 é um mínimo para promover o modelo. É diferente do corte individual
de 0,50 e não compara automaticamente o candidato com um champion anterior.

### `src/churn/exportar.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Registry** é o catálogo de modelos e versões; **Tracking** é o registro
  das execuções que produziram os resultados.
- **Alias** é um nome que aponta para uma versão. `champion` pode apontar
  para `1` hoje e `2` amanhã.
- **Exportar** copia uma versão resolvida para um pacote. Não executa `fit`
  nem encontra outro modelo melhor.
- **Serialização** transforma o objeto ajustado em arquivos carregáveis depois.
  O projeto usa `cloudpickle` no pacote MLflow.
- **Assinatura** descreve entrada/saída do modelo; não é a assinatura
  criptográfica de um certificado.
- **Metadados** descrevem o objeto. `deploy.json` identifica a origem do pacote;
  ele não contém a implementação da floresta.

**Se perguntarem “o site muda junto com o alias?”** Não no modo de pacote
fixado na imagem. É necessário exportar e publicar outra versão.

**Para conferir:** [Versões e aliases no Registry](https://mlflow.org/docs/latest/ml/model-registry/).

</details>

**Função:** resolve o alias `champion` no Registry, baixa a versão numérica e
gera o pacote `artifacts/modelo`. Verifica `predict_proba` e a classe 1.

Acrescenta `deploy.json` com nome, versão, alias, origem e `run_id`. Recusa
sobrescrever uma pasta de destino existente.

**O que é o alias?** Um ponteiro para uma versão, como `models:/churn@champion`.
Uma URI como `models:/churn/1` fixa a versão 1. A exportação transforma essa
escolha em um pacote que acompanha a imagem.

**Como explicar:** “O servidor recebe uma versão identificada do modelo. Ele
consegue prever sem acessar o banco local de experimentos do meu computador.”

Mudar o alias no MLflow não atualiza um pacote já incluído na imagem. Para servir
outra versão, é necessário exportar e publicar o pacote pretendido.

### `src/churn/mlflow.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Commit** é um registro de estado no histórico Git, com identificador.
- **Linhagem** liga dados, código, execução e modelo.
- Esse helper consulta o Git; o comando de experimentos utiliza a informação
  ao registrar o run.

**Se perguntarem “o commit sozinho reproduz tudo?”** Ele identifica código;
ainda precisamos da base, dependências e configurações correspondentes.

</details>

**Função:** `git_commit` consulta o hash do commit do código pelo Git local.

**Quem usa:** `experimentos.py`, para registrar a origem do código junto ao run.

**Como explicar:** “Esse helper liga o experimento a uma versão do código.
O hash do CSV identifica os dados e o commit identifica a implementação.”

O clone traz o histórico `.git`; o Download ZIP traz código e dados, mas não
traz esse histórico. A consulta do commit depende do Git disponível no ambiente.

### `src/churn/pipeline.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Pipeline** conecta etapas num objeto que transforma a entrada e aplica
  o classificador.
- **fit** ajusta a partir dos exemplos; **transform** aplica transformações;
  **predict** devolve classes; **predict_proba** devolve scores por classe.
- **Imputação** substitui ausência por valor. **Moda** é o mais frequente;
  **mediana** é o valor central após ordenar.
- **One-hot** cria indicadores das categorias: contrato mensal pode ter uma
  coluna com 1, com outras categorias em 0.
- **Árvore de decisão** aprende perguntas que dividem grupos de exemplos.
  Uma **folha** é o grupo final atingido.
- **Random Forest** combina várias árvores construídas com sorteios de dados
  e atributos. A média das estimativas reduz dependência de uma única árvore.
- **Profundidade** limita os níveis de cada árvore. 500 árvores não significa
  500 camadas numa árvore só.
- **n_jobs=-1** permite usar os processadores disponíveis na execução da
  biblioteca.
- **Vazamento de dados** é usar informação que não deveria participar do
  aprendizado/seleção. Por isso os ajustes de valores e categorias usam só
  os exemplos de treino.

**Se perguntarem “a API faz one-hot por conta própria?”** Não. Entrega os
atributos ao objeto que já tem as etapas ajustadas.

**Para conferir:** [Pipeline no scikit-learn](https://scikit-learn.org/1.7/modules/compose.html) · [Florestas aleatórias](https://scikit-learn.org/1.7/modules/ensemble.html#forest).

</details>

**Função:** cria o objeto que reúne a representação numérica da entrada e o
classificador. Os ajustes que aprendem valores/categorias são feitos no treino,
e o mesmo objeto é usado na previsão.

Contém a característica derivada `gasto_por_mes`, imputadores, one-hot e Random
Forest. A API recebe os 19 campos originais; não precisa receber a característica
calculada internamente.

**Detalhes para responder se perguntarem:** `gasto_por_mes` usa
`TotalCharges / (tenure + 1)`; categóricas usam moda e one-hot; numéricas usam
mediana. `TotalCharges` ausente/inválido recebe 2.200. A floresta usa semente 42
e `n_jobs=-1`.

Esses são comportamentos do código. A explicação principal é que as mesmas
transformações acompanham o modelo, evitando reconstruí-las manualmente na API.

**Como explicar:** “O modelo exportado é o pipeline completo. Assim a entrada
recebe a mesma sequência de transformações ao treinar e ao prever.”

### `src/churn/schema.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Pandera** verifica regras sobre tabelas pandas.
- **Schema**, aqui, é contrato de colunas, tipos e regras. Não é o espaço
  `public` do banco nem é um modelo preditivo.
- **ge/le** significam maior/menor ou igual. **isin** limita valores a uma lista.
- **coerce=True** tenta converter tipos; **strict=False** permite colunas
  extras, sem liberar valores proibidos nas colunas verificadas.

**Se perguntarem “isso prova que o dado está perfeito?”** Só verifica as regras
efetivamente declaradas; não cobre todos os aspectos de qualidade de dados.

**Para conferir:** [Contratos Pandera](https://pandera.readthedocs.io/en/stable/dataframe_models.html).

</details>

**Função:** declara o contrato Pandera de cinco colunas verificadas no treino:
faixas de `tenure` e cobranças, categorias de `Contract` e valores do alvo.

`coerce=True` permite converter tipos e `strict=False` aceita colunas extras.
Com `lazy=True`, as violações são reunidas em vez de parar na primeira.

**Como explicar:** “Define as regras que o arquivo de entrada precisa respeitar.
É validação do contrato, não uma nova entrega de preparação de dados.”

**Limites do contrato:** o schema do treino cobre cinco colunas; a API tem seu
contrato Pydantic para os 19 campos. O one-hot pode tratar uma categoria nova
internamente, mas ela pode ser rejeitada antes pela API. Também existe uma
diferença conhecida: o frontend converte `TotalCharges` ausente em 0,0 antes
do envio, enquanto o pipeline do treino usa 2.200.

## 8. `tests/`

É a suíte automatizada. Os arquivos seguem a configuração do pytest e
verificam partes do comportamento antes de publicar uma alteração.

### `tests/teste_api.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Teste automatizado** executa um cenário e verifica o resultado esperado.
- **TestClient** chama a aplicação em ambiente de teste, sem precisar da EC2.
- **Assert** verifica uma condição e faz o caso falhar se ela não for atendida.
- **Substituição controlada** força situações como falta de modelo para conferir
  a resposta; não mede a qualidade preditiva de um modelo de negócio.

**Se perguntarem “esses testes provam a ROC AUC?”** Conferem contrato e
comportamento da API. O desempenho na disciplina vem da avaliação do treino.

</details>

Verifica saúde, prontidão, formulário, contrato de entrada, resposta de previsão,
metadados e recarga. Há modelos pequenos e dependências substituídas para
controlar os cenários.

**Como explicar:** “Confere se a API aceita os dados certos e responde
corretamente, inclusive quando o modelo está indisponível.”

### `tests/teste_configuracao.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Valor padrão** é usado quando nenhuma configuração substitui aquele valor.
- O teste confere o caminho da base a partir da raiz do projeto.

**Se perguntarem “por que verificar um caminho?”** Um endereço errado impede
carregar a base mesmo com o arquivo corretamente incluído na entrega.

</details>

Confere o caminho padrão da base da disciplina.

**Como explicar:** “Evita que o padrão do projeto passe a apontar para um
arquivo ou diretório errado.”

### `tests/teste_dados.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Amostra de teste** é uma tabela pequena montada para verificar um cenário.
- **Exceção esperada** é a rejeição que uma entrada incompatível deve produzir.
- **failure_cases** detalha quais regras do Pandera foram violadas.

**Se perguntarem “gerou um erro e o teste passou?”** Passa se o comportamento
esperado era rejeitar aquela entrada ruim. Falharia se ela fosse aceita.

</details>

Verifica leitura do CSV, conversão dos campos prevista no código e violações do
contrato Pandera. O caso inválido reúne erros de várias colunas com `lazy=True`.

**Como explicar:** “Confere que a entrada é lida e que um arquivo incompatível
seja detectado antes do treino.”

### `tests/teste_experimentos.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Fixture/tmp_path** fornece recursos temporários ao teste.
- **monkeypatch** troca uma dependência durante o teste e restaura ao fim.
  Ajuda a forçar métricas para verificar escolhas.
- **Integração** combina componentes, como Registry em SQLite, exportação e
  recarga. Isso ainda não prova uma instalação na EC2.

**Se perguntarem “por que métricas controladas?”** Para provocar aprovação e
reprovação previsíveis e verificar a versão/alias. As métricas reais são
medidas no treinamento com a base.

</details>

Verifica seleção, separação entre validação e teste, mínimo de promoção,
Registry, carga e exportação do modelo. Usa SQLite temporário e modelos pequenos;
as métricas são controladas nos cenários de decisão.

**Como explicar:** “Testa se a lógica escolhe e registra o modelo corretamente.
As métricas finais da disciplina vêm do treino com o CSV, não desses cenários.”

### `tests/teste_frontend.py`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **AppTest** executa o script Streamlit em teste e simula interação com campos.
- **HTTP simulado** devolve respostas controladas sem acessar o servidor real.
- **Parametrizar** repete um cenário com valores diferentes, como modo público
  ligado/desligado.

**Se perguntarem “41 casos são 41 arquivos?”** Não. Uma função parametrizada
pode gerar vários casos.

</details>

Verifica busca por código, montagem dos 19 campos, apresentação e regra de
inferência local. O AppTest do Streamlit simula respostas HTTP para testar
consultas sucessivas.

**Como explicar:** “Confere a passagem do cliente escolhido até a resposta
mostrada na tela.”

A suíte ativa tem 41 casos e passou na reorganização. Testes com HTTP simulado
não comprovam o banco ou o site remoto. O smoke test em `scripts/` atende a
essa outra situação quando executado contra uma instalação real.

## 9. Arquivos da raiz

Depois das pastas, continue nos arquivos abaixo, na ordem da listagem.

### `.dockerignore`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Contexto de build** é o conjunto de arquivos disponível durante a construção.
- **Padrão de exclusão** retira caminhos do contexto; exceções com `!` permitem
  incluir os caminhos previstos.
- Contexto Docker e versionamento Git são seleções independentes.

**Se perguntarem “ignorar apaga o arquivo?”** Não. Muda sua inclusão no
contexto, não sua existência no computador.

</details>

**Função:** seleciona o que fica fora do contexto enviado ao Docker no build.
Exclui ambientes, caches, histórico, dados e arquivos de apoio; reinclui
`artifacts/modelo` para a imagem da aplicação.

**Como explicar:** “O build recebe só o contexto necessário. O modelo exportado
entra na imagem; os dados da consulta local são montados separadamente.”

### `.gitattributes`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **LF/CRLF** são representações diferentes de quebra de linha.
- **Atributo Git** controla tratamentos como conversão de texto.
- `-text` impede a normalização do CSV. Se os bytes mudarem, o hash também
  pode mudar, mesmo que a tabela pareça igual.

**Se perguntarem “isso melhora acurácia?”** Não. Preserva compatibilidade e
identidade do arquivo; não é uma escolha estatística.

</details>

**Função:** padroniza fins de linha de scripts e receitas para funcionar entre
Windows e Linux. Para o CSV, desliga conversão de texto para preservar os
bytes e o hash original.

**Como explicar:** “Protege a compatibilidade dos scripts e a identidade da base.”

### `.gitignore`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Versionar/rastrear** é registrar um arquivo no histórico.
- **Ignore** orienta a seleção de arquivos ainda não rastreados. Não remove
  automaticamente algo que já foi registrado.
- **Artefato gerado** é uma saída de execução, como o pacote exportado.

**Se perguntarem “por que CSV entra e modelo não?”** O CSV é uma entrada
fixada da disciplina. O modelo é produzido e identificado pelo fluxo de
treinamento/exportação.

</details>

**Função:** define o que fica fora do versionamento: ambientes, saídas, modelos,
banco de experimentos e arquivos de configuração local. Abre exceção apenas
para o CSV original em `data/raw/churn.csv` entre os dados do projeto.

**Diferença importante:** ignorar no Git não exclui automaticamente do Docker.
Por isso o modelo pode ficar fora do Git e ser incluído na imagem, enquanto
o CSV fica no Git e é excluído do contexto da imagem da aplicação.

### `Dockerfile.api`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Dockerfile** é receita; **imagem** é o pacote construído; **contêiner**
  é uma execução isolada dele.
- **Build** lê a receita; **camadas** permitem reaproveitar partes correspondentes
  da construção quando seus insumos não mudam.
- **Kernel** é o núcleo do sistema operacional que gerencia processos e recursos.
  Contêineres usam o kernel de seu ambiente; não são máquinas virtuais inteiras.
  No desenho AWS, as EC2 hospedam os contêineres.
- **Root** é o usuário administrador Linux. A aplicação usa usuário sem esse
  privilégio.
- **EXPOSE** documenta a porta; publicá-la depende da execução, aqui o Compose.

**Se perguntarem “uma imagem vira duas aplicações?”** O conteúdo é o mesmo;
o comando do backend inicia Uvicorn e o do frontend inicia Streamlit.

**Para conferir:** [Imagem Docker](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/) · [Contêiner e máquina virtual](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/).

</details>

**Função:** receita da imagem compartilhada de FastAPI e Streamlit. Usa Python
3.12, instala `requirements.runtime.txt`, copia código e modelo exportado e
cria um usuário sem root.

**Quem usa:** `compose.yaml`, por `dockerfile: Dockerfile.api`.

**Como explicar:** “Define o ambiente e os arquivos da aplicação. A mesma imagem
inicia dois contêineres, um para a API e outro para o Streamlit.”

Imagem é o pacote; contêiner é a execução. O pacote `artifacts/modelo` precisa
existir antes do build.

### `Dockerfile.postgres`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Imagem-base** é o ponto de partida da receita.
- **Inicialização do banco** cria estrutura e carrega registros quando o
  diretório de dados está vazio.
- A imagem leva arquivos iniciais; dados produzidos durante a operação precisam
  do armazenamento persistente previsto.

**Se perguntarem “o modelo está aqui?”** Não. Esta imagem inicializa clientes;
o pacote preditivo fica na imagem da aplicação.

</details>

**Função:** receita separada da imagem PostgreSQL. Inclui o CSV da disciplina e
`deploy/postgres/iniciar.sql` para inicializar o banco de clientes.

**Como explicar:** “Esta é a imagem do banco; não é a imagem da aplicação.
A carga inicial cria os clientes a partir do CSV.”

### `Dockerfile.postgres.dockerignore`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Contexto específico** permite fornecer os insumos dessa receita.
- `**` exclui caminhos; exceções reincluem CSV e SQL.
- O build do banco não precisa do ambiente de treino Python.

**Se perguntarem “por que outro dockerignore?”** Porque essa imagem precisa
de arquivos que não são os mesmos da aplicação.

</details>

**Função:** lista de inclusão do contexto específico da imagem PostgreSQL:
CSV e SQL. Ela atende a um build que precisa dos dados.

**Como explicar:** “As duas imagens precisam de arquivos diferentes.
A aplicação leva o modelo; a imagem do banco leva a base para sua carga inicial.”

### `LICENSE`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Licença** é o texto com os termos declarados de uso do código.
- O arquivo não instala uma biblioteca nem altera a previsão. O README
  distingue o código da base fornecida na disciplina.

**Se perguntarem “qual é sua função técnica?”** Documentar os termos do código;
não participa da execução.

</details>

**Função:** licença MIT do código. Não é executada.

**Como explicar:** “Define os termos de uso do código do projeto.”

### `Makefile`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Target/alvo**, aqui, é o nome de uma tarefa como `tarefa`.
- **Comando** é a instrução que a tarefa executa, neste caso o pytest.
- Não é o mesmo “alvo” estatístico da coluna `Churn`.

**Se perguntarem “preciso de make no Windows?”** O comando Python equivalente
pode ser executado diretamente.

</details>

**Função:** oferece `make tarefa` como atalho para `python -m pytest -q`.

**Como explicar:** “É um atalho de desenvolvimento. No PowerShell, também posso
rodar o comando Python diretamente.”

### `README.md`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **README** é o texto de entrada apresentado na página principal do GitHub.
- **Git** é o sistema de controle de versões. **GitHub** hospeda o repositório
  remoto e oferece páginas, colaboração e revisão.
- **Branch** é uma linha de histórico, como §main§. **Commit** registra um
  estado; **tag** dá um nome a um ponto desse histórico.
- **Clone** traz arquivos e histórico. **Download ZIP** traz os arquivos daquela
  versão sem o histórico `.git`.
- **Push** envia commits ao remoto; **deploy** coloca a versão para executar
  no ambiente. Um não implica automaticamente o outro.

**Se perguntarem “o GitHub atualiza o site?”** Só se existir uma automação ou
operação que faça isso. O projeto documenta publicação por scripts.

</details>

**Função:** porta de entrada da documentação. Tem arquitetura, comandos de
instalação, treino, exportação, API, deploy e links para os guias.

**Como explicar:** “É o primeiro arquivo para alguém baixar e executar o
projeto. A base do professor já vem junto.”

O link da demonstração não garante que ela esteja executando o último commit.
Para uma apresentação ao vivo, confira a versão do ambiente utilizado.

### `compose.postgres.yaml`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Overlay** complementa/sobrescreve a configuração base na ordem indicada
  ao Compose.
- **Mount/montagem** disponibiliza arquivo ou armazenamento no contêiner.
- **Secret**, nesse Compose, é um recurso de arquivo fornecido ao serviço;
  não significa que a senha esteja dentro do Git.

**Se perguntarem “a ordem da tela é a execução?”** Não. O GitHub mostra nomes
em ordem; o comando parte da base e aplica os complementos que foram indicados.

</details>

**Função:** complementa a configuração base para consultar o PostgreSQL privado.
Monta os arquivos de conexão/certificado no backend e retira o bind do CSV
do frontend.

**Como explicar:** “Troca a origem da busca de clientes: em vez do arquivo local,
a interface pede os atributos à API e ao banco.”

### `compose.publico.yaml`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Limite de recursos** restringe CPU (processamento) e memória que o serviço
  pode consumir.
- **Modo público** é uma configuração da interface; não é autenticação.
- **Superfície exposta** é o que visitantes conseguem acessar. Restringir
  caminhos/controles não transforma a demo em sistema com login.

**Se perguntarem “por que bloquear recarga?”** É uma operação que muda o modelo
carregado e não deve ficar disponível ao visitante dessa demonstração.

</details>

**Função:** complementa a execução com limites de recursos e ajustes públicos.
Desabilita recarga no backend e restringe os controles do frontend. O Nginx
descrito em `deploy/` fornece a entrada HTTPS.

**Como explicar:** “Adapta os serviços para a demonstração pública, mantendo as
portas da aplicação no host local.”

### `compose.yaml`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Compose** organiza os serviços Docker. **YAML** representa sua configuração
  com grupos e recuos.
- **Serviço** é uma definição como `backend`; dele se cria um contêiner.
- **DNS** associa nomes a endereços; a rede interna permite usar `backend`
  como nome do destino. **Porta** é um ponto numérico de atendimento.
- Em `127.0.0.1:8000:8000`, endereço/porta iniciais são do host e a última
  porta é do contêiner. **Loopback** é o endereço local da própria máquina.
- **Bind mount** liga um caminho específico do host, como o CSV. Um **volume
  nomeado** é armazenamento gerenciado pelo Docker, como o usado no banco.
- `read_only` restringe escrita; **tmpfs** fornece área temporária em memória;
  remover **capabilities** limita privilégios Linux.
- `&aplicacao` declara uma configuração reutilizável e `*aplicacao` a referencia.
  As expressões de variável com padrão usam o padrão quando não há valor.

**Se perguntarem “qualquer pessoa acessa a porta 8000?”** O Compose publica
em loopback; a entrada pública documentada passa pelo Nginx. O estado real da
rede e do host precisa ser conferido no ambiente.

**Para conferir:** [Modelo do Compose](https://docs.docker.com/compose/intro/compose-application-model/) · [Armazenamento persistente](https://docs.docker.com/get-started/docker-concepts/running-containers/persisting-container-data/).

</details>

**Função:** define a execução base dos serviços `backend` e `frontend`,
utilizando a mesma imagem construída pelo `Dockerfile.api`.

Configura rede interna, portas locais, bind do CSV para leitura e healthchecks.
A API roda em 8000, Streamlit em 8501. A interface espera a API pronta.
Os serviços usam usuário da imagem, raiz somente leitura, `/tmp` temporário,
capacidades removidas e reinício automático.

| Arquivos combinados | De onde vêm os clientes |
| --- | --- |
| Base | CSV montado no frontend |
| Base + público | CSV, com interface pública restrita |
| Base + público + PostgreSQL | API consulta o banco privado |

**Como explicar:** “O Dockerfile define a imagem; o Compose organiza como os
serviços dessa aplicação serão executados.”

Mudar `CAMINHO_DADOS` no Python sozinho não muda o bind do CSV definido no
Compose base.

### `pyproject.toml`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Metadados** descrevem o projeto: nome, versão e versão Python.
- **Coleta do pytest** é a descoberta dos arquivos/casos que serão executados.
- **PYTHONPATH/src** ajuda a localizar o pacote `churn` no diretório de código.

**Se perguntarem “TOML treina algo?”** É configuração lida por ferramentas;
quem ajusta a floresta é o comando de experimentos.

</details>

**Função:** declara metadados e Python 3.12, configura o `src` para os testes e
os padrões de coleta do pytest.

**Como explicar:** “Descreve o projeto Python e como encontrar os módulos e
os testes da versão mantida.”

### `requirements.runtime.txt`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Dependência** é uma biblioteca necessária ao programa.
- **Runtime** é o ambiente de execução. **MLflow Skinny** é uma instalação
  menor usada na carga/uso do modelo, em vez do conjunto completo de treino.
- **Versão fixada**, como `scikit-learn==1.7.2`, pede aquela versão declarada.

**Se perguntarem “para prever precisa treinar de novo?”** Não. O pacote
ajustado recebe os atributos; a busca do cliente é outra responsabilidade.

</details>

**Função:** dependências da imagem da aplicação. Inclui FastAPI, Streamlit,
scikit-learn e MLflow Skinny para carregar o pacote.

**Como explicar:** “É o ambiente necessário para servir a versão treinada.”

### `requirements.txt`

<details>
<summary>Entenda os termos e as perguntas</summary>

- **Ambiente virtual** separa as instalações Python de outros projetos.
  Não é um contêiner e não inclui um sistema operacional.
- **pip** instala pacotes Python.
- **Dependência transitiva** é exigida por outra biblioteca. Este arquivo não
  fixa explicitamente todas elas, então não equivale a um lock completo de
  todos os pacotes resolvidos.

**Se perguntarem “por que duas listas?”** Quem treina e testa usa ferramentas
adicionais; a imagem da aplicação usa a lista de execução.

</details>

**Função:** dependências do desenvolvimento e do treinamento, incluindo o
MLflow completo, Pandera e pytest.

**Como explicar:** “É o ambiente de quem vai treinar e testar o projeto.
O arquivo anterior atende à execução da aplicação.”

## Arquivos gerados que você não vê nessa listagem

Não são outras etapas que precisam ser decoradas; são produtos ou insumos de
execução que ficam fora da árvore versionada:

| Caminho | O que é |
| --- | --- |
| `.venv/` | Ambiente Python de desenvolvimento |
| `mlflow.db` | Metadados do Tracking e Registry |
| `mlartifacts/` e `mlruns/` | Artefatos de experimentos conforme o backend |
| `artifacts/modelo/` | Pipeline exportado e seus metadados, necessário para o build |
| `artifacts/pacotes/` | Pacotes produzidos para publicação |
| `.env` da release | Tag da imagem e arquivos Compose usados naquela execução |
| Arquivos externos de conexão/certificado | Montados no backend para acessar o banco |
| `__pycache__/` e `.pytest_cache/` | Caches de Python e pytest |

## Fechamento da explicação

> “A base foi fornecida pronta. O projeto organiza a experimentação, guarda a
> origem dos resultados, fixa uma versão do modelo e permite consultar clientes
> por uma aplicação. Cada pasta da árvore atende a uma dessas responsabilidades.”

A decisão de risco é uma estimativa do modelo, não certeza de cancelamento.
O código contém uma demonstração sem login; não apresenta calibração das
probabilidades, retorno de campanhas, avaliação de equidade, monitoramento de
drift ou reentreino automático. A configuração de rede e publicação está
versionada, mas o estado real da EC2 deve ser verificado no ambiente da demo.

## Palavras do fechamento

- **Monitoramento** é observar a operação e suas medidas ao longo do tempo.
  Ter logs ou healthchecks não equivale a medir qualidade preditiva futura.
- **Drift** é uma mudança nas distribuições dos dados ou nas relações
  relevantes para o modelo ao longo do tempo; pode afetar seu desempenho.
- **Equidade** exige analisar comportamento e erros entre grupos relevantes;
  usar atributos de perfil não demonstra que essa análise tenha sido feita.
- **Reentreino automático** seria disparar novos ajustes por uma regra
  operacional. O grid deste projeto é executado por comando; não é esse
  agendamento automático.

## Confira se consegue explicar

Tente responder antes de abrir cada resposta.

<details>
<summary>Uma probabilidade de 0,60 significa 60% de acerto?</summary>

É o score daquela entrada. Acurácia exige várias entradas com respostas
conhecidas e compara as decisões com os rótulos.
</details>

<details>
<summary>Trocar o limiar de 0,50 para 0,70 cria outro modelo?</summary>

Não. Muda a regra de decisão sobre os scores do mesmo modelo. Um score de 0,60
passa de Yes para No. Em um mesmo conjunto, elevar o corte tende a sinalizar
menos casos; isso afeta a contagem de alertas e cancelamentos encontrados.
</details>

<details>
<summary>Por que não usamos os clientes do teste para ajustar os imputadores?</summary>

Porque isso introduziria informação do conjunto reservado no ajuste. O teste
deve medir o modelo que foi escolhido sem aprender com aquelas entradas.
</details>

<details>
<summary>Onde a previsão roda no modo público: navegador, Streamlit ou FastAPI?</summary>

Na FastAPI. O navegador apresenta a interface; o processo Streamlit envia a
requisição e mostra o retorno.
</details>

<details>
<summary>Qual diferença há entre PostgreSQL e SQLite neste projeto?</summary>

PostgreSQL fornece atributos de clientes à aplicação. SQLite é o backend local
dos metadados de experimentos/Registry no treinamento.
</details>

<details>
<summary>Se champion mudou, por que o site pode continuar usando outra versão?</summary>

A instalação com pacote exportado carrega uma versão fixa incluída na imagem.
É necessário exportar e publicar a versão pretendida.
</details>

<details>
<summary>Qual é a diferença entre receita, pacote e execução no Docker?</summary>

Dockerfile é a receita; imagem é o pacote construído; contêiner é a execução.
Dois contêineres podem usar a mesma imagem com comandos diferentes.
</details>

<details>
<summary>Se o GitHub tem o código, por que não sabemos se o site está atualizado?</summary>

Push atualiza o repositório remoto. Deploy e a observação do serviço confirmam
qual release/modelo está realmente executando.
</details>
