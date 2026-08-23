import pandas as pd


def teste_criar_caracteristicas_calcula_gasto_por_mes():
    from churn.caracteristicas import criar_caracteristicas

    dados = pd.DataFrame(
        {
            "TotalCharges": [2200.0, 100.0],
            "tenure": [9, 0],
        }
    )

    resultado = criar_caracteristicas(dados)

    assert resultado["gasto_por_mes"].tolist() == [220.0, 100.0]


def teste_separar_alvo_remove_churn_das_caracteristicas():
    from churn.caracteristicas import separar_alvo

    dados = pd.DataFrame(
        {
            "Churn": [0, 1],
            "tenure": [12, 24],
            "MonthlyCharges": [50.0, 75.0],
        }
    )

    caracteristicas, alvo = separar_alvo(dados)

    assert alvo.tolist() == [0, 1]
    assert list(caracteristicas.columns) == ["tenure", "MonthlyCharges"]


def teste_normalizar_caracteristicas_usa_divisores_originais():
    from churn.caracteristicas import normalizar_caracteristicas

    caracteristicas = pd.DataFrame(
        {
            "MonthlyCharges": [118.0, 59.0],
            "TotalCharges": [8600.0, 4300.0],
            "tenure": [72.0, 36.0],
            "gasto_por_mes": [100.0, 100.0],
        }
    )

    resultado = normalizar_caracteristicas(caracteristicas)

    assert resultado["MonthlyCharges"].tolist() == [1.0, 0.5]
    assert resultado["TotalCharges"].tolist() == [1.0, 0.5]
    assert resultado["tenure"].tolist() == [1.0, 0.5]
    assert resultado["gasto_por_mes"].tolist() == [100.0, 100.0]
