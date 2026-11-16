# Histórico do projeto

Esta pasta preserva o código retirado do fluxo principal na reorganização.
São referências da versão `8a9b22f`; não são um segundo aplicativo mantido.

| Caminho | Conteúdo preservado |
| --- | --- |
| `train_churn.py` | Script monolítico original, com caminho absoluto. |
| `treino/Dockerfile` | Receita antiga que executava `churn.treinar`. |
| `treino/src/churn/` | Módulos do treino antigo e cópias dos módulos compartilhados antes do recorte. |
| `treino/tests/` | Testes do treino antigo, incluindo cópias dos testes compartilhados. |
| `dvc/` | Estrutura inicial do DVC e o antigo módulo de linhagem. |

Os arquivos arquivados conservam os imports e caminhos da estrutura original.
Não estão no `PYTHONPATH`, não são coletados pelo pytest do projeto e não
entram na imagem ou no pacote de deploy. Para estudar ou executar a estrutura
anterior completa, consulte o commit
[8a9b22f](https://github.com/JoelFarias/Mlops/tree/8a9b22f46cb2b9b940f8ab04c66abeac6a09ace4)
em uma cópia separada.

O fluxo mantido é `churn.experimentos` → `churn.exportar` → FastAPI/Streamlit.
Veja o [README principal](../README.md) e o
[guia técnico da aplicação](../docs/guia-tecnico.md).

Quando presente nesta máquina, o pickle antigo fica em `artefatos/`, ignorado
pelo Git. Esse arquivo não é distribuído nem usado pela aplicação atual.
