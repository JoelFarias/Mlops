"""Pré-processamento compartilhado pelo treino e pela inferência."""

import pandas as pd
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder


def preparar_entrada(dados):
    dados = dados.copy()
    dados["TotalCharges"] = pd.to_numeric(dados["TotalCharges"], errors="coerce").fillna(2200)
    dados["gasto_por_mes"] = dados["TotalCharges"] / (dados["tenure"] + 1)
    return dados


def criar_pipeline(n_estimators=200, max_depth=None):
    preprocessador = ColumnTransformer([
        ("categoricas", Pipeline([
            ("imputar", SimpleImputer(strategy="most_frequent")),
            ("codificar", OneHotEncoder(handle_unknown="ignore")),
        ]), make_column_selector(dtype_include=["object", "string", "category"])),
        ("numericas", SimpleImputer(strategy="median"),
         make_column_selector(dtype_include="number")),
    ])
    return Pipeline([
        ("caracteristicas", FunctionTransformer(preparar_entrada)),
        ("preprocessamento", preprocessador),
        ("modelo", RandomForestClassifier(n_estimators=n_estimators,
                                          max_depth=max_depth, random_state=42,
                                          n_jobs=-1)),
    ])
