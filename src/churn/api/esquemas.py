"""Contrato HTTP da API: o que entra e o que sai.

Os nomes dos campos repetem as colunas do CSV de propósito. O pipeline salvo
no MLflow foi treinado com essas colunas; renomear aqui só criaria uma
tradução a mais para manter.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SimNao = Literal["Yes", "No"]
ServicoInternet = Literal["No internet service", "No", "Yes"]
LinhaTelefonica = Literal["No phone service", "No", "Yes"]


class ClienteChurn(BaseModel):
    """Um cliente no formato aceito pelo pipeline de churn.

    ``customerID`` e ``Churn`` ficam de fora: o primeiro é identificador, o
    segundo é o alvo que queremos prever. ``extra="forbid"`` transforma um
    erro de digitação em 422, em vez de ignorá-lo silenciosamente.
    """

    model_config = ConfigDict(extra="forbid")

    gender: Literal["Female", "Male"] = Field(
        description="Gênero do cliente."
    )
    SeniorCitizen: int = Field(
        ge=0, le=1, description="1 se o cliente é idoso, 0 caso contrário."
    )
    Partner: SimNao = Field(description="O cliente tem cônjuge/parceiro?")
    Dependents: SimNao = Field(description="O cliente tem dependentes?")
    tenure: int = Field(
        ge=0, le=72, description="Meses de permanência na empresa."
    )
    PhoneService: SimNao = Field(description="Possui serviço de telefonia?")
    MultipleLines: LinhaTelefonica = Field(
        description="Possui múltiplas linhas telefônicas?"
    )
    InternetService: Literal["DSL", "Fiber optic", "No"] = Field(
        description="Tipo de serviço de internet."
    )
    OnlineSecurity: ServicoInternet = Field(
        description="Possui serviço de segurança online?"
    )
    OnlineBackup: ServicoInternet = Field(
        description="Possui serviço de backup online?"
    )
    DeviceProtection: ServicoInternet = Field(
        description="Possui proteção de dispositivo?"
    )
    TechSupport: ServicoInternet = Field(
        description="Possui suporte técnico?"
    )
    StreamingTV: ServicoInternet = Field(
        description="Possui streaming de TV?"
    )
    StreamingMovies: ServicoInternet = Field(
        description="Possui streaming de filmes?"
    )
    Contract: Literal["Month-to-month", "One year", "Two year"] = Field(
        description="Tipo de contrato."
    )
    PaperlessBilling: SimNao = Field(
        description="Usa cobrança sem papel?"
    )
    PaymentMethod: Literal[
        "Bank transfer (automatic)",
        "Credit card (automatic)",
        "Electronic check",
        "Mailed check",
    ] = Field(description="Forma de pagamento.")
    MonthlyCharges: float = Field(
        ge=18.0, le=120.0, description="Cobrança mensal em dólares."
    )
    TotalCharges: float = Field(
        ge=0.0, description="Total cobrado até hoje em dólares."
    )


class ClienteConsulta(ClienteChurn):
    """Campos do cliente usados pela interface e pelo modelo."""

    customerID: str
    TotalCharges: float | None = Field(default=None, ge=0.0)


class PrevisaoChurn(BaseModel):
    """Resposta de uma predição individual."""

    churn: SimNao = Field(
        description="Classe prevista: Yes indica risco de churn."
    )
    probabilidade: float = Field(
        ge=0.0, le=1.0, description="Probabilidade estimada de churn."
    )
    limiar: float = Field(
        ge=0.0,
        le=1.0,
        description="Limiar usado para converter probabilidade em classe.",
    )


class SaudeResposta(BaseModel):
    """Estado do processo e disponibilidade do modelo."""

    status: Literal["ok"] = Field(
        description="O processo HTTP está no ar e responde."
    )
    modelo_carregado: bool = Field(
        description="Indica se o champion foi carregado na inicialização."
    )
    origem: str | None = Field(
        default=None, description="URI de onde o modelo foi carregado."
    )


class InfoModelo(BaseModel):
    """Rastreabilidade da versão que está servindo."""

    origem: str = Field(description="URI do modelo carregado.")
    nome: str | None = Field(default=None, description="Nome no registry.")
    versao: str | None = Field(default=None, description="Versão registrada.")
    alias: str | None = Field(default=None, description="Alias usado na carga.")
    limiar: float = Field(
        ge=0.0, le=1.0, description="Limiar de decisão em uso."
    )
