def teste_executar_treinamento_salva_modelo(tmp_path, capsys):
    from churn.treinar import executar_treinamento

    caminho_dados = tmp_path / "churn.csv"
    caminho_dados.write_text(
        "customerID,TotalCharges,tenure,MonthlyCharges,Churn\n"
        "001,100,1,20,No\n"
        "002,200,2,30,Yes\n"
        "003,300,3,40,No\n"
        "004,400,4,50,Yes\n"
        "005,500,5,60,No\n"
        "006,600,6,70,Yes\n"
        "007,700,7,80,No\n"
        "008,800,8,90,Yes\n",
        encoding="utf-8",
    )
    caminho_modelo = tmp_path / "modelo_final_v3_ok.pkl"

    executar_treinamento(caminho_dados, caminho_modelo)

    saida = capsys.readouterr().out
    assert caminho_modelo.is_file()
    assert "acuracia:" in saida
    assert "salvo!" in saida
