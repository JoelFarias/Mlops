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

## 1. `.streamlit/`

Configuração da interface feita com Streamlit. O ponto inicial no nome da pasta
não significa código secreto: é apenas uma convenção de configuração.

### `.streamlit/config.toml`

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

**Função:** configuração inicial do Nginx, antes do certificado público.
Atende em HTTP o desafio usado para emitir o certificado.

**Quem usa:** `scripts/configurar-https.sh` na etapa `preparar`.

**Como explicar:** “É a configuração inicial para provar o controle do endereço
e permitir a emissão do certificado.”

### `deploy/nginx/publico.conf`

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

**Função:** cria `public.clientes`, importa as 21 colunas do CSV e usa
`customerID` como chave primária. Ajusta o tipo de `TotalCharges` para número,
convertendo espaços em `NULL`.

**Quem usa:** a imagem do PostgreSQL na inicialização de um volume novo.

**Atenção:** trocar a imagem ou reiniciar o contêiner com um volume já existente
não executa novamente a importação.

**Como explicar:** “O banco recebe os clientes dessa base. Ele fornece os dados
da consulta; o modelo treinado fica em outro pacote.”

### `deploy/systemd/churn-https.service`

**Função:** define uma tarefa `oneshot` do systemd para executar o script de
renovação do HTTPS.

**Quem usa:** o systemd no host, por acionamento do timer.

**Como explicar:** “Descreve o que o servidor deve executar quando for verificar
a renovação do certificado.”

### `deploy/systemd/churn-https.timer`

**Função:** agenda a verificação após a inicialização e a cada 12 horas, com
atraso aleatório de até cinco minutos.

**Quem usa:** systemd, para acionar o `service` anterior.

**Como explicar:** “O service diz o que executar; o timer diz quando executar.”

## 4. `docs/`

Documentação de instalação, funcionamento e operação. A pasta
`material-disciplina/` reúne os slides e os guias da aula; para apresentar o
fluxo ativo, siga os dois arquivos abaixo.

### `docs/deploy-ec2.md`

**Função:** manual para preparar e operar a publicação documentada, com uma EC2
para a aplicação e outra para o PostgreSQL privado.

Descreve pré-requisitos, envio do pacote, ativação do HTTPS, conexão ao banco
e verificações operacionais. É um manual: suas instruções só mudam o servidor
quando alguém executa os comandos.

**Como explicar:** “Este é o roteiro de publicação. Os arquivos descrevem a
instalação; a versão realmente executada precisa ser conferida no servidor.”

### `docs/guia-tecnico.md`

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

**Função:** instala/prepara o Nginx e, na etapa de ativação, solicita o
certificado via Certbot. Também instala a renovação pelo systemd.

**Quem usa:** o administrador durante a preparação do host público.

**Como explicar:** “Automatiza a configuração da entrada HTTPS usando os arquivos
do Nginx e as tarefas de renovação.”

### `scripts/deploy-ec2.ps1`

**Função:** no Windows, seleciona os arquivos necessários, gera um pacote
`tar.gz` com hash, envia por SSH/SCP e chama o inicializador da aplicação.
Cada envio recebe uma pasta de release própria.

`-SomentePacote` cria o pacote local e para antes do envio. `-Publico` inclui
a configuração pública; `-Publico -Postgres` prepara o perfil que consulta o
banco privado.

**Como explicar:** “É o procedimento de entrega do meu computador para a EC2.
O pacote reúne código, configuração e uma versão já exportada do modelo.”

### `scripts/iniciar-ec2.sh`

**Função:** no Ubuntu, verifica insumos, prepara Docker se necessário, configura
o Compose da release, constrói a imagem e sobe os serviços.

Espera os healthchecks, confere que backend e frontend usam a mesma imagem e
chama o script de verificação. Com PostgreSQL, verifica a consulta de um cliente
antes de atualizar os serviços.

**Como explicar:** “Faz a aplicação subir no host e verifica se os componentes
necessários respondem.”

### `scripts/iniciar-postgres-ec2.sh`

**Função:** prepara o host privado do PostgreSQL: Docker, imagem, volume, TLS,
regra de acesso e usuário de leitura.

**Quem usa:** o administrador da instalação do banco. A API utiliza a conexão
configurada; esse instalador não é executado a cada consulta.

**Como explicar:** “Prepara o banco privado para fornecer os dados dos clientes
à aplicação.”

### `scripts/proteger-host.sh`

**Função:** configura SSH por chave e firewall, usando o IP da conexão do
administrador. Inclui a medida de retorno prevista para evitar perda de acesso.

