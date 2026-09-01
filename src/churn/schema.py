import pandera.pandas as pa
from pandera.typing import Series

class ChurnSchema(pa.DataFrameModel):
  #Tipos e Restrições
  tenure: Series[int] = pa.Field(ge=0, le=72)
  Monthlychanges: Series[float] = pa.Field(ge=18.0, le=120.0) #Faixa do slide
  TotalCharges: Series[float] = pa.Field(ge=0, nullable=True) #Permite nulos

  Contract: Series[str] = pa.field(
    isin=["Mês-a-Mês", "Um ano", "Dois anos"]
  )
  Churn: Series[str] = pa.Field(isin=["Sim", "Não"])

  class Config:
    Coerce = True #Converte os tipos auto
    Strict = False #Tolera colunas extras
