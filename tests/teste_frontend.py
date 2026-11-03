import pandas as pd
import pytest

from churn.api.servico import ServicoChurn
from churn.frontend.dados import (
    COLUNAS_ENTRADA,
    buscar_cliente,
    carregar_clientes,
    montar_payload,
    tabela_informacoes,
)
from churn.frontend.inferencia import info_modelo_local, prever_local


def cliente_exemplo() -> pd.Series:
    return pd.Series(
        {
            "customerID": "7590-VHVEG",
            "gender": "Female",
            "SeniorCitizen": 0,
            "Partner": "Yes",
            "Dependents": "No",
            "tenure": 1,
            "PhoneService": "No",
            "MultipleLines": "No phone service",
            "InternetService": "DSL",
            "OnlineSecurity": "No",
            "OnlineBackup": "Yes",
            "DeviceProtection": "No",
            "TechSupport": "No",
            "StreamingTV": "No",
            "StreamingMovies": "No",
            "Contract": "Month-to-month",
            "PaperlessBilling": "Yes",
            "PaymentMethod": "Electronic check",
            "MonthlyCharges": 29.85,
            "TotalCharges": 29.85,
            "Churn": "No",
        }
    )


def teste_buscar_cliente_ignora_maiusculas_e_espacos():
    segundo = cliente_exemplo().to_dict()
    segundo["customerID"] = "5575-GNVDE"
    dados = pd.DataFrame([cliente_exemplo().to_dict(), segundo])

    cliente = buscar_cliente(dados, "  7590-vhveg ")

    assert cliente is not None
    assert cliente["customerID"] == "7590-VHVEG"


def teste_buscar_cliente_inexistente_retorna_none():
    dados = pd.DataFrame([cliente_exemplo()])

    assert buscar_cliente(dados, "0000-AAAAA") is None
    assert buscar_cliente(dados, "   ") is None


def teste_montar_payload_remove_identificador_e_alvo():
    payload = montar_payload(cliente_exemplo())

    assert set(payload) == set(COLUNAS_ENTRADA)
    assert "customerID" not in payload
    assert "Churn" not in payload
    assert payload["SeniorCitizen"] == 0
    assert payload["tenure"] == 1
    assert payload["MonthlyCharges"] == 29.85
    assert isinstance(payload["tenure"], int)
    assert isinstance(payload["MonthlyCharges"], float)


def teste_montar_payload_total_charges_vazio_vira_zero():
    cliente = cliente_exemplo()
    cliente["TotalCharges"] = float("nan")

    payload = montar_payload(cliente)

    assert payload["TotalCharges"] == 0.0


def teste_montar_payload_rejeita_campo_obrigatorio_vazio():
    cliente = cliente_exemplo()
    cliente["Contract"] = None

    with pytest.raises(ValueError, match="Contract"):
        montar_payload(cliente)


def teste_tabela_informacoes_traduz_valores_basicos():
    tabela = tabela_informacoes(cliente_exemplo())

    assert list(tabela.columns) == ["Informação", "Valor"]
    valores = dict(zip(tabela["Informação"], tabela["Valor"]))
    assert valores["Código"] == "7590-VHVEG"
    assert valores["Gênero"] == "Feminino"
    assert valores["Idoso"] == "Não"
    assert valores["Meses de casa"] == "1 mês"
    assert valores["Internet"] == "DSL"
    assert valores["Contrato"] == "Mensal"
    assert valores["Cobrança mensal"] == "US$ 29,85"


def teste_carregar_clientes_le_csv_e_normaliza_codigo(tmp_path):
    caminho = tmp_path / "clientes.csv"
    pd.DataFrame(
        [{**cliente_exemplo().to_dict(), "customerID": " 7590-VHVEG "}]
    ).to_csv(caminho, index=False)

    dados = carregar_clientes(caminho)

    assert dados.loc[0, "customerID"] == "7590-VHVEG"
    assert buscar_cliente(dados, "7590-vhveg") is not None


def teste_carregar_clientes_arquivo_ausente(tmp_path):
    with pytest.raises(FileNotFoundError, match="Dataset"):
        carregar_clientes(tmp_path / "nao_existe.csv")


def teste_carregar_clientes_valida_colunas(tmp_path):
    caminho = tmp_path / "incompleto.csv"
    pd.DataFrame([{"customerID": "001"}]).to_csv(caminho, index=False)

    with pytest.raises(ValueError, match="colunas"):
        carregar_clientes(caminho)


