# MLflow — Guia Completo + Implementação no projeto churn

> **Curso de MLOps — IESB · Bloco 2: ML Pipeline (Encontro 6)**
>
> Material de referência sobre MLflow, encerrando com um guia prático de
> implementação no projeto-fio-condutor (`prj_churn`).


---

## 1. O problema que o MLflow resolve

Treinar um modelo é fácil. O difícil é o que vem em volta: você roda 40 variações,
anota a acurácia num post-it, muda um hiperparâmetro, roda de novo — e três dias
depois ninguém sabe qual configuração deu o melhor resultado, nem com qual versão
do dado. O `print(accuracy)` mostra o número e o esquece.

**MLflow é uma plataforma open-source de gestão do ciclo de vida de ML.** A peça
que resolve a dor acima chama-se **Tracking**: ela dá *memória* aos seus
experimentos — cada execução vira um registro permanente, comparável e
reproduzível, com os parâmetros de entrada, as métricas de saída e os artefatos
gerados.

No diagrama do ml-ops.org, o MLflow Tracking mapeia quase 1:1 com a caixa
*Experiments / Trials* dentro do ML Pipeline. Ele **não treina o modelo por
você** — ele registra e compara o que você já treina.

---

## 2. Os componentes do MLflow

MLflow tem quatro peças. Saber distingui-las é metade da batalha.

| Componente | O que faz | No curso |
| --- | --- | --- |
| **Tracking** | registra params, métricas, artefatos e tags de cada run | **Encontro 6 (foco)** |
| **Models** | formato padrão para empacotar o modelo (flavors) | Encontro 8 |
| **Model Registry** | versiona e promove modelos (staging → produção) | Encontro 7 |
| **Projects** | empacota o código do experimento de forma reprodutível | citado |

Este guia foca em **Tracking** e cobre o essencial de **Models** (porque logar o
modelo é parte do tracking). O Registry aparece em visão geral na seção 10.

---

## 3. Instalação

```bash
uv add mlflow          # no projeto do curso (uv)
# ou: pip install mlflow
mlflow --version       # confirme a versão instalada
```

MLflow instala também a CLI (`mlflow ui`, `mlflow server`) e a biblioteca Python.

---

## 4. O modelo mental do Tracking

A hierarquia tem três níveis:

```
Experiment  ("churn")
└── Run  (uma execução de treino)
    ├── params     entradas que você escolheu   (n_estimators, test_size)
    ├── metrics    números que você mediu        (accuracy, roc_auc)
    ├── artifacts  arquivos gerados              (o modelo, gráficos, o encoder)
    └── tags       metadados                     (git_commit, data_md5, autor)
```

**A regra que evita 90% da confusão:**

- Se **você escolheu** o valor → é um **param**.
- Se **você mediu** o valor → é uma **metric**.
- Se é um **arquivo** → é um **artifact**.
- Se é **metadado** sobre o run → é uma **tag**.

Params e tags são fixos no run; métricas podem ter uma série ao longo do tempo
(útil para curvas de treino, via o argumento `step`).

---

## 5. API básica

O padrão mais comum usa `start_run` como *context manager* — o `with` garante
que o run fecha corretamente, mesmo se ocorrer um erro.

```python
import mlflow

mlflow.set_experiment("churn")            # agrupa os runs sob um nome

with mlflow.start_run(run_name="rf-baseline"):
    # 1) params — as entradas
    mlflow.log_params({"n_estimators": 200, "test_size": 0.25})

    # 2) treina (seu código de sempre)
    model = RandomForestClassifier(n_estimators=200).fit(X_train, y_train)

    # 3) metrics — as saídas
    mlflow.log_metrics({"accuracy": 0.757, "roc_auc": 0.805})

    # 4) tags — metadados / linhagem
    mlflow.set_tag("git_commit", "abc123")

    # 5) o modelo como artefato (ver nota de versão na seção 7)
    mlflow.sklearn.log_model(model, artifact_path="model")
```

