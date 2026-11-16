import pandas as pd
from sklearn.dummy import DummyClassifier


def teste_avaliar_modelo_calcula_acuracia():
    from churn.avaliacao import avaliar_modelo

    caracteristicas = pd.DataFrame({"valor": [1, 2, 3]})
    alvo = pd.Series([0, 0, 1])
    modelo = DummyClassifier(strategy="most_frequent")
    modelo.fit(caracteristicas, alvo)

    acuracia = avaliar_modelo(modelo, caracteristicas, alvo)

    assert acuracia == 2 / 3
