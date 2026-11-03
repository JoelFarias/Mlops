"""Inferência local do frontend Streamlit.

No modo local, o próprio processo do Streamlit carrega o champion do MLflow e
executa ``predict_proba``. No modo API, essa responsabilidade fica com a
FastAPI; os dois caminhos usam a mesma regra de decisão.
"""

from __future__ import annotations

from typing import Any

from churn.api.servico import ServicoChurn, carregar_modelo
from churn.configuracao import Configuracao


def carregar_modelo_local() -> ServicoChurn:
    """Carrega ``churn@champion`` no processo do frontend."""
    return carregar_modelo(Configuracao())


def prever_local(
    servico: ServicoChurn, payload: dict[str, Any]
) -> dict[str, Any]:
    """Executa a inferência e devolve o mesmo contrato de ``/prever``."""
    classe, probabilidade = servico.prever(payload)
    return {
        "churn": "Yes" if classe == 1 else "No",
        "probabilidade": probabilidade,
        "limiar": servico.limiar,
    }


def info_modelo_local(servico: ServicoChurn) -> dict[str, Any]:
    """Metadados do modelo local para a tabela da barra lateral."""
    return {
        "origem": servico.origem,
        "nome": servico.nome,
        "versao": servico.versao,
        "alias": servico.alias,
        "limiar": servico.limiar,
    }
