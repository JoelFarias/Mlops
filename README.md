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
