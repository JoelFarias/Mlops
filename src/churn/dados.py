from pathlib import Path

import pandas as pd

from churn.schema import ChurnSchema


def carregar_dados(caminho_csv: str | Path) -> pd.DataFrame:
    return pd.read_csv(caminho_csv, na_values=[" "])


def limpar_dados(dados: pd.DataFrame) -> pd.DataFrame:
    dados = dados.drop("customerID", axis=1).copy()
    dados["TotalCharges"] = pd.to_numeric(
        dados["TotalCharges"],
        errors="coerce",
    )
    dados["TotalCharges"] = dados["TotalCharges"].fillna(2200)

    return ChurnSchema.validate(dados, lazy=True)