Funções equivalentes no singular existem (`log_param`, `log_metric`,
`set_tag`). Para métricas ao longo de épocas:

```python
for epoch, loss in enumerate(losses):
    mlflow.log_metric("loss", loss, step=epoch)
```

**Runs aninhados** (útil para varreduras/hyperparameter search) usam
`nested=True`:

```python
with mlflow.start_run(run_name="busca"):          # run-pai
    for n in [100, 200, 500]:
        with mlflow.start_run(run_name=f"rf-{n}", nested=True):
            ...
```

---

## 6. Autologging

Uma linha instrumenta bibliotecas populares (scikit-learn, XGBoost, PyTorch,
etc.), capturando params, métricas e o modelo automaticamente:

```python
import mlflow
mlflow.sklearn.autolog()      # ou mlflow.autolog() para todas as libs suportadas

model.fit(X_train, y_train)   # params, métricas e modelo capturados sozinhos
```

**Trade-off (importante):** autolog é ótimo para começar rápido, mas registra o
que a *biblioteca* decide relevante. Ele **não conhece** o que é específico do seu
problema — a sua métrica de negócio, a **versão do dado (DVC)**, o commit do Git.

> **Recomendação prática:** use `autolog()` **mais** algumas chamadas manuais de
> `log_metric`/`set_tag` para o que ele não captura. É o melhor dos dois mundos.

---

## 7. Logar e carregar modelos (MLflow Models)

`log_model` salva o modelo num formato padronizado (*flavor*), que pode ser
recarregado depois sem você lembrar como serializou.

```python
from mlflow.models import infer_signature

signature = infer_signature(X_train, model.predict(X_train))

mlflow.sklearn.log_model(
    model,
    artifact_path="model",       # ⚠️ ver nota de versão abaixo
    signature=signature,         # documenta o schema de entrada/saída
    input_example=X_train.head(3),
)
```

Recarregar em qualquer lugar:

```python
model = mlflow.sklearn.load_model("runs:/<run_id>/model")
# ou como função genérica (pyfunc), independente da lib:
model = mlflow.pyfunc.load_model("runs:/<run_id>/model")
```

> ### ⚠️ Ponto sensível à versão — leia antes de rodar
> No **MLflow 2.x**, o segundo argumento é `artifact_path="model"`.
> No **MLflow 3.x**, ele foi renomeado para `name="model"` (o antigo ainda
> funciona, mas emite *deprecation warning*). Confirme com `mlflow --version` e
> use a forma correspondente. Nos exemplos deste guia mantive `artifact_path`
> por compatibilidade ampla.

A `signature` (schema de entrada/saída) e o `input_example` não são
obrigatórios, mas são fortemente recomendados: eles documentam o contrato do
modelo e habilitam validação no serving (Encontro 12).

---

## 8. A interface (mlflow ui)

```bash
mlflow ui                 # sobe em http://localhost:5000
# rode na raiz do projeto, onde está a pasta ./mlruns
```

Na UI você:

- vê a **tabela de runs** de um experiment, com params e métricas em colunas;
- **ordena** por uma métrica → o melhor run sobe ao topo;
- **compara** runs lado a lado;
- usa **coordenadas paralelas** para ver o efeito de cada hiperparâmetro;
- navega nos **artifacts** (o modelo, gráficos, o encoder).

---

## 9. Consultar experimentos por código

Tudo que a UI mostra está disponível programaticamente. `search_runs` devolve
um **DataFrame do pandas** — familiar para quem já usa pandas.

```python
import mlflow

runs = mlflow.search_runs(
    experiment_names=["churn"],
    order_by=["metrics.roc_auc DESC"],
    filter_string="metrics.roc_auc > 0.8",     # opcional
)
best = runs.iloc[0]
print(best["params.n_estimators"], best["metrics.roc_auc"])
```

Para operações mais finas (criar experiments, gerenciar o Registry), use o
cliente de baixo nível:

