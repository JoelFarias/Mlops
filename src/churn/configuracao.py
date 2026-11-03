from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


RAIZ_PROJETO = Path(__file__).resolve().parents[2]


class Configuracao(BaseSettings):
    caminho_dados: Path = RAIZ_PROJETO / "data" / "raw" / "churn.csv"
    caminho_modelo: Path = RAIZ_PROJETO / "modelo_final_v3_ok.pkl"

    # Usados pela API: o mesmo backend atende Tracking e Registry.
    mlflow_tracking_uri: str = (
        "sqlite:///" + (RAIZ_PROJETO / "mlflow.db").as_posix()
    )
    nome_modelo: str = "churn"
    alias_modelo: str = "champion"
    # No deploy, aponta para o pacote MLflow exportado dentro da imagem.
    modelo_uri: str | None = None
    recarga_modelo_habilitada: bool = True
    limiar_churn: float = Field(default=0.5, ge=0.0, le=1.0)
