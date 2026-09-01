def teste_carregar_dados_le_arquivo_csv(tmp_path):
    from churn.dados import carregar_dados

    caminho_csv = tmp_path / "amostra.csv"
    caminho_csv.write_text(
        "cliente,Churn\nA,No\nB,Yes\n",
        encoding="utf-8",
    )

    dados = carregar_dados(caminho_csv)

    assert list(dados.columns) == ["cliente", "Churn"]
    assert dados.to_dict(orient="records") == [
        {"cliente": "A", "Churn": "No"},
        {"cliente": "B", "Churn": "Yes"},
    ]


def teste_limpar_dados_preserva_regras_do_script_original():
    import pandas as pd

    from churn.dados import limpar_dados

    dados_originais = pd.DataFrame(
        {
            "customerID": ["001", "002"],
            "TotalCharges": ["100.5", "valor_invalido"],
            "tenure": [1, 2],
            "MonthlyCharges": [20.0, 30.0],
            "Contract": ["Month-to-month", "One year"],
            "Churn": ["No", "Yes"],
        }
    )

    dados_limpos = limpar_dados(dados_originais)

    assert "customerID" not in dados_limpos.columns
    assert dados_limpos["TotalCharges"].tolist() == [100.5, 2200.0]
    assert dados_limpos["Churn"].tolist() == ["No", "Yes"]


def teste_schema_coleta_todas_as_falhas_com_lazy_true():
    import pandas as pd
    import pandera.pandas as pa
    import pytest

    from churn.dados import limpar_dados

    dados_quebrados = pd.DataFrame(
        {
            "customerID": ["001"],
            "TotalCharges": [100.0],
            "tenure": [999],
            "MonthlyCharges": [200.0],
            "Contract": ["Vitalicio"],
            "Churn": ["Talvez"],
        }
    )

    with pytest.raises(pa.errors.SchemaErrors) as erro:
        limpar_dados(dados_quebrados)

    colunas_com_erro = set(erro.value.failure_cases["column"])
    assert colunas_com_erro == {
        "tenure",
        "MonthlyCharges",
        "Contract",
        "Churn",
    }


def teste_remover_nulos_e_codificar_preserva_ordem_original():
    import pandas as pd

    from churn.dados import remover_nulos_e_codificar

    dados = pd.DataFrame(
        {
            "servico": ["B", "A", None],
            "Churn": ["No", "Yes", "No"],
            "numero": [1.0, 2.0, None],
        }
    )

    resultado = remover_nulos_e_codificar(dados)

    assert len(resultado) == 2
    assert resultado["servico"].tolist() == [1, 0]
    assert resultado["Churn"].tolist() == [0, 1]
    assert resultado.isna().sum().sum() == 0
