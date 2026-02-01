# -*- coding: utf-8 -*-
"""
Configurações do Sistema - Carrega variáveis do .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env do diretório do projeto
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / '.env')


class Settings:
    """Configurações centralizadas do sistema"""

    def __init__(self):
        # Oracle Database
        self.DB_USER = os.getenv('DB_USER', 'SOTRIGO')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        self.DB_HOST = os.getenv('DB_HOST', '10.4.23.2')
        self.DB_PORT = int(os.getenv('DB_PORT', '1521'))
        self.DB_SERVICE = os.getenv('DB_SERVICE', 'WINT')

        # Oracle Client
        self.ORACLE_CLIENT = os.getenv('ORACLE_CLIENT', r'C:\oracle\instantclient_23_0')

        # Pool de conexões
        self.DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', '2'))
        self.DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', '10'))
        self.DB_POOL_INCREMENT = int(os.getenv('DB_POOL_INCREMENT', '1'))

        # Flask
        self.FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
        self.FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

        # Servidor de arquivos
        self.SERVIDOR_REDE = os.getenv('SERVIDOR_REDE', r'\\192.168.0.155\Compartilhamentos')
        self.ANEXOS_DIR = os.getenv('ANEXOS_DIR', rf'{self.SERVIDOR_REDE}\imagens_chamados')

        # Usuários especiais
        self.USUARIOS_TI = self._parse_list(os.getenv('USUARIOS_TI', '14'))
        self.USUARIOS_GERENCIA = self._parse_list(os.getenv('USUARIOS_GERENCIA', '14'))

        # Cores SLA
        self.COR_SLA_OK = os.getenv('COR_SLA_OK', '#22c55e')
        self.COR_SLA_ATENCAO = os.getenv('COR_SLA_ATENCAO', '#f59e0b')
        self.COR_SLA_ATRASADO = os.getenv('COR_SLA_ATRASADO', '#ef4444')
        self.COR_SLA_FINALIZADO = os.getenv('COR_SLA_FINALIZADO', '#6b7280')
        self.COR_SLA_SEM = os.getenv('COR_SLA_SEM', '#9ca3af')

        # Auto-refresh
        self.AUTO_REFRESH_INTERVAL = int(os.getenv('AUTO_REFRESH_INTERVAL', '60'))

        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'chamados_ti.log')
        self.LOG_DIR = PROJECT_ROOT / 'logs'

        # Listas de opções
        self.LISTA_STATUS = ["Todos", "ABERTO", "EM_RESOLUCAO", "AGUARDANDO", "FINALIZADO"]
        self.LISTA_PRIORIDADE = ["Todas", "ALTA", "MEDIA", "BAIXA"]
        self.LISTA_CATEGORIA = [
            "Todas", "WinThor", "Impressora", "Internet", "Atualização",
            "Infra-estrutura", "Outros", "Suporte TOTVS", "Desenvolvimento"
        ]
        self.LISTA_CATEGORIA_ABERTURA = [
            "WinThor", "Impressora", "Internet", "Atualização",
            "Infra-estrutura", "Outros"
        ]
        self.LISTA_CATEGORIA_MOVER = [
            "WinThor", "Impressora", "Internet", "Atualização",
            "Infra-estrutura", "Outros", "Suporte TOTVS", "Desenvolvimento"
        ]
        self.LISTA_SLA = ["Todos", "No Prazo", "Atrasados", "Sem SLA", "Finalizados"]

        # Configura Oracle Client
        self._setup_oracle_env()

    def _parse_list(self, value):
        """Converte string separada por vírgula em lista de inteiros"""
        if not value:
            return []
        return [int(x.strip()) for x in value.split(',') if x.strip().isdigit()]

    def _setup_oracle_env(self):
        """Configura variáveis de ambiente do Oracle"""
        os.environ['ORACLE_HOME'] = self.ORACLE_CLIENT
        os.environ['TNS_ADMIN'] = self.ORACLE_CLIENT
        os.environ['PATH'] = self.ORACLE_CLIENT + ';' + os.environ.get('PATH', '')

    @property
    def dsn(self):
        """Retorna DSN no formato EZCONNECT"""
        return f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_SERVICE}"

    def validate(self):
        """Valida configurações obrigatórias"""
        errors = []
        if not self.DB_USER:
            errors.append("DB_USER não configurado")
        if not self.DB_PASSWORD:
            errors.append("DB_PASSWORD não configurado")
        if not self.DB_HOST:
            errors.append("DB_HOST não configurado")
        if errors:
            raise ValueError(f"Configurações inválidas: {', '.join(errors)}")
        return True


# Instância global
settings = Settings()
