from pathlib import Path

from pydantic_settings import BaseSettings


RAIZ_PROJETO = Path(__file__).resolve().parents[2]


class Configuracao(BaseSettings):
    caminho_dados: Path = RAIZ_PROJETO / "data" / "raw" / "churn.csv"
    caminho_modelo: Path = RAIZ_PROJETO / "modelo_final_v3_ok.pkl"
