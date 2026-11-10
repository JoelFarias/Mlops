"""Busca dos dados de exemplo no PostgreSQL."""

from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from churn.api.esquemas import ClienteConsulta

CONSULTA_CLIENTE = sql.SQL(
    'SELECT {} FROM public.clientes WHERE upper(btrim("customerID")) = %s LIMIT 1'
).format(sql.SQL(", ").join(map(sql.Identifier, ClienteConsulta.model_fields)))


def buscar_cliente_postgres(
    caminho_dsn: Path, codigo: str
) -> dict[str, Any] | None:
    with psycopg.connect(
        caminho_dsn.read_text(encoding="utf-8").strip(),
        connect_timeout=4,
        options="-c statement_timeout=4000",
        row_factory=dict_row,
    ) as conexao:
        return conexao.execute(CONSULTA_CLIENTE, (codigo.strip().upper(),)).fetchone()