```python
from mlflow.tracking import MlflowClient
client = MlflowClient()
run = client.get_run(run_id)
```

---

## 10. Model Registry (visão geral — Encontro 7)

Depois de achar o melhor run, o **Registry** promove aquele modelo de
"experimento" a "artefato gerenciado", com versões e estágios/aliases.

```python
# registra a versão a partir de um run
mlflow.register_model("runs:/<run_id>/model", name="churn")

# em MLflow recente, prefira ALIASES a stages (staging/production foram depreciados)
client.set_registered_model_alias(name="churn", alias="champion", version=3)
```

Isso é o tema do Encontro 7 — aqui basta saber que o caminho natural depois do
tracking é registrar e promover o vencedor.

---

## 11. Onde o MLflow guarda tudo (backends)

MLflow separa **metadados** (params, métricas, tags) de **artefatos** (arquivos).

| Cenário | Backend de metadados | Artifact store |
|---|---|---|
| **Local (padrão)** | pasta `./mlruns` (file store) | `./mlruns` |
| **Time / produção** | banco (SQLite, Postgres) via `mlflow server` | S3 / GCS / Azure |

Fixar o destino evita runs espalhados:

```python
mlflow.set_tracking_uri("file:./mlruns")          # local, explícito
# ou apontando para um servidor:
mlflow.set_tracking_uri("http://mlflow.local:5000")
# ou via variável de ambiente:
#   export MLFLOW_TRACKING_URI=...
```

**Análogo gerenciado (AWS):** MLflow Tracking → **SageMaker Experiments**. Mesma
ideia — rastrear runs, params e métricas — terceirizada na nuvem. Você aprende o
conceito no open-source e reconhece o serviço gerenciado como "a mesma coisa".

---

## 12. Boas práticas e armadilhas

- **Fixe o `MLFLOW_TRACKING_URI`.** A armadilha nº1 é rodar de pastas diferentes
  e criar vários `./mlruns` — runs somem porque foram para outro lugar.
- **Nomeie os runs e use tags desde o início.** 40 runs chamados `None` são
  impossíveis de comparar. `run_name` + tags de linhagem salvam a análise futura.
- **Logue a linhagem.** Um run sem a versão do dado não é reproduzível. Registre
  `data_md5` (do DVC) e `git_commit` como tags — é o que fecha a cadeia
  dados → código → modelo.
- **Autolog + manual.** Deixe o autolog pegar o trivial e logue manualmente o que
  importa para o negócio.
- **Não confunda param com metric.** Entrada é param; medida é metric. Trocar os
  dois quebra a ordenação e a comparação na UI.
- **Cuidado com artefatos grandes.** Logar datasets inteiros como artefato incha o
  store — para dados, use DVC; no MLflow, logue só o *hash* como tag.
- **Não logue segredos** (chaves, dados pessoais) em params/tags.

---

## 13. MLflow vs. alternativas

| Ferramenta | Foco | Quando preferir |
|---|---|---|
| **MLflow** | tracking + models + registry, open-source, self-hosted | padrão do curso; controle total, sem custo por seat |
| **Weights & Biases** | tracking + visualização ricos, SaaS | dashboards colaborativos, times distribuídos |
| **Neptune** | tracking gerenciado | metadados em escala, SaaS |
| **DVC experiments** | experimentos versionados via Git/DVC | quem já vive dentro do fluxo DVC e quer tudo no Git |

MLflow é a escolha do curso por ser open-source, completo (do tracking ao
registry) e por rodar localmente sem infra — o mesmo critério de "aprender onde
se vê o encanamento" que guiou DVC e Docker.

---

# 14. Guia de implementação no `prj_churn`

Aqui aplicamos tudo ao projeto. O objetivo: instrumentar o `train()` que já
existe, fechar a linhagem com o DVC, e ter um grid rastreado.

### 14.1 Dependência

```bash
uv add mlflow
```

### 14.2 Um utilitário de linhagem

