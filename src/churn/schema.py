import pandera.pandas as pa
from pandera.typing import Series


class ChurnSchema(pa.DataFrameModel):
    # Tipos e restrições
    tenure: Series[int] = pa.Field(ge=0, le=72)
    MonthlyCharges: Series[float] = pa.Field(ge=18.0, le=120.0)
    TotalCharges: Series[float] = pa.Field(ge=0)

    Contract: Series[str] = pa.Field(
        isin=["Month-to-month", "One year", "Two year"]
    )
    Churn: Series[str] = pa.Field(isin=["Yes", "No"])

    class Config:
        coerce = True  # Converte os tipos automaticamente
        strict = False  # Tolera colunas extras
