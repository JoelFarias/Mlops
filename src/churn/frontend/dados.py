"""Acesso aos dados de exemplo e montagem do payload do frontend.

Este módulo não importa Streamlit de propósito: assim a busca por código, a
tabela de informações e o payload podem ser testados com pytest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from churn.configuracao import Configuracao

COLUNAS_ENTRADA = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
]

TRADUCOES = {
    "gender": {"Female": "Feminino", "Male": "Masculino"},
    "Partner": {"Yes": "Sim", "No": "Não"},
    "Dependents": {"Yes": "Sim", "No": "Não"},
    "PhoneService": {"Yes": "Sim", "No": "Não"},
    "MultipleLines": {
        "Yes": "Sim",
        "No": "Não",
        "No phone service": "Sem serviço telefônico",
    },
    "InternetService": {
        "DSL": "DSL",
        "Fiber optic": "Fibra óptica",
        "No": "Não",
    },
    "Contract": {
        "Month-to-month": "Mensal",
        "One year": "Um ano",
        "Two year": "Dois anos",
    },
    "PaperlessBilling": {"Yes": "Sim", "No": "Não"},
    "PaymentMethod": {
        "Electronic check": "Cheque eletrônico",
        "Mailed check": "Cheque por correio",
        "Bank transfer (automatic)": "Transferência bancária (automática)",
        "Credit card (automatic)": "Cartão de crédito (automático)",
    },
}


def carregar_clientes(caminho: str | Path | None = None) -> pd.DataFrame:
    """Carrega o CSV de clientes e normaliza a coluna ``customerID``.

    O arquivo não é versionado no Git. Quando ele não existe, o frontend mostra
    uma mensagem explicando como obtê-lo; por isso a exceção é explícita.
    """
    caminho_dados = Path(caminho) if caminho else Configuracao().caminho_dados
    if not caminho_dados.is_file():
        raise FileNotFoundError(
            f"Dataset não encontrado em {caminho_dados}. "
            "Coloque o CSV em data/raw/churn.csv."
        )

    dados = pd.read_csv(caminho_dados, na_values=[" "])
    faltantes = [c for c in ["customerID", *COLUNAS_ENTRADA] if c not in dados]
    if faltantes:
        raise ValueError(
            "O CSV não tem as colunas esperadas: " + ", ".join(faltantes)
        )

    dados["customerID"] = dados["customerID"].astype(str).str.strip()
    return dados


def buscar_cliente(
    dados: pd.DataFrame, codigo: str
) -> pd.Series | None:
    """Busca um cliente pelo ``customerID``, sem diferenciar maiúsculas."""
    codigo = str(codigo).strip()
    if not codigo:
        return None

    mascara = dados["customerID"].str.upper() == codigo.upper()
    if not mascara.any():
        return None

    return dados.loc[mascara].iloc[0].copy()


def montar_payload(cliente: pd.Series) -> dict[str, Any]:
    """Converte uma linha do CSV no JSON aceito por ``POST /prever``.

    ``customerID`` e ``Churn`` ficam de fora. Tipos numpy são convertidos para
    tipos nativos do Python para que o ``requests`` consiga serializar o JSON.
    ``TotalCharges`` vazio (comum em clientes com ``tenure = 0``) vira 0.0.
    """
    payload: dict[str, Any] = {}
    for campo in COLUNAS_ENTRADA:
        if campo not in cliente.index:
            raise ValueError(f"Campo ausente no cliente: {campo}")

        valor = cliente[campo]
        if pd.isna(valor):
            if campo == "TotalCharges":
                payload[campo] = 0.0
                continue
            raise ValueError(f"O campo {campo} está vazio para este cliente.")

        if campo in {"SeniorCitizen", "tenure"}:
            payload[campo] = int(valor)
        elif campo in {"MonthlyCharges", "TotalCharges"}:
            payload[campo] = float(valor)
        else:
            payload[campo] = str(valor)

    return payload


def _traduzir(campo: str, valor: Any) -> str:
    if pd.isna(valor):
        return "—"
    texto = str(valor)
    return TRADUCOES.get(campo, {}).get(texto, texto)


def _moeda(valor: Any) -> str:
    if pd.isna(valor):
        return "—"
    formatado = f"{float(valor):,.2f}".replace(",", "X")
    return "US$ " + formatado.replace(".", ",").replace("X", ".")


def tabela_informacoes(cliente: pd.Series) -> pd.DataFrame:
    """Monta a tabela com as informações básicas exibidas no frontend."""
    tenure = int(cliente["tenure"])
    meses = "1 mês" if tenure == 1 else f"{tenure} meses"
    linhas = [
        ("Código", cliente["customerID"]),
        ("Gênero", _traduzir("gender", cliente["gender"])),
        ("Idoso", "Sim" if int(cliente["SeniorCitizen"]) == 1 else "Não"),
        ("Parceiro(a)", _traduzir("Partner", cliente["Partner"])),
        ("Dependentes", _traduzir("Dependents", cliente["Dependents"])),
        ("Meses de casa", meses),
        ("Internet", _traduzir("InternetService", cliente["InternetService"])),
        ("Contrato", _traduzir("Contract", cliente["Contract"])),
        ("Cobrança mensal", _moeda(cliente["MonthlyCharges"])),
        ("Total cobrado", _moeda(cliente["TotalCharges"])),
        (
            "Forma de pagamento",
            _traduzir("PaymentMethod", cliente["PaymentMethod"]),
        ),
    ]
    return pd.DataFrame(linhas, columns=["Informação", "Valor"])
