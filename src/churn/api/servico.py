"""Carregamento do modelo e execução das previsões.

O modelo é carregado uma única vez, na inicialização da aplicação. Cada
requisição apenas monta um DataFrame e chama ``predict_proba``: o pipeline do
scikit-learn já contém limpeza, imputação e codificação.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from churn.configuracao import Configuracao

logger = logging.getLogger(__name__)


@dataclass
class ServicoChurn:
    """Modelo em memória + regra que transforma probabilidade em classe."""

    modelo: Any
    origem: str
    limiar: float = 0.5
    nome: str | None = None
    versao: str | None = None
    alias: str | None = None

    def prever_lote(
        self, clientes: list[dict[str, Any]]
    ) -> list[tuple[int, float]]:
        """Prevê vários clientes em uma única chamada ao modelo."""
        if not clientes:
            return []

        entrada = pd.DataFrame(clientes)
        probabilidades = self.modelo.predict_proba(entrada)
        classes = list(getattr(self.modelo, "classes_", [0, 1]))
        if 1 not in classes:
            raise ValueError("O modelo precisa prever a classe 1 (churn).")
        coluna_churn = classes.index(1)

        return [
            (
                int(linha[coluna_churn] >= self.limiar),
                float(linha[coluna_churn]),
            )
            for linha in probabilidades
        ]

    def prever(self, cliente: dict[str, Any]) -> tuple[int, float]:
        """Prevê um cliente e devolve ``(classe, probabilidade)``."""
        return self.prever_lote([cliente])[0]


def carregar_servico(
    configuracao: Configuracao | None = None,
) -> ServicoChurn | None:
    """Tenta carregar o alias ``champion`` do registry.

    Devolver ``None`` (em vez de derrubar o processo) permite que a API suba
    mesmo quando o MLflow ainda não está disponível. ``/saude`` mostra essa
    condição e ``/prever`` responde 503 até o modelo existir.
    """
    config = configuracao or Configuracao()
    try:
        return carregar_modelo(config)
    except Exception as erro:  # noqa: BLE001 - falha de infraestrutura
        logger.warning("Não foi possível carregar o modelo: %s", erro)
        return None


def carregar_modelo(config: Configuracao) -> ServicoChurn:
    """Usa um pacote portátil quando MODELO_URI está definido."""
    if not config.modelo_uri:
        return carregar_do_registro(config)

    import mlflow.sklearn

    modelo = mlflow.sklearn.load_model(config.modelo_uri)
    caminho_metadados = Path(config.modelo_uri) / "deploy.json"
    metadados = (
        json.loads(caminho_metadados.read_text(encoding="utf-8"))
        if caminho_metadados.is_file()
        else {}
    )
    return ServicoChurn(
        modelo=modelo,
        origem=config.modelo_uri,
        limiar=config.limiar_churn,
        nome=metadados.get("nome", config.nome_modelo),
        versao=metadados.get("versao"),
        alias=metadados.get("alias"),
    )


def carregar_do_registro(config: Configuracao) -> ServicoChurn:
    """Lê ``models:/<nome>@<alias>`` do MLflow."""
    import mlflow
    import mlflow.sklearn
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(config.mlflow_tracking_uri)
    mlflow.set_registry_uri(config.mlflow_tracking_uri)

    cliente = MlflowClient()
    versao = cliente.get_model_version_by_alias(
        config.nome_modelo, config.alias_modelo
    )
    uri = f"models:/{config.nome_modelo}@{config.alias_modelo}"
    # Fixa a versão consultada, mesmo se o alias mudar durante o download.
    modelo = mlflow.sklearn.load_model(
        f"models:/{config.nome_modelo}/{versao.version}"
    )

    logger.info(
        "Modelo %s versão %s carregado de %s",
        config.nome_modelo,
        versao.version,
        uri,
    )
    return ServicoChurn(
        modelo=modelo,
        origem=uri,
        limiar=config.limiar_churn,
        nome=config.nome_modelo,
        versao=str(versao.version),
        alias=config.alias_modelo,
    )
