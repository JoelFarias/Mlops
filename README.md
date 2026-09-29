# Projeto de churn — MLOps

Projeto modular para treinamento do modelo de previsão de churn usado nos
encontros iniciais da disciplina de MLOps.

O comportamento do script inicial foi preservado. A única correção funcional é
a substituição do caminho absoluto do CSV por caminhos construídos com
`pathlib.Path` e centralizados em uma configuração Pydantic.

## Estrutura

```text
src/churn/
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
API. Um serviço já em execução precisa recarregar o modelo para adotar uma
nova versão. Para fixar uma versão, use `models:/churn/1` (substitua `1`).
Referências: [MLflow Models](https://www.mlflow.org/docs/latest/model/) e
[Model Registry](https://mlflow.org/docs/latest/ml/model-registry/tutorial).

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
