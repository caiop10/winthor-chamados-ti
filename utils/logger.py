# -*- coding: utf-8 -*-
"""
Sistema de Logging - Chamados TI
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = 'chamados_ti',
    log_dir: Path = None,
    log_file: str = 'chamados_ti.log',
    level: str = 'INFO',
    max_bytes: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura e retorna um logger com rotação de arquivos.

    Args:
        name: Nome do logger
        log_dir: Diretório para os arquivos de log
        log_file: Nome do arquivo de log
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Tamanho máximo do arquivo antes de rotacionar
        backup_count: Número de arquivos de backup a manter

    Returns:
        Logger configurado
    """
    # Determina diretório de logs
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / 'logs'

    # Cria diretório se não existir
    log_dir.mkdir(parents=True, exist_ok=True)

    # Cria logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove handlers existentes para evitar duplicação
    logger.handlers.clear()

    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para console (apenas em dev)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Logger global
logger = setup_logger()


class AuditLogger:
    """Logger específico para auditoria de operações"""

    def __init__(self, user_logger: logging.Logger = None):
        self._logger = user_logger or logger

    def log_login(self, matricula: int, nome: str, success: bool = True):
        """Registra tentativa de login"""
        status = "SUCESSO" if success else "FALHA"
        self._logger.info(f"LOGIN {status} | Matrícula: {matricula} | Nome: {nome}")

    def log_chamado_aberto(self, id_chamado: int, matricula: int, categoria: str):
        """Registra abertura de chamado"""
        self._logger.info(f"CHAMADO ABERTO | ID: {id_chamado} | Matrícula: {matricula} | Categoria: {categoria}")

    def log_chamado_assumido(self, id_chamado: int, matricula_analista: int):
        """Registra assunção de chamado"""
        self._logger.info(f"CHAMADO ASSUMIDO | ID: {id_chamado} | Analista: {matricula_analista}")

    def log_chamado_finalizado(self, id_chamado: int, matricula: int):
        """Registra finalização de chamado"""
        self._logger.info(f"CHAMADO FINALIZADO | ID: {id_chamado} | Matrícula: {matricula}")

    def log_resposta(self, id_chamado: int, matricula: int, tipo: str):
        """Registra resposta em chamado"""
        self._logger.info(f"RESPOSTA {tipo.upper()} | ID: {id_chamado} | Matrícula: {matricula}")

    def log_erro(self, operacao: str, erro: str, matricula: int = None):
        """Registra erro em operação"""
        mat_info = f" | Matrícula: {matricula}" if matricula else ""
        self._logger.error(f"ERRO {operacao}{mat_info} | {erro}")

    def log_db_operation(self, operation: str, table: str, details: str = ""):
        """Registra operação de banco de dados"""
        self._logger.debug(f"DB {operation} | Tabela: {table} | {details}")


# Instância global do audit logger
audit_logger = AuditLogger()
