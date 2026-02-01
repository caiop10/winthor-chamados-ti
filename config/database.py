# -*- coding: utf-8 -*-
"""
Pool de Conexões Oracle
"""
import oracledb
from .settings import settings

# Variável global do pool
_pool = None


class DatabasePool:
    """Gerenciador de pool de conexões Oracle"""

    def __init__(self):
        self._pool = None
        self._initialized = False

    def initialize(self):
        """Inicializa o Oracle Client e cria o pool"""
        if self._initialized:
            return

        try:
            # Inicializa Oracle em modo THICK (OCI)
            oracledb.init_oracle_client(lib_dir=settings.ORACLE_CLIENT)
        except Exception:
            # Já inicializado
            pass

        # Cria o pool de conexões
        self._pool = oracledb.create_pool(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            dsn=settings.dsn,
            min=settings.DB_POOL_MIN,
            max=settings.DB_POOL_MAX,
            increment=settings.DB_POOL_INCREMENT,
            getmode=oracledb.POOL_GETMODE_WAIT,
            homogeneous=True
        )
        self._initialized = True

    def get_connection(self):
        """Obtém uma conexão do pool"""
        if not self._initialized:
            self.initialize()
        return self._pool.acquire()

    def release_connection(self, conn):
        """Libera uma conexão de volta ao pool"""
        if conn and self._pool:
            self._pool.release(conn)

    def close(self):
        """Fecha o pool de conexões"""
        if self._pool:
            self._pool.close()
            self._pool = None
            self._initialized = False

    @property
    def is_initialized(self):
        return self._initialized

    @property
    def statistics(self):
        """Retorna estatísticas do pool"""
        if not self._pool:
            return None
        return {
            'busy': self._pool.busy,
            'open': self._pool.opened,
            'min': self._pool.min,
            'max': self._pool.max
        }


# Instância global do pool
db_pool = DatabasePool()


def get_connection():
    """
    Função de compatibilidade com código legado.
    Retorna uma conexão do pool.

    IMPORTANTE: A conexão DEVE ser fechada após uso!
    Usar preferencialmente com context manager:

    with get_connection() as conn:
        ...
    """
    return db_pool.get_connection()


class ConnectionContext:
    """Context manager para conexões com auto-close"""

    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = db_pool.get_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                self.conn.close()
        return False


def get_connection_context():
    """Retorna um context manager para conexão"""
    return ConnectionContext()
