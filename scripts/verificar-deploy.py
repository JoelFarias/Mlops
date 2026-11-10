"""Smoke test HTTP, executável no host ou no container da API."""

import argparse
import json
import os
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--frontend", default="http://frontend:8501")
    args = parser.parse_args()

    with urlopen(f"{args.api}/pronto", timeout=15) as resposta:
        saude = json.load(resposta)
    assert saude["modelo_carregado"] is True, saude
    with urlopen(f"{args.api}/modelo", timeout=15) as resposta:
        modelo = json.load(resposta)
    with urlopen(f"{args.frontend}/_stcore/health", timeout=15) as resposta:
        assert resposta.status == 200

    cliente = {
        "gender": "Female", "SeniorCitizen": 0, "Partner": "Yes",
        "Dependents": "No", "tenure": 12, "PhoneService": "Yes",
        "MultipleLines": "No", "InternetService": "Fiber optic",
        "OnlineSecurity": "No", "OnlineBackup": "Yes",
        "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
        "StreamingMovies": "No", "Contract": "Month-to-month",
        "PaperlessBilling": "Yes", "PaymentMethod": "Electronic check",
        "MonthlyCharges": 70.5, "TotalCharges": 845.5,
    }
    codigo = None
    if os.getenv("POSTGRES_CLIENTES_DSN_ARQUIVO"):
        codigo = "1069-XAIEM"
        with urlopen(f"{args.api}/clientes?codigo={codigo}", timeout=15) as resposta:
            cliente = json.load(resposta)
        assert cliente and cliente.pop("customerID") == codigo, cliente
        if cliente["TotalCharges"] is None:
            cliente["TotalCharges"] = 0.0
    requisicao = Request(
        f"{args.api}/prever", data=json.dumps(cliente).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(requisicao, timeout=30) as resposta:
        previsao = json.load(resposta)
    assert previsao["churn"] in {"Yes", "No"}, previsao
    assert 0 <= previsao["probabilidade"] <= 1, previsao
    assert previsao["churn"] == (
        "Yes" if previsao["probabilidade"] >= previsao["limiar"] else "No"
    ), previsao
    relatorio = {"modelo": modelo, "previsao": previsao}
    if codigo:
        relatorio["cliente_postgres"] = codigo
    print(json.dumps(relatorio, indent=2))


if __name__ == "__main__":
    main()