O `train()` deve registrar **de qual versão do dado** ele veio. Essa versão é o
`md5` que o DVC guarda no `data/churn.csv.dvc`. Um helper lê esse hash:

```python
# src/churn/lineage.py
from pathlib import Path
import subprocess
import yaml


def data_md5(dvc_pointer: Path = Path("data/churn.csv.dvc")) -> str:
    """Lê o md5 do dado versionado pelo DVC (a versão exata do churn.csv)."""
    doc = yaml.safe_load(dvc_pointer.read_text())
    return doc["outs"][0]["md5"]


def git_commit() -> str:
    """Hash do commit atual — a versão exata do código."""
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
```

> No `churn.csv` que versionamos no Encontro 5, esse `md5` é
> `d390bd07b5514a2256a2396993b8b0e3` (v1). Ao trocar a versão do dado com
> `dvc checkout`, o helper passa a devolver o hash correspondente — a linhagem
> acompanha automaticamente.

### 14.3 Instrumentar o `train()`

Partimos do `src/churn/model.py` refatorado no Encontro 2 e adicionamos MLflow.
As mudanças estão comentadas com `# +mlflow`.

```python
# src/churn/model.py
import mlflow                                              # +mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from churn.config import Settings, settings
from churn.data import load_clean
from churn.evaluate import evaluate
from churn.features import (
    CategoricalEncoder, add_derived_features, split_features_target,
)
from churn.lineage import data_md5, git_commit             # +mlflow


def build_model(cfg: Settings) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=cfg.n_estimators, random_state=cfg.random_state,
    )


def train(cfg: Settings = settings) -> tuple[RandomForestClassifier, dict]:
    frame = add_derived_features(
        load_clean(cfg.data_path, cfg.id_column, cfg.target)
    )
    features, labels = split_features_target(frame, cfg.target, cfg.positive_label)
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=cfg.test_size,
        random_state=cfg.random_state, stratify=labels,
    )
    encoder = CategoricalEncoder().fit(x_train)

    mlflow.set_experiment("churn")                          # +mlflow
    with mlflow.start_run(run_name="rf"):                  # +mlflow
        # linhagem: qual dado + qual código geraram este modelo
        mlflow.set_tags({                                  # +mlflow
            "data_md5": data_md5(),
            "git_commit": git_commit(),
        })
        # a config Pydantic vira params (Pydantic → MLflow num passo só)
        mlflow.log_params(cfg.model_dump())                # +mlflow

        model = build_model(cfg).fit(encoder.transform(x_train), y_train)
        metrics = evaluate(model, encoder.transform(x_test), y_test)

        mlflow.log_metrics(metrics)                        # +mlflow
        # ⚠️ MLflow 3: troque artifact_path= por name=
        mlflow.sklearn.log_model(model, artifact_path="model")   # +mlflow

    return model, metrics


def main() -> None:
    _, metrics = train()
    print("métricas no teste:", metrics)


if __name__ == "__main__":
    main()
```

**Dois encaixes elegantes com o que já construímos:**

- `cfg.model_dump()` transforma o `Settings` (Pydantic) em um dicionário de
  params — os dois contratos do curso (Pydantic para config, MLflow para o run)
  se encontram em uma linha.
- `data_md5()` amarra o run à versão exata do dado no DVC. Agora todo modelo
  rastreia até o `churn.csv` que o gerou.

### 14.4 O grid rastreado (a tarefa de casa do Encontro 6)

