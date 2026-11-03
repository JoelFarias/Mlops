import pandas as pd
import pytest
from fastapi.testclient import TestClient

from churn.api import aplicacao
from churn.api.aplicacao import app, obter_servico
from churn.api.servico import ServicoChurn
from churn.pipeline import criar_pipeline

CLIENTE = {
    "gender": "Female",
    "SeniorCitizen": 0,
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": 12,
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "OnlineBackup": "Yes",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "Yes",
    "StreamingMovies": "No",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 70.5,
    "TotalCharges": 845.5,
}


def amostra_treino() -> pd.DataFrame:
    linhas = []
    for i in range(40):
        linha = dict(CLIENTE)
        linha["tenure"] = i % 72
        linha["MonthlyCharges"] = 18.0 + i
        linha["TotalCharges"] = 100.0 + i * 10
        linha["Contract"] = "Two year" if i % 2 == 0 else "Month-to-month"
        linha["Churn"] = "No" if i % 2 == 0 else "Yes"
        linhas.append(linha)
    return pd.DataFrame(linhas)


class ModeloFixo:
    """Modelo mínimo para testar a regra de decisão sem treinar nada."""

    classes_ = [0, 1]

    def __init__(self, probabilidades: list[float]):
        self.probabilidades = probabilidades
        self.entrada = None

    def predict_proba(self, dados):
        self.entrada = dados.copy()
        return [[1 - p, p] for p in self.probabilidades]


@pytest.fixture(scope="module")
def servico_treinado() -> ServicoChurn:
    dados = amostra_treino()
    alvo = dados.pop("Churn").map({"No": 0, "Yes": 1})
    modelo = criar_pipeline(n_estimators=2).fit(dados, alvo)
    return ServicoChurn(modelo=modelo, origem="teste", limiar=0.5)


@pytest.fixture
def cliente_api(monkeypatch):
    # Evita consultar o MLflow real durante o lifespan dos testes.
    monkeypatch.setattr(aplicacao, "carregar_servico", lambda: None)
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def usar_modelo(servico: ServicoChurn) -> None:
    app.dependency_overrides[obter_servico] = lambda: servico


def teste_saude_responde_mesmo_sem_modelo(cliente_api):
    resposta = cliente_api.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "ok",
        "modelo_carregado": False,
        "origem": None,
    }


def teste_alias_health_responde_como_saude(cliente_api):
    resposta = cliente_api.get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def teste_pronto_sem_modelo_retorna_503(cliente_api):
    assert cliente_api.get("/pronto").status_code == 503


def teste_pronto_confirma_modelo_carregado(cliente_api, servico_treinado):
    usar_modelo(servico_treinado)

    resposta = cliente_api.get("/pronto")

    assert resposta.status_code == 200
    assert resposta.json()["modelo_carregado"] is True
    assert resposta.json()["origem"] == "teste"


def teste_pagina_inicial_serve_formulario(cliente_api):
    resposta = cliente_api.get("/")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
    assert "Previsão de churn" in resposta.text
    assert 'id="formulario"' in resposta.text


def teste_prever_sem_modelo_retorna_503(cliente_api):
    resposta = cliente_api.post("/prever", json=CLIENTE)

    assert resposta.status_code == 503
    assert "Modelo indisponível" in resposta.json()["detail"]


def teste_prever_retorna_classe_e_probabilidade(
    cliente_api, servico_treinado
):
    usar_modelo(servico_treinado)

    resposta = cliente_api.post("/prever", json=CLIENTE)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["churn"] in {"Yes", "No"}
    assert 0.0 <= corpo["probabilidade"] <= 1.0
    assert corpo["limiar"] == 0.5


def teste_info_modelo_expoe_origem(cliente_api, servico_treinado):
    usar_modelo(servico_treinado)

    resposta = cliente_api.get("/modelo")

    assert resposta.status_code == 200
    assert resposta.json()["origem"] == "teste"
    assert resposta.json()["versao"] is None


def teste_recarregar_modelo_atualiza_servico(
    cliente_api, monkeypatch, servico_treinado
):
    monkeypatch.setattr(
        aplicacao, "carregar_servico", lambda: servico_treinado
    )

    resposta = cliente_api.post("/modelo/recarregar")

    assert resposta.status_code == 200
    assert resposta.json()["origem"] == "teste"
    assert cliente_api.get("/saude").json()["modelo_carregado"] is True


def teste_recarregar_modelo_sem_mlflow_retorna_503(cliente_api):
    resposta = cliente_api.post("/modelo/recarregar")

    assert resposta.status_code == 503
    assert "Não foi possível carregar o modelo" in resposta.json()["detail"]


def teste_recarga_desabilitada_nao_executa_carregamento(cliente_api, monkeypatch):
    monkeypatch.setenv("RECARGA_MODELO_HABILITADA", "false")

    def nao_carregar():
        raise AssertionError("O ambiente público não deve executar recarga.")

    monkeypatch.setattr(aplicacao, "carregar_servico", nao_carregar)
    assert cliente_api.post("/modelo/recarregar").status_code == 403


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("tenure", 999),
        ("MonthlyCharges", 500.0),
        ("TotalCharges", -1.0),
        ("Contract", "Vitalicio"),
        ("gender", "Outro"),
    ],
)
def teste_rejeita_valores_fora_do_contrato(
    cliente_api, servico_treinado, campo, valor
):
    usar_modelo(servico_treinado)

    resposta = cliente_api.post("/prever", json={**CLIENTE, campo: valor})

    assert resposta.status_code == 422


def teste_rejeita_campo_desconhecido(cliente_api, servico_treinado):
    usar_modelo(servico_treinado)

    resposta = cliente_api.post(
        "/prever", json={**CLIENTE, "customerID": "001"}
    )

    assert resposta.status_code == 422


def teste_servico_envia_colunas_recebidas_e_aplica_limiar():
    modelo = ModeloFixo([0.6])
    servico = ServicoChurn(modelo=modelo, origem="teste", limiar=0.7)

    classe, probabilidade = servico.prever(CLIENTE)

    assert list(modelo.entrada.columns) == list(CLIENTE)
    assert probabilidade == 0.6
    assert classe == 0
