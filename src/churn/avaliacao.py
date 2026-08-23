import pandas as pd
from sklearn.metrics import accuracy_score


def avaliar_modelo(modelo, caracteristicas_teste: pd.DataFrame, alvo_teste: pd.Series):
    previsoes = modelo.predict(caracteristicas_teste)
    return accuracy_score(alvo_teste, previsoes)