**Como explicar:** “É uma rotina administrativa de proteção do host. Não faz
parte do cálculo do risco do cliente.”

### `scripts/renovar-https.sh`

**Função:** executa a verificação de renovação do certificado e valida/recarrega
o Nginx.

**Quem usa:** o service do systemd, acionado periodicamente pelo timer.

**Como explicar:** “Mantém a validade da entrada HTTPS ao longo do tempo.”

### `scripts/verificar-deploy.py`

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

Dentro de `api/`, a pasta `static/` aparece antes dos arquivos Python.

**Função:** formulário HTML alternativo, servido em `GET /` da API local.
Permite digitar os 19 atributos manualmente; o JavaScript envia `POST /prever`
e apresenta a resposta.

**Como explicar:** “Este é um cliente simples da API para preencher atributos
manualmente. A interface de consulta por código é feita com Streamlit.”

### `src/churn/api/__init__.py`

**Função:** identifica o pacote da API e reexporta a instância `app`.

**Como explicar:** “É a entrada do pacote Python da API; as rotas estão no
arquivo seguinte.”

### `src/churn/api/aplicacao.py`

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

**Função:** busca o registro no PostgreSQL com SQL parametrizado. Normaliza o
código, aplica timeouts e devolve somente os campos definidos no contrato
de consulta.

O `customerID` identifica o registro; o rótulo real `Churn` não é devolvido como
atributo de previsão.

**Como explicar:** “É a ligação entre a API e o banco privado. O código recebido
serve para localizar os atributos do cliente.”

### `src/churn/api/esquemas.py`

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

Agora abra a pasta `frontend/`.

**Função:** identifica o pacote Python da interface.

**Como explicar:** “Organiza os módulos que cuidam da tela e de sua comunicação
com o modelo ou com a API.”

### `src/churn/frontend/app.py`

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

**Função:** carrega os clientes no modo CSV, busca o código sem diferenciar
maiúsculas e monta o payload de 19 campos. Remove identificador e alvo, converte
tipos numéricos e traduz valores apenas para apresentação na tabela.

**Como explicar:** “Pega o registro escolhido e o transforma na entrada da API.
O dado conhecido de cancelamento não é enviado ao modelo.”

### `src/churn/frontend/inferencia.py`

**Função:** permite que o próprio Streamlit carregue e consulte o modelo no
modo local. Reaproveita `ServicoChurn` e devolve o mesmo formato de resposta da
API.

**Como explicar:** “Oferece uma alternativa de execução local. No Compose e no
perfil público, a inferência é feita pela FastAPI.”

### `src/churn/__init__.py`

Volte a `src/churn/` para os arquivos que vêm depois das duas subpastas.

**Função:** identifica o pacote principal. Está vazio.

**Como explicar:** “Marca a organização do código como pacote Python.”

### `src/churn/configuracao.py`

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

**Função:** `git_commit` consulta o hash do commit do código pelo Git local.

**Quem usa:** `experimentos.py`, para registrar a origem do código junto ao run.

**Como explicar:** “Esse helper liga o experimento a uma versão do código.
O hash do CSV identifica os dados e o commit identifica a implementação.”

O clone traz o histórico `.git`; o Download ZIP traz código e dados, mas não
traz esse histórico. A consulta do commit depende do Git disponível no ambiente.

### `src/churn/pipeline.py`

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

Verifica saúde, prontidão, formulário, contrato de entrada, resposta de previsão,
metadados e recarga. Há modelos pequenos e dependências substituídas para
controlar os cenários.

**Como explicar:** “Confere se a API aceita os dados certos e responde
corretamente, inclusive quando o modelo está indisponível.”

### `tests/teste_configuracao.py`

Confere o caminho padrão da base da disciplina.

**Como explicar:** “Evita que o padrão do projeto passe a apontar para um
arquivo ou diretório errado.”

### `tests/teste_dados.py`

Verifica leitura do CSV, conversão dos campos prevista no código e violações do
contrato Pandera. O caso inválido reúne erros de várias colunas com `lazy=True`.

**Como explicar:** “Confere que a entrada é lida e que um arquivo incompatível
seja detectado antes do treino.”

### `tests/teste_experimentos.py`

Verifica seleção, separação entre validação e teste, mínimo de promoção,
Registry, carga e exportação do modelo. Usa SQLite temporário e modelos pequenos;
as métricas são controladas nos cenários de decisão.

**Como explicar:** “Testa se a lógica escolhe e registra o modelo corretamente.
As métricas finais da disciplina vêm do treino com o CSV, não desses cenários.”

