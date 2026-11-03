"""Aplicação FastAPI que serve o modelo de churn.

Rotas síncronas (``def``) rodam no threadpool do FastAPI. Isso é intencional:
``predict_proba`` é bloqueante e não deve travar o event loop.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse

from churn.api.esquemas import (
    ClienteChurn,
    InfoModelo,
    PrevisaoChurn,
    SaudeResposta,
)
from churn.api.servico import ServicoChurn, carregar_servico
from churn.configuracao import Configuracao

logger = logging.getLogger(__name__)

CAMINHO_PAGINA = Path(__file__).resolve().parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carrega o champion uma vez, no startup, e libera no shutdown."""
    app.state.servico = carregar_servico()
    yield


app = FastAPI(
    title="API de Churn",
    description=(
        "Serve o modelo <code>churn@champion</code> registrado no MLflow. "
        "O contrato de entrada usa as colunas do CSV, sem customerID e sem Churn."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def obter_servico(request: Request) -> ServicoChurn:
    """Dependência que falha com 503 quando o modelo não foi carregado."""
    servico = getattr(request.app.state, "servico", None)
    if servico is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Modelo indisponível. Verifique o MLflow e o alias champion."
            ),
        )
    return servico


@app.get("/", include_in_schema=False)
def raiz() -> FileResponse:
    """Interface web para preencher os dados e ver o resultado."""
    return FileResponse(CAMINHO_PAGINA, media_type="text/html")


@app.get("/saude", response_model=SaudeResposta, tags=["Operação"])
def saude(request: Request) -> SaudeResposta:
    """Liveness: o processo responde. O modelo pode estar ausente."""
    servico = getattr(request.app.state, "servico", None)
    return SaudeResposta(
        status="ok",
        modelo_carregado=servico is not None,
        origem=servico.origem if servico is not None else None,
    )


def _info_modelo(servico: ServicoChurn) -> InfoModelo:
    return InfoModelo(
        origem=servico.origem,
        nome=servico.nome,
        versao=servico.versao,
        alias=servico.alias,
        limiar=servico.limiar,
    )


@app.get("/health", include_in_schema=False)
def health(request: Request) -> SaudeResposta:
    """Alias de ``/saude`` para verificações de infraestrutura."""
    return saude(request)


@app.get("/modelo", response_model=InfoModelo, tags=["Operação"])
def info_modelo(
    servico: ServicoChurn = Depends(obter_servico),
) -> InfoModelo:
    """Mostra qual versão do registry está em uso."""
    return _info_modelo(servico)


@app.get("/pronto", response_model=SaudeResposta, tags=["Operação"])
def pronto(
    servico: ServicoChurn = Depends(obter_servico),
) -> SaudeResposta:
    """Readiness: só aceita tráfego quando o modelo está carregado."""
    return SaudeResposta(
        status="ok", modelo_carregado=True, origem=servico.origem
    )


@app.post(
    "/modelo/recarregar",
    response_model=InfoModelo,
    tags=["Operação"],
)
def recarregar_modelo(request: Request) -> InfoModelo:
    """Carrega o alias ``champion`` novamente, sem reiniciar o processo.

    Serve para adotar uma versão promovida no MLflow depois que a API já
    subiu. Se o MLflow estiver fora do ar, o serviço anterior é preservado.
    """
    if not Configuracao().recarga_modelo_habilitada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recarga desabilitada neste ambiente.",
        )
    servico = carregar_servico()
    if servico is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível carregar o modelo. Verifique o MLflow "
                "e o alias champion."
            ),
        )

    request.app.state.servico = servico
    return _info_modelo(servico)


@app.post("/prever", response_model=PrevisaoChurn, tags=["Inferência"])
def prever(
    cliente: ClienteChurn,
    servico: ServicoChurn = Depends(obter_servico),
) -> PrevisaoChurn:
    """Prevê a probabilidade de churn de um cliente."""
    try:
        classe, probabilidade = servico.prever(cliente.model_dump())
    except Exception:
        logger.exception("Falha ao executar o modelo")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao executar o modelo.",
        ) from None

    return PrevisaoChurn(
        churn="Yes" if classe == 1 else "No",
        probabilidade=probabilidade,
        limiar=servico.limiar,
    )
