# -*- coding: utf-8 -*-
"""
Serviço de SLA - Cálculo e monitoramento
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple
from config.settings import settings


class SLAService:
    """Serviço para cálculos e análise de SLA"""

    # Definição de SLA por prioridade (em minutos)
    SLA_MINUTOS = {
        'ALTA': 60,      # 1 hora
        'MEDIA': 240,    # 4 horas
        'BAIXA': 480     # 8 horas
    }

    @classmethod
    def calcular_sla(cls, prioridade: str) -> int:
        """Retorna SLA em minutos para a prioridade"""
        return cls.SLA_MINUTOS.get(prioridade, 480)

    @classmethod
    def calcular_data_limite(cls, data_abertura: datetime, prioridade: str) -> datetime:
        """Calcula data limite considerando horário comercial"""
        sla_minutos = cls.calcular_sla(prioridade)
        return data_abertura + timedelta(minutes=sla_minutos)

    @classmethod
    def calcular_status_sla(
        cls,
        data_limite: datetime,
        status_chamado: str
    ) -> Tuple[str, str, int]:
        """
        Calcula status do SLA.

        Returns:
            Tupla (status_sla, cor, minutos_restantes)
        """
        # Chamado finalizado
        if status_chamado == 'FINALIZADO':
            return ('FINALIZADO', settings.COR_SLA_FINALIZADO, 0)

        # Sem data limite definida
        if not data_limite:
            return ('SEM_SLA', settings.COR_SLA_SEM, 0)

        now = datetime.now()
        diff = data_limite - now
        minutos = int(diff.total_seconds() / 60)

        # Atrasado
        if minutos < 0:
            return ('ATRASADO', settings.COR_SLA_ATRASADO, minutos)

        # Atenção (menos de 30 minutos)
        if minutos <= 30:
            return ('ATENCAO', settings.COR_SLA_ATENCAO, minutos)

        # No prazo
        return ('NO_PRAZO', settings.COR_SLA_OK, minutos)

    @classmethod
    def formatar_tempo_sla(cls, minutos: int) -> str:
        """
        Formata minutos em formato legível.

        Exemplos:
            45 -> "45min"
            90 -> "1h30min"
            -30 -> "-30min (atrasado)"
        """
        if minutos is None:
            return "Sem SLA"

        atrasado = minutos < 0
        minutos_abs = abs(minutos)

        horas = minutos_abs // 60
        mins = minutos_abs % 60

        if horas > 0:
            texto = f"{horas}h{mins:02d}min"
        else:
            texto = f"{mins}min"

        if atrasado:
            return f"-{texto}"
        return texto

    @classmethod
    def obter_cor_sla(cls, status_sla: str) -> str:
        """Retorna cor para o status do SLA"""
        cores = {
            'NO_PRAZO': settings.COR_SLA_OK,
            'ATENCAO': settings.COR_SLA_ATENCAO,
            'ATRASADO': settings.COR_SLA_ATRASADO,
            'FINALIZADO': settings.COR_SLA_FINALIZADO,
            'SEM_SLA': settings.COR_SLA_SEM
        }
        return cores.get(status_sla, settings.COR_SLA_SEM)

    @classmethod
    def analisar_chamado(cls, chamado) -> Dict:
        """
        Analisa SLA de um chamado e retorna informações completas.

        Returns:
            Dict com: status, cor, tempo_restante, tempo_formatado, descricao
        """
        status, cor, minutos = cls.calcular_status_sla(
            chamado.data_limite_sla,
            chamado.status
        )

        descricoes = {
            'NO_PRAZO': f'No prazo ({cls.formatar_tempo_sla(minutos)})',
            'ATENCAO': f'Atenção! ({cls.formatar_tempo_sla(minutos)})',
            'ATRASADO': f'ATRASADO ({cls.formatar_tempo_sla(minutos)})',
            'FINALIZADO': 'Finalizado',
            'SEM_SLA': 'Sem SLA definido'
        }

        return {
            'status': status,
            'cor': cor,
            'tempo_restante': minutos,
            'tempo_formatado': cls.formatar_tempo_sla(minutos),
            'descricao': descricoes.get(status, 'Desconhecido')
        }

    @classmethod
    def filtrar_por_sla(cls, chamados: list, filtro_sla: str) -> list:
        """
        Filtra lista de chamados pelo status de SLA.

        Args:
            chamados: Lista de objetos Chamado
            filtro_sla: "Todos", "No Prazo", "Atrasados", "Sem SLA", "Finalizados"

        Returns:
            Lista filtrada de chamados
        """
        if filtro_sla == "Todos":
            return chamados

        filtrados = []
        for chamado in chamados:
            info = cls.analisar_chamado(chamado)

            if filtro_sla == "No Prazo" and info['status'] in ('NO_PRAZO', 'ATENCAO'):
                filtrados.append(chamado)
            elif filtro_sla == "Atrasados" and info['status'] == 'ATRASADO':
                filtrados.append(chamado)
            elif filtro_sla == "Sem SLA" and info['status'] == 'SEM_SLA':
                filtrados.append(chamado)
            elif filtro_sla == "Finalizados" and info['status'] == 'FINALIZADO':
                filtrados.append(chamado)

        return filtrados
