import pandas as pd


def teste_dividir_dados_mantem_proporcao_original():
    from churn.modelo import dividir_dados

    caracteristicas = pd.DataFrame({"valor": range(8)})
    alvo = pd.Series([0, 1, 0, 1, 0, 1, 0, 1])

    (
        caracteristicas_treino,
        caracteristicas_teste,
        alvo_treino,
        alvo_teste,
    ) = dividir_dados(caracteristicas, alvo)

    assert len(caracteristicas_treino) == 6
    assert len(caracteristicas_teste) == 2
    assert len(alvo_treino) == 6
    assert len(alvo_teste) == 2


def teste_treinar_modelo_mantem_duzentas_arvores():
    from churn.modelo import treinar_modelo

    caracteristicas = pd.DataFrame({"valor": range(8)})
    alvo = pd.Series([0, 1, 0, 1, 0, 1, 0, 1])

    modelo = treinar_modelo(caracteristicas, alvo)

    assert len(modelo.estimators_) == 200


def teste_salvar_modelo_grava_pickle_carregavel(tmp_path):
    import pickle

    from sklearn.dummy import DummyClassifier

    from churn.modelo import salvar_modelo

    caracteristicas = pd.DataFrame({"valor": [1, 2]})
    alvo = pd.Series([0, 1])
    modelo = DummyClassifier(strategy="most_frequent")
    modelo.fit(caracteristicas, alvo)
    caminho_modelo = tmp_path / "modelo_final_v3_ok.pkl"

    salvar_modelo(modelo, caminho_modelo)

    assert caminho_modelo.is_file()
    with caminho_modelo.open("rb") as arquivo_modelo:
        modelo_carregado = pickle.load(arquivo_modelo)
    assert modelo_carregado.predict(caracteristicas).tolist() == [0, 0]
