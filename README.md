# Projeto de churn — MLOps

Projeto modular para treinamento do modelo de previsão de churn usado nos
encontros iniciais da disciplina de MLOps.

O comportamento do script inicial foi preservado. A única correção funcional é
a substituição do caminho absoluto do CSV por caminhos construídos com
`pathlib.Path` e centralizados em uma configuração Pydantic.

## Estrutura

```text
src/churn/
├── api/
│   ├── aplicacao.py
│   ├── esquemas.py
│   ├── servico.py
│   └── static/
├── frontend/
│   ├── app.py
│   ├── dados.py
│   └── inferencia.py
├── avaliacao.py
├── caracteristicas.py
├── configuracao.py
├── dados.py
├── modelo.py
└── treinar.py
```

O arquivo `train_churn.py` permanece no repositório como versão inicial para
comparação. O dataset fica em `data/raw/churn.csv` e não é versionado pelo Git.

## Ambiente local

No PowerShell, com o ambiente virtual ativo:

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m churn.treinar
```

O treinamento grava `modelo_final_v3_ok.pkl` na raiz do projeto.

## Treino/tuning, registro e seleção para deploy

O fluxo MLflow usa o CSV real, valida o contrato Pandera e divide os dados
em treino (60%), validação (20%) e teste (20%), com estratificação e seed 42.
O comando legado `churn.treinar` continua disponível; o fluxo abaixo inclui
o pré-processamento no modelo para permitir inferência com as colunas do CSV.

```powershell
$env:PYTHONPATH = "src"
python -m churn.experimentos
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Execute na raiz do projeto. Abra http://localhost:5000 e o experimento
`churn-tuning`. Cada busca contém nove runs: Random Forest com 100, 200 ou 500
árvores e profundidade livre, 8 ou 16. O encoder e os imputadores são ajustados
somente no treino. Cada run armazena parâmetros, métricas de validação, hash
SHA-256 do CSV, commit Git e o pipeline completo com assinatura e exemplo.

A maior `validation_roc_auc` escolhe o vencedor **dessa busca**; em empate,
vence a primeira configuração na ordem do grid. Apenas o vencedor é avaliado
no teste. Se `test_roc_auc >= 0.80`, uma versão é registrada como `churn` e
recebe o alias `champion`. Caso contrário, nenhuma versão é registrada e o
alias anterior é preservado. O relatório `selecao.json` fica no run da busca.
Esse gate é um mínimo de qualidade; não compara com um champion anterior.
Os resultados de buscas diferentes não são misturados com runs sintéticos.

Opções: `--dados caminho.csv`, `--limiar 0.80`, `--experimento churn-tuning`,
`--nome-modelo churn` e `--tracking-uri sqlite:///mlflow.db`.
Também é possível configurar `MLFLOW_TRACKING_URI`; sem configuração, o banco
é `mlflow.db` na raiz deste projeto. Tracking e Registry usam o mesmo backend.

Para consumir o modelo selecionado, use o mesmo tracking URI do treinamento:

```python
import mlflow
import pandas as pd

mlflow.set_tracking_uri("sqlite:///mlflow.db")
modelo = mlflow.pyfunc.load_model("models:/churn@champion")
entrada = pd.read_csv("data/raw/churn.csv", na_values=[" "])
entrada = entrada.drop(columns=["customerID", "Churn"])
previsoes = modelo.predict(entrada.head())  # 0 = No, 1 = Yes
```