### `tests/teste_frontend.py`

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

**Função:** seleciona o que fica fora do contexto enviado ao Docker no build.
Exclui ambientes, caches, histórico, dados e arquivos de apoio; reinclui
`artifacts/modelo` para a imagem da aplicação.

**Como explicar:** “O build recebe só o contexto necessário. O modelo exportado
entra na imagem; os dados da consulta local são montados separadamente.”

### `.gitattributes`

**Função:** padroniza fins de linha de scripts e receitas para funcionar entre
Windows e Linux. Para o CSV, desliga conversão de texto para preservar os
bytes e o hash original.

**Como explicar:** “Protege a compatibilidade dos scripts e a identidade da base.”

### `.gitignore`

**Função:** define o que fica fora do versionamento: ambientes, saídas, modelos,
banco de experimentos e arquivos de configuração local. Abre exceção apenas
para o CSV original em `data/raw/churn.csv` entre os dados do projeto.

**Diferença importante:** ignorar no Git não exclui automaticamente do Docker.
Por isso o modelo pode ficar fora do Git e ser incluído na imagem, enquanto
o CSV fica no Git e é excluído do contexto da imagem da aplicação.

### `Dockerfile.api`

**Função:** receita da imagem compartilhada de FastAPI e Streamlit. Usa Python
3.12, instala `requirements.runtime.txt`, copia código e modelo exportado e
cria um usuário sem root.

**Quem usa:** `compose.yaml`, por `dockerfile: Dockerfile.api`.

**Como explicar:** “Define o ambiente e os arquivos da aplicação. A mesma imagem
inicia dois contêineres, um para a API e outro para o Streamlit.”

Imagem é o pacote; contêiner é a execução. O pacote `artifacts/modelo` precisa
existir antes do build.

### `Dockerfile.postgres`

**Função:** receita separada da imagem PostgreSQL. Inclui o CSV da disciplina e
`deploy/postgres/iniciar.sql` para inicializar o banco de clientes.

**Como explicar:** “Esta é a imagem do banco; não é a imagem da aplicação.
A carga inicial cria os clientes a partir do CSV.”

### `Dockerfile.postgres.dockerignore`

**Função:** lista de inclusão do contexto específico da imagem PostgreSQL:
CSV e SQL. Ela atende a um build que precisa dos dados.

**Como explicar:** “As duas imagens precisam de arquivos diferentes.
A aplicação leva o modelo; a imagem do banco leva a base para sua carga inicial.”

### `LICENSE`

**Função:** licença MIT do código. Não é executada.

**Como explicar:** “Define os termos de uso do código do projeto.”

### `Makefile`

**Função:** oferece `make tarefa` como atalho para `python -m pytest -q`.

**Como explicar:** “É um atalho de desenvolvimento. No PowerShell, também posso
rodar o comando Python diretamente.”

### `README.md`

**Função:** porta de entrada da documentação. Tem arquitetura, comandos de
instalação, treino, exportação, API, deploy e links para os guias.

**Como explicar:** “É o primeiro arquivo para alguém baixar e executar o
projeto. A base do professor já vem junto.”

O link da demonstração não garante que ela esteja executando o último commit.
Para uma apresentação ao vivo, confira a versão do ambiente utilizado.

### `compose.postgres.yaml`

**Função:** complementa a configuração base para consultar o PostgreSQL privado.
Monta os arquivos de conexão/certificado no backend e retira o bind do CSV
do frontend.

**Como explicar:** “Troca a origem da busca de clientes: em vez do arquivo local,
a interface pede os atributos à API e ao banco.”

### `compose.publico.yaml`

**Função:** complementa a execução com limites de recursos e ajustes públicos.
Desabilita recarga no backend e restringe os controles do frontend. O Nginx
descrito em `deploy/` fornece a entrada HTTPS.

**Como explicar:** “Adapta os serviços para a demonstração pública, mantendo as
portas da aplicação no host local.”

### `compose.yaml`

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

**Função:** declara metadados e Python 3.12, configura o `src` para os testes e
os padrões de coleta do pytest.

**Como explicar:** “Descreve o projeto Python e como encontrar os módulos e
os testes da versão mantida.”

### `requirements.runtime.txt`

**Função:** dependências da imagem da aplicação. Inclui FastAPI, Streamlit,
scikit-learn e MLflow Skinny para carregar o pacote.

**Como explicar:** “É o ambiente necessário para servir a versão treinada.”

### `requirements.txt`

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
