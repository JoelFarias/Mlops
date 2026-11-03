"""Exporta uma versão do champion para servir sem o banco local do MLflow."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from churn.configuracao import Configuracao, RAIZ_PROJETO


def exportar_modelo(
    destino: str | Path, configuracao: Configuracao | None = None
) -> Path:
    """Copia os artefatos da versão selecionada e registra sua procedência."""
    import mlflow
    import mlflow.sklearn
    from mlflow.tracking import MlflowClient

    config = configuracao or Configuracao()
    destino = Path(destino).resolve()
    if destino.exists():
        raise FileExistsError(
            f"O destino {destino} já existe. Use --destino com uma nova pasta."
        )

    mlflow.set_tracking_uri(config.mlflow_tracking_uri)
    mlflow.set_registry_uri(config.mlflow_tracking_uri)
    versao = MlflowClient().get_model_version_by_alias(
        config.nome_modelo, config.alias_modelo
    )
    uri = f"models:/{config.nome_modelo}/{versao.version}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="churn-export-") as temporario:
        origem = mlflow.artifacts.download_artifacts(
            artifact_uri=uri, dst_path=temporario
        )
        modelo = mlflow.sklearn.load_model(origem)
        if not callable(getattr(modelo, "predict_proba", None)):
            raise ValueError("O modelo precisa implementar predict_proba.")
        if 1 not in list(getattr(modelo, "classes_", [])):
            raise ValueError("O modelo precisa prever a classe 1 (churn).")
        metadados = {
            "nome": config.nome_modelo,
            "versao": str(versao.version),
            "alias": config.alias_modelo,
            "origem": uri,
            "run_id": versao.run_id,
        }
        (Path(origem) / "deploy.json").write_text(
            json.dumps(metadados, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        shutil.copytree(origem, destino)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino", type=Path, default=RAIZ_PROJETO / "artifacts" / "modelo"
    )
    args = parser.parse_args()
    print(exportar_modelo(args.destino))


if __name__ == "__main__":
    main()
