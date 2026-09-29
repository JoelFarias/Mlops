import argparse
import hashlib
import json
import os
from pathlib import Path

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import ParameterGrid, train_test_split

from churn.configuracao import Configuracao, RAIZ_PROJETO
from churn.dados import carregar_dados, limpar_dados
from churn.mlflow import git_commit
from churn.pipeline import criar_pipeline


def metricas(modelo, x, y):
    return {
        "roc_auc": float(roc_auc_score(y, modelo.predict_proba(x)[:, 1])),
        "accuracy": float(accuracy_score(y, modelo.predict(x))),
        "f1": float(f1_score(y, modelo.predict(x), zero_division=0)),
    }


def run_grid(caminho_dados=None, tracking_uri=None, experimento="churn-tuning",
             nome_modelo="churn", limiar=0.80, grid=None):
    if not 0 <= limiar <= 1:
        raise ValueError("O limiar deve estar entre 0 e 1.")
    combinacoes = list(ParameterGrid(grid if grid is not None else {
        "n_estimators": [100, 200, 500], "max_depth": [None, 8, 16],
    }))
    if not combinacoes:
        raise ValueError("O grid deve conter pelo menos uma configuracao.")
    caminho = Path(caminho_dados or Configuracao().caminho_dados)
    dados = carregar_dados(caminho)
    limpar_dados(dados)  # Valida o contrato antes de iniciar qualquer run.
    x = dados.drop(columns=["Churn", "customerID"])
    y = dados["Churn"].map({"No": 0, "Yes": 1})
    x_dev, x_teste, y_dev, y_teste = train_test_split(
        x, y, test_size=0.20, stratify=y, random_state=42,
    )
    x_treino, x_val, y_treino, y_val = train_test_split(
        x_dev, y_dev, test_size=0.25, stratify=y_dev, random_state=42,
    )
    uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI") or (
        "sqlite:///" + (RAIZ_PROJETO / "mlflow.db").as_posix()
    )
    mlflow.set_tracking_uri(uri)
    mlflow.set_registry_uri(uri)
    mlflow.set_experiment(experimento)
    tags = {
        "data_sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
        "git_commit": git_commit(), "selecao": "validation_roc_auc",
    }
    melhor = None
    with mlflow.start_run(run_name="rf-tuning") as busca:
        mlflow.set_tags(tags)
        mlflow.log_params({"random_state": 42, "train_size": 0.60,
                           "validation_size": 0.20, "test_size": 0.20,
                           "limiar_teste": limiar})
        for params in combinacoes:
            with mlflow.start_run(run_name=f"rf-{params}", nested=True) as run:
                mlflow.set_tags(tags)
                mlflow.log_params({**params, "random_state": 42})
                modelo = criar_pipeline(**params).fit(x_treino, y_treino)
                valores = metricas(modelo, x_val, y_val)
                mlflow.log_metrics({f"validation_{k}": v for k, v in valores.items()})
                info = mlflow.sklearn.log_model(
                    modelo, name="model", serialization_format="cloudpickle",
                    signature=infer_signature(x_treino, modelo.predict(x_treino)),
                    input_example=x_treino.head(3),
                    code_paths=[str(RAIZ_PROJETO / "src" / "churn")],
                )
                # Empates mantem a primeira configuracao na ordem do grid.
                if melhor is None or valores["roc_auc"] > melhor["validation_roc_auc"]:
                    melhor = {"run_id": run.info.run_id, "model_uri": info.model_uri,
                              "validation_roc_auc": valores["roc_auc"],
                              "params": params, "modelo": modelo}
                print(f"{params}: validation_roc_auc={valores['roc_auc']:.4f}", flush=True)

        teste = metricas(melhor.pop("modelo"), x_teste, y_teste)
        client = MlflowClient()
        for chave, valor in teste.items():
            client.log_metric(melhor["run_id"], f"test_{chave}", valor)
        resultado = {**melhor, "test": teste, "limiar": limiar,
                     "promovido": teste["roc_auc"] >= limiar,
                     "busca_run_id": busca.info.run_id}
        mlflow.log_metrics({f"best_test_{k}": v for k, v in teste.items()})
        mlflow.set_tag("best_run_id", melhor["run_id"])
        if resultado["promovido"]:
            versao = mlflow.register_model(melhor["model_uri"], nome_modelo)
            client.set_model_version_tag(nome_modelo, versao.version, "data_sha256", tags["data_sha256"])
            client.set_registered_model_alias(nome_modelo, "champion", versao.version)
            resultado.update(version=versao.version, deploy_uri=f"models:/{nome_modelo}@champion")
        mlflow.log_dict(resultado, "selecao.json")
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=Configuracao().caminho_dados)
    parser.add_argument("--tracking-uri")
    parser.add_argument("--experimento", default="churn-tuning")
    parser.add_argument("--nome-modelo", default="churn")
    parser.add_argument("--limiar", type=float, default=0.80)
    args = parser.parse_args()
    resultado = run_grid(args.dados, args.tracking_uri, args.experimento,
                         args.nome_modelo, args.limiar)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if not resultado["promovido"]:
        raise SystemExit("Modelo abaixo do limiar; alias champion preservado.")


if __name__ == "__main__":
    main()