O pacote inclui limpeza de `TotalCharges`, criação de `gasto_por_mes`,
imputação e codificação de categorias (inclusive categorias novas).
O alias identifica a versão escolhida para deploy; o comando não publica uma
API. Para adotar uma nova versão sem reiniciar o processo, use
`POST /modelo/recarregar` (ou os botões de recarga do frontend).
Para fixar uma versão, use `models:/churn/1` (substitua `1`).
Referências: [MLflow Models](https://www.mlflow.org/docs/latest/model/) e
[Model Registry](https://mlflow.org/docs/latest/ml/model-registry/tutorial).

## API de inferência (FastAPI)

A API carrega uma única vez, no startup, o modelo `churn@champion` do MLflow
e expõe o contrato de entrada do CSV (sem `customerID` e sem `Churn`).

| Rota | Método | Uso |
| --- | --- | --- |
| `/` | GET | formulário web para preencher e ver o resultado |
| `/saude` | GET | processo no ar e modelo carregado |
| `/pronto` | GET | retorna 200 somente com modelo carregado; caso contrário, 503 |
| `/modelo` | GET | versão e alias em uso |
| `/modelo/recarregar` | POST | recarrega o champion sem reiniciar |
| `/prever` | POST | prediz um cliente |
| `/docs` | GET | Swagger UI |

Pré-requisito: ter rodado `python -m churn.experimentos`, para existir
`mlflow.db` com o alias `champion`.

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn churn.api.aplicacao:app --reload
```

Abra http://127.0.0.1:8000/ para o formulário, ou
http://127.0.0.1:8000/docs para o Swagger. No formulário, preencha os dados
e clique em **Calcular risco**: a página chama `POST /prever` e exibe a
classe, a probabilidade e a resposta JSON.

Ou via HTTP:

```powershell
$corpo = @{
    gender = "Female"; SeniorCitizen = 0; Partner = "Yes"; Dependents = "No"
    tenure = 12; PhoneService = "Yes"; MultipleLines = "No"
    InternetService = "Fiber optic"; OnlineSecurity = "No"
    OnlineBackup = "Yes"; DeviceProtection = "No"; TechSupport = "No"
    StreamingTV = "Yes"; StreamingMovies = "No"
    Contract = "Month-to-month"; PaperlessBilling = "Yes"
    PaymentMethod = "Electronic check"; MonthlyCharges = 70.5
    TotalCharges = 845.5
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/prever `
    -ContentType "application/json" -Body $corpo
```

A resposta traz `churn` (`Yes`/`No`), `probabilidade` e o `limiar` usado.
`422` significa contrato violado; `503`, modelo não carregado.

Os testes da API não dependem do MLflow:

```powershell
python -m pytest tests/teste_api.py -q
```

## Frontend Streamlit (inferência online)

Abra outro terminal:

```powershell
$env:PYTHONPATH = "src"
python -m streamlit run src/churn/frontend/app.py
```

Abra http://localhost:8501. O frontend tem dois modos, escolhidos na barra
lateral:

- **Modelo local (Streamlit)** — padrão. O próprio frontend carrega o alias
  `churn@champion` do MLflow, executa `predict_proba` e aplica o limiar. O
  modelo é carregado uma vez no processo do Streamlit e fica em cache; o botão
  **Recarregar modelo local** limpa o cache e carrega novamente.
- **API FastAPI** — o frontend consulta `GET /saude` e `GET /modelo`, envia os
  19 campos para `POST /prever` e recebe a predição pronta. O botão
  **Recarregar modelo na API** chama `POST /modelo/recarregar`.

Nos dois modos, o cliente é buscado pelo `customerID` em `data/raw/churn.csv`,
uma tabela com informações básicas é exibida e o resultado mostra classe,
probabilidade e limiar. A URL da API pode ser alterada na barra lateral; o
padrão é `http://127.0.0.1:8000` (ou a variável `CHURN_API_URL`). No modo local
a API pode até estar desligada; é o Streamlit que executa a inferência.

Exemplos de códigos para testar: `1069-XAIEM` (risco alto), `7590-VHVEG`
(perto do limiar) e `0902-XKXPN` (risco baixo).

### Docker

O frontend Streamlit e o backend FastAPI usam **a mesma imagem**, construída
com `Dockerfile.api`, em dois containers. O frontend inicia no modo API e
chama `http://backend:8000` pela rede interna do Compose.

Exporte o champion treinado no Windows antes do build. Isso inclui os artefatos
na imagem e elimina a dependência dos caminhos absolutos do `mlflow.db`:

```powershell
$env:PYTHONPATH = "src"
python -m churn.exportar
docker compose build backend
docker compose up -d --no-build --pull never --wait --wait-timeout 180
```

Abra http://127.0.0.1:8501 para o Streamlit ou http://127.0.0.1:8000/docs para
a API. O CSV `data/raw/churn.csv` é montado somente para leitura no frontend;
o modelo exportado fica em `artifacts/modelo`, dentro da imagem. O backend só
é publicado no endereço local da máquina. O healthcheck exige modelo carregado
antes de iniciar o frontend.

Valide a inferência e acompanhe os serviços:

```powershell
docker compose exec -T backend python scripts/verificar-deploy.py
docker compose ps
docker compose logs --tail 50
```

O exportador fixa a versão selecionada pelo alias e não sobrescreve uma pasta
existente. Para outra versão, use `python -m churn.exportar --destino <pasta>`
e substitua a pasta de build `artifacts/modelo` após revisar o novo pacote.
Com `MODELO_URI` definido, a recarga relê o pacote exportado; para atualizar o
champion no deploy é necessário exportar novamente e reconstruir a imagem.

Configurações via ambiente: `MODELO_URI`, `MLFLOW_TRACKING_URI`, `NOME_MODELO`,
`ALIAS_MODELO`, `LIMIAR_CHURN`, `CHURN_API_URL`, `CHURN_MODO_INFERENCIA`,
`CHURN_IMAGEM`, `CHURN_PORTA_API`, `CHURN_PORTA_FRONTEND`, `CHURN_MODO_PUBLICO`,
`CHURN_ENDERECO_PUBLICO` e `RECARGA_MODELO_HABILITADA`.
Se as portas locais estiverem ocupadas, configure `CHURN_PORTA_API=18000`
e `CHURN_PORTA_FRONTEND=18501` antes de subir os serviços.
Sem `MODELO_URI`, o carregamento local mantém
o comportamento de consultar o registry.

O passo a passo de publicação está em [Deploy na EC2](docs/deploy-ec2.md).

Para demonstração pública, o deploy usa `compose.publico.yaml` e Nginx com
HTTPS no IP. O frontend permite consultas sem login; edição da URL da API,
escolha de inferência local e recarga administrativa ficam desabilitadas.
As portas 8000 e 8501 continuam restritas ao localhost. O proxy limita
requisições e conexões, e um timer renova o certificado automaticamente.
Use dados de exemplo nesse modo, pois qualquer visitante pode consultá-los.

## Testes

```powershell
python -m pytest -q
```

### Caso de dado quebrado

O teste `teste_schema_coleta_todas_as_falhas_com_lazy_true` cria uma amostra
temporária com quatro violações do contrato:

- `tenure = 999`, acima do limite de 72;
- `MonthlyCharges = 200`, acima do limite de 120;
- `Contract = "Vitalicio"`, categoria não permitida;
- `Churn = "Talvez"`, categoria não permitida.

A chamada `ChurnSchema.validate(..., lazy=True)` interrompe o pipeline antes do
treinamento e reúne as quatro violações em `SchemaErrors.failure_cases`. O CSV
original não é modificado.

Para executar somente esse caso:

```powershell
python -m pytest tests/teste_dados.py::teste_schema_coleta_todas_as_falhas_com_lazy_true -v
```

## Leitura — Data Pipeline

A seção [Data: Data Engineering Pipelines](https://ml-ops.org/content/three-levels-of-ml-software#data-data-engineering-pipelines)
organiza o pipeline em ingestão, exploração e validação, limpeza e divisão dos
dados. O profiling produz metadados como tipos, faixas e quantidade de valores
ausentes; a validação aplica regras para detectar erros; e a limpeza transforma
os dados por meio de funções reproduzíveis. O projeto implementa esse fluxo em
`carregar_dados`, `limpar_dados` e `ChurnSchema`.

## Docker

Construa a imagem:

```powershell
docker build -t churn-treino .
```

Execute o treinamento usando o dataset local como volume somente leitura:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path)\data,target=/aplicacao/data,readonly" churn-treino
```

O comando executa o mesmo módulo `churn.treinar` dentro do contêiner.

## Imagem Docker do PostgreSQL

A imagem `churn-postgres:1.0` inclui o CSV de exemplo e importa seus registros
para `public.clientes` no banco `churn` na primeira inicialização com um volume
vazio. O campo `"customerID"` é a chave primária.

Com `data/raw/churn.csv` na raiz do projeto, construa e exporte a imagem para
Linux x86-64.

```powershell
docker build --platform linux/amd64 -f Dockerfile.postgres -t churn-postgres:1.0 .
New-Item -ItemType Directory -Path artifacts -Force | Out-Null
docker save -o artifacts/postgres-churn.tar churn-postgres:1.0
```

Para usar o arquivo em outro Docker, carregue a imagem e inicie o contêiner.
A senha é definida em tempo de execução e o volume preserva o banco entre
execuções.

```powershell
docker load -i artifacts/postgres-churn.tar
$env:POSTGRES_PASSWORD = [guid]::NewGuid().ToString('N')
docker run -d --name churn-postgres --env POSTGRES_PASSWORD `
  --mount type=volume,source=churn-postgres-dados,target=/var/lib/postgresql/data `
  churn-postgres:1.0
Remove-Item Env:POSTGRES_PASSWORD
```

Depois que o PostgreSQL estiver pronto, consulte a tabela pelo próprio contêiner.

```powershell
docker exec churn-postgres psql -U postgres -d churn -c 'SELECT count(*) FROM public.clientes;'
```

[Conectar a aplicação ao PostgreSQL em uma segunda EC2](docs/deploy-ec2.md#postgresql-em-uma-segunda-ec2)