```python
# src/churn/experiments.py
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from churn.config import settings as cfg
from churn.data import load_clean
from churn.evaluate import evaluate
from churn.features import (
    CategoricalEncoder, add_derived_features, split_features_target,
)


def run_grid() -> None:
    frame = add_derived_features(
        load_clean(cfg.data_path, cfg.id_column, cfg.target)
    )
    X, y = split_features_target(frame, cfg.target, cfg.positive_label)
    x_tr, x_te, y_tr, y_te = train_test_split(
        X, y, test_size=cfg.test_size, random_state=cfg.random_state, stratify=y,
    )
    enc = CategoricalEncoder().fit(x_tr)
    x_tr_e, x_te_e = enc.transform(x_tr), enc.transform(x_te)

    mlflow.set_experiment("churn")
    for n in (100, 200, 500):
        for depth in (None, 8, 16):
            with mlflow.start_run(run_name=f"rf-n{n}-d{depth}"):
                mlflow.log_params({"n_estimators": n, "max_depth": depth})
                model = RandomForestClassifier(
                    n_estimators=n, max_depth=depth,
                    random_state=cfg.random_state,
                ).fit(x_tr_e, y_tr)
                mlflow.log_metrics(evaluate(model, x_te_e, y_te))


if __name__ == "__main__":
    run_grid()
```

Rodar e depois achar o melhor:

```bash
uv run python -m churn.experiments      # 9 runs rastreados
uv run mlflow ui                        # inspecionar em localhost:5000
```

```python
# achar o melhor por código
import mlflow
runs = mlflow.search_runs(
    experiment_names=["churn"], order_by=["metrics.roc_auc DESC"],
)
best = runs.iloc[0]
print(best["run_id"], best["params.n_estimators"],
      best["params.max_depth"], best["metrics.roc_auc"])
```

### 14.5 Integração com o DVC (opcional, mas recomendada)

O `dvc.yaml` do Encontro 5 pode chamar o treino instrumentado. Assim, `dvc repro`
versiona dado + código + modelo, e o MLflow registra o experimento — as duas
ferramentas cobrem pontas complementares da linhagem.

```yaml
# dvc.yaml
stages:
  treino:
    cmd: uv run python -m churn.model
    deps:
      - data/churn.csv
      - src/churn
    outs:
      - artifacts/churn_model.pkl
```

> **Divisão de trabalho:** o DVC responde "qual dado e qual código" (versionamento
> reproduzível); o MLflow responde "qual experimento, com quais params e métricas"
> (comparação). A tag `data_md5` no run é a costura entre os dois.

### 14.6 Estrutura de arquivos resultante

```
prj_churn/
├─ src/churn/
│  ├─ config.py        # Settings (Pydantic)
│  ├─ data.py          # carga + validação (pandera, Enc. 4)
│  ├─ features.py      # transformações + encoder
│  ├─ model.py         # treino  ← instrumentado com MLflow
│  ├─ evaluate.py      # métricas
│  ├─ experiments.py   # +novo: grid rastreado
│  └─ lineage.py       # +novo: data_md5() e git_commit()
├─ data/churn.csv(.dvc)
├─ mlruns/             # +novo: backend local do MLflow (gitignored)
├─ dvc.yaml
└─ pyproject.toml      # +mlflow
```

Adicione `mlruns/` ao `.gitignore` (os experimentos locais não vão para o Git; em
time, use um tracking server).

### 14.7 Checklist de implementação

- [ ] `uv add mlflow`
- [ ] criar `src/churn/lineage.py` (`data_md5`, `git_commit`)
- [ ] instrumentar `train()` em `model.py` (experiment, tags, params, metrics, model)
- [ ] criar `src/churn/experiments.py` (grid)
- [ ] confirmar a assinatura de `log_model` para a versão instalada (`artifact_path` vs `name`)
- [ ] `mlruns/` no `.gitignore`
- [ ] rodar o grid e achar o melhor com `search_runs`
- [ ] (opcional) ligar o `dvc.yaml` ao treino instrumentado

---

## 15. Referências

- Documentação oficial: https://mlflow.org/docs/latest/index.html
- Tracking: https://mlflow.org/docs/latest/tracking.html
- Models: https://mlflow.org/docs/latest/models.html
- Model Registry: https://mlflow.org/docs/latest/model-registry.html
- Search runs / API Python: https://mlflow.org/docs/latest/python_api/mlflow.html

---

*Curso de MLOps — IESB · material de referência do Encontro 6 (Bloco 2: ML Pipeline).*
