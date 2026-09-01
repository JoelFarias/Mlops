from pathlib import Path

from churn.avaliacao import avaliar_modelo
from churn.caracteristicas import (
    criar_caracteristicas,
    normalizar_caracteristicas,
    separar_alvo,
)
from churn.configuracao import Configuracao
from churn.dados import (
    carregar_dados,
    limpar_dados,
    remover_nulos_e_codificar,
)
from churn.modelo import dividir_dados, salvar_modelo, treinar_modelo


def executar_treinamento(
    caminho_dados: str | Path,
    caminho_modelo: str | Path,
) -> None:
    dados = carregar_dados(caminho_dados)

    print(dados.shape)
    print(dados.head())
    print("churn:", dados["Churn"].value_counts())

    dados = limpar_dados(dados)
    dados = criar_caracteristicas(dados)
    dados = remover_nulos_e_codificar(dados)

    caracteristicas, alvo = separar_alvo(dados)
    caracteristicas = normalizar_caracteristicas(caracteristicas)

    (
        caracteristicas_treino,
        caracteristicas_teste,
        alvo_treino,
        alvo_teste,
    ) = dividir_dados(caracteristicas, alvo)
    modelo = treinar_modelo(caracteristicas_treino, alvo_treino)

    acuracia = avaliar_modelo(modelo, caracteristicas_teste, alvo_teste)
    print("acuracia:", acuracia)

    salvar_modelo(modelo, caminho_modelo)
    print("salvo!")


def main() -> None:
    configuracao = Configuracao()
    executar_treinamento(
        configuracao.caminho_dados,
        configuracao.caminho_modelo,
    )


if __name__ == "__main__":
    main()
