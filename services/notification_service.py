# -*- coding: utf-8 -*-
"""
Serviço de Notificações - Sons e alertas
"""
import os
from pathlib import Path
from typing import Optional
from utils.logger import logger


class NotificationService:
    """Serviço para notificações sonoras e visuais"""

    def __init__(self, sounds_dir: Path = None):
        """
        Inicializa o serviço de notificações.

        Args:
            sounds_dir: Diretório com arquivos de som
        """
        if sounds_dir is None:
            sounds_dir = Path(__file__).parent.parent / 'sounds'
        self.sounds_dir = sounds_dir
        self._winsound_available = self._check_winsound()
        self._plyer_available = self._check_plyer()

    def _check_winsound(self) -> bool:
        """Verifica se winsound está disponível (Windows)"""
        try:
            import winsound
            return True
        except ImportError:
            return False

    def _check_plyer(self) -> bool:
        """Verifica se plyer está disponível (notificações desktop)"""
        try:
            from plyer import notification
            return True
        except ImportError:
            return False

    def play_sound(self, sound_name: str = 'notification.wav') -> bool:
        """
        Toca um som de notificação.

        Args:
            sound_name: Nome do arquivo de som (sem caminho)

        Returns:
            True se som foi tocado, False caso contrário
        """
        sound_path = self.sounds_dir / sound_name

        if not sound_path.exists():
            logger.warning(f"Arquivo de som não encontrado: {sound_path}")
            return False

        try:
            if self._winsound_available:
                import winsound
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
        except Exception as e:
            logger.error(f"Erro ao tocar som: {e}")

        return False

    def play_new_chamado(self) -> bool:
        """Toca som de novo chamado"""
        return self.play_sound('new_chamado.wav') or self.play_sound('notification.wav')

    def play_resposta(self) -> bool:
        """Toca som de nova resposta"""
        return self.play_sound('resposta.wav') or self.play_sound('notification.wav')

    def play_alerta(self) -> bool:
        """Toca som de alerta (SLA crítico)"""
        return self.play_sound('alerta.wav') or self.play_sound('notification.wav')

    def show_notification(
        self,
        title: str,
        message: str,
        app_name: str = "Chamados TI",
        timeout: int = 10
    ) -> bool:
        """
        Mostra notificação desktop (toast).

        Args:
            title: Título da notificação
            message: Mensagem
            app_name: Nome do aplicativo
            timeout: Tempo em segundos para auto-fechar

        Returns:
            True se notificação foi mostrada
        """
        if not self._plyer_available:
            logger.debug("Plyer não disponível para notificações")
            return False

        try:
            from plyer import notification

            icon_path = Path(__file__).parent.parent / 'icon.ico'
            icon = str(icon_path) if icon_path.exists() else None

            notification.notify(
                title=title,
                message=message,
                app_name=app_name,
                app_icon=icon,
                timeout=timeout
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao mostrar notificação: {e}")
            return False

    def notify_new_chamado(self, id_chamado: int, categoria: str) -> bool:
        """Notifica novo chamado"""
        self.play_new_chamado()
        return self.show_notification(
            title="Novo Chamado",
            message=f"Chamado #{id_chamado} - {categoria}"
        )

    def notify_resposta(self, id_chamado: int) -> bool:
        """Notifica nova resposta em chamado"""
        self.play_resposta()
        return self.show_notification(
            title="Nova Resposta",
            message=f"Chamado #{id_chamado} recebeu uma resposta"
        )

    def notify_sla_critico(self, id_chamado: int, tempo_restante: str) -> bool:
        """Notifica SLA crítico"""
        self.play_alerta()
        return self.show_notification(
            title="SLA Crítico!",
            message=f"Chamado #{id_chamado} - Tempo restante: {tempo_restante}"
        )


# Instância global
notification_service = NotificationService()
