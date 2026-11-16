def teste_configuracao_usa_caminhos_do_projeto():
    from churn.configuracao import Configuracao, RAIZ_PROJETO

    configuracao = Configuracao()

    assert configuracao.caminho_dados == (
        RAIZ_PROJETO / "data" / "raw" / "churn.csv"
    )
