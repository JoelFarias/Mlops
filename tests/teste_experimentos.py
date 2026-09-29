import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import numpy as np
import pandas as pd
import pytest
from mlflow.tracking import MlflowClient

from churn import experimentos
from churn.pipeline import criar_pipeline


def amostra():
    return pd.DataFrame({
        "customerID": [str(i) for i in range(100)],
        "TotalCharges": [float(100 + i) for i in range(100)],
        "tenure": [i % 72 for i in range(100)],
        "MonthlyCharges": [float(20 + i % 80) for i in range(100)],
        "Contract": ["Month-to-month", "One year"] * 50,
        "Churn": ["No", "Yes"] * 50,
    })


def teste_pipeline_aceita_categoria_nova_e_nao_altera_entrada():
    dados = amostra().drop(columns=["customerID", "Churn"])
    original = dados.copy(deep=True)
    modelo = criar_pipeline(n_estimators=2).fit(dados, [0, 1] * 50)
    novo = dados.iloc[:1].copy()
    novo["Contract"] = "categoria nova"
    novo["TotalCharges"] = " "
    assert modelo.predict(novo).shape == (1,)
    pd.testing.assert_frame_equal(dados, original)


def teste_tuning_registro_recarga_e_gate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dados = amostra()
    caminho = tmp_path / "churn.csv"
    dados.to_csv(caminho, index=False)
    uri = "sqlite:///" + (tmp_path / "tracking.db").as_posix()
    tracking_anterior = mlflow.get_tracking_uri()
    registry_anterior = mlflow.get_registry_uri()
    chamadas = []
    scores = iter([0.90, 0.85, 0.81])

    def avaliar(modelo, x, y):
        chamadas.append(set(x.index))
        return {"roc_auc": next(scores), "accuracy": 0.8, "f1": 0.7}

    monkeypatch.setattr(experimentos, "metricas", avaliar)
    try:
        resultado = experimentos.run_grid(
            caminho, uri, grid={"n_estimators": [2, 3], "max_depth": [2]},
        )
        assert chamadas[0] == chamadas[1]
        assert chamadas[0].isdisjoint(chamadas[2])
        assert resultado["params"]["n_estimators"] == 2
        assert resultado["promovido"]
        client = MlflowClient()
        versao = client.get_model_version_by_alias("churn", "champion")
        assert versao.run_id == resultado["run_id"]
        entrada = dados.drop(columns=["customerID", "Churn"]).head(3)
        original = mlflow.sklearn.load_model(resultado["model_uri"])
        recarregado = mlflow.pyfunc.load_model(resultado["deploy_uri"])
        np.testing.assert_array_equal(original.predict(entrada), recarregado.predict(entrada))
        runs = client.search_runs([client.get_experiment_by_name("churn-tuning").experiment_id])
        candidatos = [r for r in runs if "validation_roc_auc" in r.data.metrics]
        assert len(candidatos) == 2
        assert sum("test_roc_auc" in r.data.metrics for r in candidatos) == 1
        assert all(r.info.status == "FINISHED" for r in runs)

        scores = iter([0.95, 0.70])
        reprovado = experimentos.run_grid(caminho, uri, grid={"n_estimators": [2]})
        assert not reprovado["promovido"]
        assert client.get_model_version_by_alias("churn", "champion").version == versao.version
        assert len(client.search_model_versions("name='churn'")) == 1
    finally:
        mlflow.set_tracking_uri(tracking_anterior)
        mlflow.set_registry_uri(registry_anterior)


@pytest.mark.parametrize("limiar", [-0.1, 1.1, float("nan")])
def teste_rejeita_limiar_invalido(limiar):
    with pytest.raises(ValueError, match="limiar"):
        experimentos.run_grid(limiar=limiar)
