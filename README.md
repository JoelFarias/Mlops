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
