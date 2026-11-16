def teste_configuracao_usa_caminhos_do_projeto():
    from churn.configuracao import Configuracao, RAIZ_PROJETO

    configuracao = Configuracao()

    assert configuracao.caminho_dados == (
        RAIZ_PROJETO / "data" / "raw" / "churn.csv"
    )
    assert configuracao.caminho_modelo == (
        RAIZ_PROJETO / "modelo_final_v3_ok.pkl"
    )
