# -*- coding: utf-8 -*-
"""
Funções auxiliares - Chamados TI
"""
from datetime import datetime, timedelta
from typing import Optional, Any


def format_datetime(dt: datetime, format: str = "%d/%m/%Y %H:%M") -> str:
    """Formata datetime para string"""
    if dt is None:
        return ""
    return dt.strftime(format)


def format_date(dt: datetime, format: str = "%d/%m/%Y") -> str:
    """Formata data para string"""
    if dt is None:
        return ""
    return dt.strftime(format)


def format_sla_time(minutes: int) -> str:
    """
    Formata minutos em formato legível (ex: 2h30min ou -1h20min)
    """
    if minutes is None:
        return "Sem SLA"

    sign = ""
    if minutes < 0:
        sign = "-"
        minutes = abs(minutes)

    hours = minutes // 60
    mins = minutes % 60

    if hours > 0:
        return f"{sign}{hours}h{mins:02d}min"
    return f"{sign}{mins}min"


def safe_int(value: Any, default: int = 0) -> int:
    """Converte valor para int de forma segura"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Converte valor para string de forma segura"""
    if value is None:
        return default
    return str(value)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Trunca texto para tamanho máximo"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_business_hours(start: datetime, end: datetime) -> int:
    """
    Calcula horas úteis entre duas datas.
    Considera: 08:00-18:00, segunda a sexta.
    """
    if not start or not end:
        return 0

    business_start_hour = 8
    business_end_hour = 18
    total_minutes = 0

    current = start
    while current < end:
        # Pula finais de semana
        if current.weekday() < 5:  # Segunda a Sexta
            day_start = current.replace(
                hour=business_start_hour, minute=0, second=0, microsecond=0
            )
            day_end = current.replace(
                hour=business_end_hour, minute=0, second=0, microsecond=0
            )

            # Ajusta para horário comercial
            work_start = max(current, day_start)
            work_end = min(end, day_end)

            if work_start < work_end:
                diff = work_end - work_start
                total_minutes += diff.total_seconds() / 60

        # Próximo dia
        current = (current + timedelta(days=1)).replace(
            hour=business_start_hour, minute=0, second=0, microsecond=0
        )

    return int(total_minutes)


def parse_sla_status(status_sla: str, data_limite: datetime) -> dict:
    """
    Analisa status do SLA e retorna informações formatadas.

    Returns:
        dict com: status, cor, tempo_restante, descricao
    """
    from config.settings import settings

    now = datetime.now()
    result = {
        'status': status_sla or 'SEM_SLA',
        'cor': settings.COR_SLA_SEM,
        'tempo_restante': None,
        'descricao': 'Sem SLA definido'
    }

    if status_sla == 'FINALIZADO':
        result['cor'] = settings.COR_SLA_FINALIZADO
        result['descricao'] = 'Finalizado'
        return result

    if not data_limite:
        return result

    diff = data_limite - now
    minutos = int(diff.total_seconds() / 60)
    result['tempo_restante'] = minutos

    if minutos < 0:
        result['status'] = 'ATRASADO'
        result['cor'] = settings.COR_SLA_ATRASADO
        result['descricao'] = f'Atrasado: {format_sla_time(minutos)}'
    elif minutos <= 60:  # Menos de 1 hora
        result['status'] = 'ATENCAO'
        result['cor'] = settings.COR_SLA_ATENCAO
        result['descricao'] = f'Atenção: {format_sla_time(minutos)}'
    else:
        result['status'] = 'NO_PRAZO'
        result['cor'] = settings.COR_SLA_OK
        result['descricao'] = f'No prazo: {format_sla_time(minutos)}'

    return result


def is_network_available(path: str, timeout: float = 2.0) -> bool:
    """Verifica se caminho de rede está disponível"""
    import os
    try:
        return os.path.exists(path)
    except Exception:
        return False


def get_file_extension(filename: str) -> str:
    """Retorna extensão do arquivo em minúsculas"""
    if not filename:
        return ""
    parts = filename.rsplit('.', 1)
    return parts[1].lower() if len(parts) > 1 else ""


def is_image_file(filename: str) -> bool:
    """Verifica se arquivo é imagem"""
    extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    return get_file_extension(filename) in extensions
