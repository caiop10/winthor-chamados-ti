# -*- coding: utf-8 -*-
"""
Modelos de dados - Chamados TI
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Usuario:
    """Representa um usuário do sistema"""
    matricula: int
    nome: str
    codsetor: int
    usuario_bd: str = ""

    @property
    def is_ti(self) -> bool:
        """Verifica se usuário é do setor TI"""
        from config.settings import settings
        return self.codsetor == 10 or self.matricula in settings.USUARIOS_TI

    @property
    def is_gerencia(self) -> bool:
        """Verifica se usuário tem acesso à gerência"""
        from config.settings import settings
        return self.matricula in settings.USUARIOS_GERENCIA


@dataclass
class HistoricoChamado:
    """Representa uma entrada no histórico do chamado"""
    datahora: datetime
    tipo: str
    matricula: int
    mensagem: str


@dataclass
class Anexo:
    """Representa um anexo de chamado"""
    id: int = None
    id_chamado: int = None
    caminho: str = ""
    datahora: datetime = None


@dataclass
class Chamado:
    """Representa um chamado de TI"""
    id: int
    matricula: int = None
    data_abertura: datetime = None
    categoria: str = ""
    prioridade: str = ""
    status: str = ""
    descricao: str = ""
    status_sla: str = ""
    data_limite_sla: datetime = None
    sla_minutos: int = None
    caminho_imagem: str = ""
    nome_usuario: str = ""
    setor: str = ""
    data_fechamento: datetime = None
    matricula_responsavel: int = None

    # Relacionamentos (carregados sob demanda)
    historico: List[HistoricoChamado] = field(default_factory=list)
    anexos: List[str] = field(default_factory=list)

    @property
    def is_aberto(self) -> bool:
        return self.status == "ABERTO"

    @property
    def is_em_resolucao(self) -> bool:
        return self.status == "EM_RESOLUCAO"

    @property
    def is_finalizado(self) -> bool:
        return self.status == "FINALIZADO"

    @property
    def is_aguardando(self) -> bool:
        return self.status == "AGUARDANDO"

    @property
    def tem_sla(self) -> bool:
        return self.sla_minutos is not None and self.sla_minutos > 0

    @property
    def sla_info(self) -> dict:
        """Retorna informações formatadas do SLA"""
        from utils.helpers import parse_sla_status
        return parse_sla_status(self.status_sla, self.data_limite_sla)

    @classmethod
    def from_row(cls, row: tuple, include_user_info: bool = False) -> 'Chamado':
        """
        Cria Chamado a partir de uma tupla do banco.

        Args:
            row: Tupla com dados
            include_user_info: Se True, espera colunas adicionais (nome_usuario, setor)
        """
        if include_user_info:
            # SELECT com JOIN para painel TI
            # ID, DATA_ABERTURA, NOME_USUARIO, SETOR, CATEGORIA, PRIORIDADE,
            # STATUS, STATUS_SLA, CAMINHO_IMAGEM, DATA_LIMITE_SLA, SLA_MINUTOS, DESCRICAO
            return cls(
                id=row[0],
                data_abertura=row[1],
                nome_usuario=row[2] or "",
                setor=row[3] or "",
                categoria=row[4] or "",
                prioridade=row[5] or "",
                status=row[6] or "",
                status_sla=row[7] or "",
                caminho_imagem=row[8] or "",
                data_limite_sla=row[9],
                sla_minutos=row[10],
                descricao=row[11] if len(row) > 11 else ""
            )
        else:
            # SELECT simples para meus chamados
            # ID, DATA_ABERTURA, CATEGORIA, PRIORIDADE, STATUS, STATUS_SLA,
            # CAMINHO_IMAGEM, DATA_LIMITE_SLA, SLA_MINUTOS
            return cls(
                id=row[0],
                data_abertura=row[1],
                categoria=row[2] or "",
                prioridade=row[3] or "",
                status=row[4] or "",
                status_sla=row[5] or "",
                caminho_imagem=row[6] or "",
                data_limite_sla=row[7],
                sla_minutos=row[8] if len(row) > 8 else None
            )

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'matricula': self.matricula,
            'data_abertura': self.data_abertura.isoformat() if self.data_abertura else None,
            'categoria': self.categoria,
            'prioridade': self.prioridade,
            'status': self.status,
            'descricao': self.descricao,
            'status_sla': self.status_sla,
            'sla_info': self.sla_info,
            'nome_usuario': self.nome_usuario,
            'setor': self.setor
        }
