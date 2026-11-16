import pandas as pd


def criar_caracteristicas(dados: pd.DataFrame) -> pd.DataFrame:
    dados["gasto_por_mes"] = dados["TotalCharges"] / (dados["tenure"] + 1)
    return dados


def separar_alvo(dados: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    alvo = dados["Churn"]
    caracteristicas = dados.drop("Churn", axis=1)
    return caracteristicas, alvo


def normalizar_caracteristicas(
    caracteristicas: pd.DataFrame,
) -> pd.DataFrame:
    caracteristicas["MonthlyCharges"] = (
        caracteristicas["MonthlyCharges"] / 118.0
    )
    caracteristicas["TotalCharges"] = (
        caracteristicas["TotalCharges"] / 8600.0
    )
    caracteristicas["tenure"] = caracteristicas["tenure"] / 72.0
    return caracteristicas
