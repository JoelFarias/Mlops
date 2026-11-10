"""Frontend Streamlit para inferência online do modelo de churn.

O frontend tem dois modos:

* **Modelo local (Streamlit)**: o próprio processo carrega o alias
  ``churn@champion`` do MLflow e executa ``predict_proba``.
* **API FastAPI**: o frontend envia os dados para ``POST /prever`` e recebe a
  predição pronta.

A predição é feita no momento do clique. A busca por ``customerID`` usa
o CSV local ou a API, conforme a configuração da aplicação.

Executar na raiz do projeto:

    $env:PYTHONPATH = "src"
    python -m streamlit run src/churn/frontend/app.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st

# Permite `streamlit run src/churn/frontend/app.py` sem depender de PYTHONPATH.
RAIZ_SRC = Path(__file__).resolve().parents[2]
if str(RAIZ_SRC) not in sys.path:
    sys.path.insert(0, str(RAIZ_SRC))

from churn.api.servico import ServicoChurn
from churn.configuracao import Configuracao
from churn.frontend.dados import (
    buscar_cliente,
    carregar_clientes,
    montar_payload,
    tabela_informacoes,
)
from churn.frontend.inferencia import (
    carregar_modelo_local,
    info_modelo_local,
    prever_local,
)

API_PADRAO = os.getenv("CHURN_API_URL", "http://127.0.0.1:8000")
CODIGO_PADRAO = "1069-XAIEM"
EXEMPLOS = ("1069-XAIEM", "7590-VHVEG", "0902-XKXPN")
MODO_LOCAL = "Modelo local (Streamlit)"
MODO_API = "API FastAPI"
MODO_PUBLICO = os.getenv("CHURN_MODO_PUBLICO", "false").lower() in {"true", "1"}
CLIENTES_VIA_API = os.getenv("CHURN_CLIENTES_VIA_API", "false").lower() in {"true", "1"}
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Churn — inferência online",
    page_icon="📉",
    layout="wide",
)


def normalizar_api(url: str) -> str:
    """Aceita ``localhost:8000`` ou uma URL completa e remove a barra final."""
    url = (url or "").strip().rstrip("/")
    if not url:
        return API_PADRAO
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


def _detalhe_erro(resposta: requests.Response) -> str:
    try:
        corpo = resposta.json()
    except ValueError:
        return resposta.text.strip() or f"HTTP {resposta.status_code}"

    detalhe = corpo.get("detail") if isinstance(corpo, dict) else corpo
    if isinstance(detalhe, str):
        return detalhe
    return json.dumps(detalhe, ensure_ascii=False)


def _requisicao(
    metodo: str,
    url: str,
    *,
    timeout: float = 10.0,
    **kwargs: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    """Executa uma chamada HTTP e devolve ``(json, erro)``."""
    try:
        resposta = requests.request(metodo, url, timeout=timeout, **kwargs)
    except requests.RequestException as erro:
        return None, f"Não foi possível falar com a API em {url}: {erro}"

    if resposta.status_code >= 400:
        return None, _detalhe_erro(resposta)

    try:
        return resposta.json(), None
    except ValueError:
        return None, "A API respondeu um conteúdo que não é JSON."


def consultar_saude(api_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return _requisicao("GET", f"{api_url}/saude", timeout=5.0)


def consultar_modelo(api_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return _requisicao("GET", f"{api_url}/modelo", timeout=5.0)


def consultar_cliente_api(
    api_url: str, codigo: str
) -> tuple[pd.Series | None, str | None]:
    resposta, erro = _requisicao("GET", f"{api_url}/clientes", params={"codigo": codigo})
    if MODO_PUBLICO and erro:
        logger.warning("Falha na busca pública de cliente: %s", erro)
        return None, "Dados da demonstração temporariamente indisponíveis."
    return (pd.Series(resposta) if resposta is not None else None), erro


def recarregar_modelo(api_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return _requisicao("POST", f"{api_url}/modelo/recarregar", timeout=120.0)


def prever_cliente(
    api_url: str, payload: dict[str, Any]
) -> tuple[dict[str, Any] | None, str | None]:
    resposta, erro = _requisicao("POST", f"{api_url}/prever", json=payload)
    if MODO_PUBLICO and erro:
        logger.warning("Falha na inferência pública: %s", erro)
        return None, "Não foi possível calcular a previsão. Tente novamente em instantes."
    return resposta, erro


@st.cache_data(show_spinner=False)
def _carregar_dados(caminho: str) -> pd.DataFrame:
    return carregar_clientes(caminho)


@st.cache_resource(show_spinner=False)
def _modelo_local_cacheado() -> ServicoChurn:
    """Carrega o modelo uma vez por processo do Streamlit."""
    return carregar_modelo_local()


def _mostrar_info_modelo(info: dict[str, Any]) -> None:
    tabela_modelo = pd.DataFrame(
        [
            ("Nome", info.get("nome") or "—"),
            ("Versão", info.get("versao") or "—"),
            ("Alias", info.get("alias") or "—"),
            ("Limiar", f"{float(info.get('limiar', 0.0)):.0%}"),
        ],
        columns=["Campo", "Valor"],
    )
    st.table(tabela_modelo, hide_index=True)
    st.caption(f"Origem: {info.get('origem')}")


def mostrar_resultado(previsao: dict[str, Any], fonte: str) -> None:
    probabilidade = float(previsao["probabilidade"])
    limiar = float(previsao["limiar"])
    risco = previsao["churn"] == "Yes"

    st.divider()
    st.subheader("Resultado da inferência")

    if risco:
        st.error(
            "### SIM — risco de churn\n"
            f"Probabilidade estimada: **{probabilidade:.1%}**"
        )
    else:
        st.success(
            "### NÃO — cliente propenso a ficar\n"
            f"Probabilidade estimada: **{probabilidade:.1%}**"
        )

    colunas = st.columns(3)
    colunas[0].metric("Probabilidade de churn", f"{probabilidade:.1%}")
    colunas[1].metric("Limiar de decisão", f"{limiar:.0%}")
    colunas[2].metric(
        "Classe prevista", "Churn" if risco else "Não churn"
    )

    st.progress(
        probabilidade,
        text=f"Probabilidade de churn: {probabilidade:.1%}",
    )
    st.caption(
        "O cliente é classificado como churn quando a probabilidade "
        "é maior ou igual ao limiar."
    )
    st.caption(f"Fonte da inferência: **{fonte}**.")

    with st.expander("Resposta da inferência (JSON)"):
        st.json(previsao)


# ---------------------------------------------------------------------------
# Barra lateral: escolha da fonte e estado do modelo
# ---------------------------------------------------------------------------

modelo_local: ServicoChurn | None = None
api_url = normalizar_api(API_PADRAO)

with st.sidebar:
    st.header("Inferência")
    modo = MODO_API if MODO_PUBLICO else st.radio(
        "Fonte da inferência",
        (MODO_LOCAL, MODO_API),
        index=1 if os.getenv("CHURN_MODO_INFERENCIA", "local").lower() == "api" else 0,
        help=(
            "Local: o Streamlit carrega o modelo do MLflow e executa "
            "predict_proba. API: o Streamlit envia os dados para a FastAPI."
        ),
    )

    modo_anterior = st.session_state.get("modo_anterior")
    if modo_anterior is not None and modo_anterior != modo:
        st.session_state.consulta = None
    st.session_state.modo_anterior = modo

    if modo == MODO_LOCAL:
        try:
            with st.spinner("Carregando o champion do MLflow..."):
                modelo_local = _modelo_local_cacheado()
        except Exception as erro:
            st.error("Não foi possível carregar o modelo local")
            st.caption(str(erro))
        else:
            st.success("Modelo local carregado")
            st.subheader("Modelo em uso")
            _mostrar_info_modelo(info_modelo_local(modelo_local))

        if st.button(
            (
                "Recarregar modelo local"
                if modelo_local is not None
                else "Carregar modelo local"
            ),
            width="stretch",
            help="Limpa o cache e recarrega o champion do MLflow.",
        ):
            _modelo_local_cacheado.clear()
            st.session_state.consulta = None
            st.rerun()

        st.divider()
        st.caption(
            "A inferência é executada no próprio Streamlit: o champion "
            "é carregado do MLflow e mantido em cache. Cada consulta "
            "chama `predict_proba` localmente."
        )
    else:
        if not MODO_PUBLICO:
            api_url = normalizar_api(
                st.text_input(
                    "URL da API",
                    value=API_PADRAO,
                    help="Endereço da FastAPI que serve o modelo churn@champion.",
                )
            )

        saude, erro_saude = consultar_saude(api_url)
        modelo_carregado = bool(saude and saude.get("modelo_carregado"))

        if erro_saude:
            st.error("Serviço temporariamente indisponível")
            if not MODO_PUBLICO:
                st.caption(erro_saude)
        elif modelo_carregado:
            st.success("API online • modelo carregado")
        else:
            st.warning("API online • modelo não carregado")

        if not MODO_PUBLICO and st.button(
            (
                "Recarregar modelo na API"
                if modelo_carregado
                else "Carregar modelo na API"
            ),
            width="stretch",
            help=(
                "Chama POST /modelo/recarregar. Útil quando um novo "
                "champion foi promovido no MLflow."
            ),
        ):
            with st.spinner("Carregando o champion do MLflow..."):
                info_reload, erro_reload = recarregar_modelo(api_url)

            if info_reload:
                nome = info_reload.get("nome") or "churn"
                versao = info_reload.get("versao") or "?"
                st.success(f"Modelo {nome} v{versao} carregado.")
                modelo_carregado = True
            else:
                st.error(erro_reload or "Falha ao carregar o modelo.")

        if modelo_carregado and not MODO_PUBLICO:
            info_modelo, erro_modelo = consultar_modelo(api_url)
            if info_modelo:
                st.subheader("Modelo em uso")
                _mostrar_info_modelo(info_modelo)
            elif erro_modelo:
                st.caption(erro_modelo)

        if MODO_PUBLICO:
            st.caption("Demonstração com dados de exemplo, sem necessidade de cadastro.")
        else:
            st.divider()
            st.caption(
                "A inferência é executada pela FastAPI. O frontend apenas "
                "envia os dados para `POST /prever`."
            )

    if not MODO_PUBLICO:
        st.caption(f"Documentação da API: {api_url}/docs")


# ---------------------------------------------------------------------------
# Área principal: busca por código e resultado
# ---------------------------------------------------------------------------

st.title("Previsão de churn")
st.caption(
    "Consulte um cliente do dataset pelo código (`customerID`). "
    "A tabela mostra as informações básicas e o resultado é calculado "
    "na hora, no modo escolhido na barra lateral."
)

dados = None
if not CLIENTES_VIA_API:
    caminho_dados = Configuracao().caminho_dados
    try:
        dados = _carregar_dados(str(caminho_dados))
    except (FileNotFoundError, ValueError) as erro:
        if MODO_PUBLICO:
            logger.warning("Dados indisponíveis: %s", erro)
            st.error("Dados da demonstração temporariamente indisponíveis.")
        else:
            st.error(str(erro))
            st.info(
                "O frontend usa `data/raw/churn.csv` para buscar o cliente pelo "
                "código. Baixe o dataset e coloque-o nesse caminho."
            )
        st.stop()

with st.container(border=True):
    st.subheader("Consulta por código")
    with st.form("form_consulta"):
        codigo = st.text_input(
            "Código do cliente (`customerID`)",
            value=CODIGO_PADRAO,
            key="codigo_cliente",
            max_chars=64,
            placeholder="Ex.: 7590-VHVEG",
            help="O código é a coluna customerID do CSV do Telco Churn.",
        )
        consultar = st.form_submit_button(
            "Buscar e prever",
            type="primary",
            width="stretch",
        )
    exemplos = ", ".join(EXEMPLOS)
    st.caption(f"Exemplos: {exemplos}")

if consultar:
    codigo_limpo = codigo.strip()
    st.session_state.consulta = None

    if not codigo_limpo:
        st.session_state.consulta = {
            "erro": "Informe o código do cliente."
        }
    else:
        cliente, erro = (
            consultar_cliente_api(api_url, codigo_limpo)
            if dados is None
            else (buscar_cliente(dados, codigo_limpo), None)
        )
        if erro:
            st.session_state.consulta = {"erro": erro}
        elif cliente is None:
            st.session_state.consulta = {
                "erro": (
                    f"Código `{codigo_limpo}` não encontrado no dataset. "
                    f"Confira o customerID (exemplos: {exemplos})."
                )
            }
        else:
            info = tabela_informacoes(cliente)
            try:
                payload = montar_payload(cliente)
            except ValueError as erro:
                st.session_state.consulta = {
                    "codigo": cliente["customerID"],
                    "info": info,
                    "erro": str(erro),
                }
            else:
                fonte = (
                    MODO_API if modo == MODO_API else MODO_LOCAL
                )
                with st.spinner("Executando a inferência..."):
                    if modo == MODO_API:
                        previsao, erro = prever_cliente(api_url, payload)
                    elif modelo_local is not None:
                        try:
                            previsao = prever_local(modelo_local, payload)
                            erro = None
                        except Exception as exc:
                            previsao = None
                            erro = (
                                "Falha ao executar o modelo local: "
                                f"{exc}"
                            )
                    else:
                        previsao = None
                        erro = (
                            "Modelo local não carregado. Use o botão "
                            "na barra lateral para carregá-lo."
                        )

                st.session_state.consulta = {
                    "codigo": cliente["customerID"],
                    "info": info,
                    "payload": payload,
                    "previsao": previsao,
                    "erro": erro,
                    "fonte": fonte,
                }

consulta = st.session_state.get("consulta")
if consulta:
    if consulta.get("erro"):
        st.error(consulta["erro"])
    elif consulta.get("previsao"):
        mostrar_resultado(
            consulta["previsao"],
            consulta.get("fonte", MODO_API),
        )

    if consulta.get("info") is not None:
        st.subheader("Informações básicas do cliente")
        st.table(consulta["info"], hide_index=True)

        if consulta.get("payload"):
            with st.expander("Payload usado na inferência"):
                st.json(consulta["payload"])

st.divider()
if not MODO_PUBLICO:
    st.caption(
        f"Modo atual: **{modo}** · "
        f"API: [{api_url}/docs]({api_url}/docs)"
    )
