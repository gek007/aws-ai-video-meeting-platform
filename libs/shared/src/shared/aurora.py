from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Callable


class AuroraBaseStore:
    def __init__(
        self,
        dsn: str | None = None,
        connection_factory: Callable[[], object] | None = None,
        *,
        env_var: str = "AURORA_DATABASE_URL",
        store_name: str = "AuroraStore",
    ) -> None:
        self._dsn = dsn or os.getenv(env_var) or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError(f"{env_var} or DATABASE_URL is required for {store_name}.")
        self._connection_factory = connection_factory

    @contextmanager
    def _connect(self):
        import psycopg

        conn = self._connection_factory() if self._connection_factory is not None else psycopg.connect(self._dsn)
        try:
            yield conn
        finally:
            conn.close()
