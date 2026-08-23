from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder


def carregar_dados(caminho_csv: str | Path) -> pd.DataFrame:
    return pd.read_csv(caminho_csv)


def limpar_dados(dados: pd.DataFrame) -> pd.DataFrame:
    dados = dados.drop("customerID", axis=1)
    dados["TotalCharges"] = pd.to_numeric(
        dados["TotalCharges"], errors="coerce"
    )
    dados["TotalCharges"] = dados["TotalCharges"].fillna(2200)
    return dados


def remover_nulos_e_codificar(dados: pd.DataFrame) -> pd.DataFrame:
    dados = dados.dropna().copy()

    codificador = LabelEncoder()
    for coluna in dados.columns:
        if dados[coluna].dtype == "object":
            dados[coluna] = codificador.fit_transform(dados[coluna])

    return dados