class ModeloFixo:
    """Modelo mínimo para testar a inferência local sem MLflow."""

    classes_ = [0, 1]

    def __init__(self, probabilidade: float):
        self.probabilidade = probabilidade
        self.entrada = None

    def predict_proba(self, dados):
        self.entrada = dados.copy()
        return [[1 - self.probabilidade, self.probabilidade]]


def _servico(probabilidade: float, limiar: float = 0.5) -> ServicoChurn:
    return ServicoChurn(
        modelo=ModeloFixo(probabilidade),
        origem="teste",
        limiar=limiar,
        nome="churn",
        versao="7",
        alias="champion",
    )


def teste_prever_local_devolve_mesmo_contrato_da_api():
    servico = _servico(0.8)
    payload = montar_payload(cliente_exemplo())

    resultado = prever_local(servico, payload)

    assert resultado == {
        "churn": "Yes",
        "probabilidade": 0.8,
        "limiar": 0.5,
    }
    assert list(servico.modelo.entrada.columns) == COLUNAS_ENTRADA


def teste_prever_local_aplica_limiar():
    payload = montar_payload(cliente_exemplo())

    resultado = prever_local(_servico(0.8, limiar=0.9), payload)

    assert resultado["churn"] == "No"


def teste_info_modelo_local_expoe_metadados():
    info = info_modelo_local(_servico(0.8))

    assert info == {
        "origem": "teste",
        "nome": "churn",
        "versao": "7",
        "alias": "champion",
        "limiar": 0.5,
    }


@pytest.mark.parametrize("publico", [False, True])
def teste_interface_consulta_tres_codigos_seguidos(tmp_path, monkeypatch, publico):
    import json

    import requests
    from streamlit.testing.v1 import AppTest

    from churn.configuracao import RAIZ_PROJETO

    codigos = ["1069-XAIEM", "7590-VHVEG", "0902-XKXPN"]
    caminho = tmp_path / "clientes.csv"
    pd.DataFrame([
        {**cliente_exemplo().to_dict(), "customerID": codigo,
         "MonthlyCharges": 20.0 + indice}
        for indice, codigo in enumerate(codigos)
    ]).to_csv(caminho, index=False)
    monkeypatch.setenv("CAMINHO_DADOS", str(caminho))
    monkeypatch.setenv("CHURN_MODO_INFERENCIA", "api")
    monkeypatch.setenv("CHURN_MODO_PUBLICO", str(publico).lower())
    monkeypatch.setenv("CHURN_API_URL", "http://backend:8000")
    payloads = []

    def requisicao(metodo, url, **kwargs):
        assert url.startswith("http://backend:8000/")
        if url.endswith("/saude"):
            corpo = {"status": "ok", "modelo_carregado": True}
        elif url.endswith("/modelo"):
            corpo = {"origem": "teste", "nome": "churn", "versao": "1",
                     "alias": "champion", "limiar": 0.5}
        elif url.endswith("/prever"):
            payloads.append(kwargs["json"])
            corpo = {"churn": "No", "probabilidade": 0.1, "limiar": 0.5}
        else:
            raise AssertionError(f"Requisição inesperada: {metodo} {url}")
        resposta = requests.Response()
        resposta.status_code = 200
        resposta._content = json.dumps(corpo).encode()
        return resposta

    monkeypatch.setattr(requests, "request", requisicao)
    interface = AppTest.from_file(
        str(RAIZ_PROJETO / "src/churn/frontend/app.py"), default_timeout=30
    ).run()
    assert not interface.exception
    if publico:
        assert not interface.radio
        assert not any(campo.label == "URL da API" for campo in interface.text_input)
        assert not any("Recarregar" in botao.label for botao in interface.button)
        assert not any("http://backend" in legenda.value for legenda in interface.caption)
    for indice, codigo in enumerate(codigos):
        next(campo for campo in interface.text_input
             if "customerID" in campo.label).set_value(codigo)
        next(botao for botao in interface.button
             if botao.label == "Buscar e prever").click()
        interface.run()
        assert not interface.exception
        assert interface.session_state["consulta"]["codigo"] == codigo
        assert payloads[-1]["MonthlyCharges"] == 20.0 + indice
