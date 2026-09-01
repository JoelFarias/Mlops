import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def dividir_dados(
    caracteristicas: pd.DataFrame,
    alvo: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    return train_test_split(caracteristicas, alvo, test_size=0.25)


def treinar_modelo(
    caracteristicas_treino: pd.DataFrame,
    alvo_treino: pd.Series,
) -> RandomForestClassifier:
    modelo = RandomForestClassifier(n_estimators=200)
    modelo.fit(caracteristicas_treino, alvo_treino)
    return modelo


def salvar_modelo(modelo, caminho_modelo: str | Path) -> None:
    pickle.dump(modelo, open(caminho_modelo, "wb"))
