# -*- coding: utf-8 -*-
"""
Serviço de Notificações - Sons, alertas e polling de notificações
"""
import os
import threading
import time
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from utils.logger import logger


@dataclass
class Notificacao:
    """Representa uma notificação"""
    id: int
    id_chamado: int
    tipo: str
    titulo: str
    mensagem: str
    datahora: datetime


class NotificationService:
    """Serviço para notificações sonoras, visuais e polling"""

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

        # Polling
        self._polling_thread: Optional[threading.Thread] = None
        self._polling_active = False
        self._matricula: Optional[int] = None
        self._callback: Optional[Callable] = None
        self._intervalo_polling = 30  # segundos

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

    # ========== Sons ==========

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
            # Tentar som padrão do Windows
            try:
                if self._winsound_available:
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                    return True
            except:
                pass
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
        return self.play_sound('new_chamado.wav') or self._beep_default()

    def play_resposta(self) -> bool:
        """Toca som de nova resposta"""
        return self.play_sound('resposta.wav') or self._beep_default()

    def play_alerta(self) -> bool:
        """Toca som de alerta (SLA crítico)"""
        return self.play_sound('alerta.wav') or self._beep_default()

    def _beep_default(self) -> bool:
        """Toca beep padrão do Windows"""
        try:
            if self._winsound_available:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                return True
        except:
            pass
        return False

    # ========== Toast Notifications ==========

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

    # ========== Polling de Notificações ==========

    def iniciar_polling(self, matricula: int, callback: Callable[[List[Notificacao]], None] = None, intervalo: int = 30):
        """
        Inicia thread de polling para buscar notificações.

        Args:
            matricula: Matrícula do usuário logado
            callback: Função chamada quando houver notificações (recebe lista)
            intervalo: Intervalo em segundos entre verificações
        """
        if self._polling_active:
            logger.warning("Polling já está ativo")
            return

        self._matricula = matricula
        self._callback = callback
        self._intervalo_polling = intervalo
        self._polling_active = True

        self._polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._polling_thread.start()
        logger.info(f"Polling de notificações iniciado (intervalo: {intervalo}s)")

    def parar_polling(self):
        """Para a thread de polling"""
        self._polling_active = False
        if self._polling_thread:
            self._polling_thread = None
        logger.info("Polling de notificações parado")

    def _polling_loop(self):
        """Loop de polling executado em thread separada"""
        while self._polling_active:
            try:
                notificacoes = self._buscar_notificacoes_pendentes()

                if notificacoes:
                    logger.info(f"{len(notificacoes)} notificação(ões) pendente(s)")

                    # Processar cada notificação
                    for notif in notificacoes:
                        self._processar_notificacao(notif)

                    # Callback para atualizar UI
                    if self._callback:
                        try:
                            self._callback(notificacoes)
                        except Exception as e:
                            logger.error(f"Erro no callback de notificação: {e}")

            except Exception as e:
                logger.error(f"Erro no polling de notificações: {e}")

            # Aguardar próximo ciclo
            time.sleep(self._intervalo_polling)

    def _buscar_notificacoes_pendentes(self) -> List[Notificacao]:
        """Busca notificações não lidas do banco"""
        from config.database import get_connection

        notificacoes = []
        conn = None

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT ID, ID_CHAMADO, TIPO, TITULO, MENSAGEM, DATAHORA
                FROM PCS_CHAMADOS_TI_NOTIF
                WHERE MATRICULA_DESTINO = :mat AND LIDA = 'N'
                ORDER BY DATAHORA DESC
            """, {"mat": self._matricula})

            rows = cur.fetchall()

            for row in rows:
                notificacoes.append(Notificacao(
                    id=row[0],
                    id_chamado=row[1],
                    tipo=row[2],
                    titulo=row[3],
                    mensagem=row[4] or "",
                    datahora=row[5]
                ))

            # Marcar como lidas
            if notificacoes:
                ids = [n.id for n in notificacoes]
                placeholders = ','.join([f':id{i}' for i in range(len(ids))])
                params = {f'id{i}': id for i, id in enumerate(ids)}

                cur.execute(f"""
                    UPDATE PCS_CHAMADOS_TI_NOTIF
                    SET LIDA = 'S', DATA_LEITURA = SYSDATE
                    WHERE ID IN ({placeholders})
                """, params)
                conn.commit()

            cur.close()

        except Exception as e:
            logger.error(f"Erro ao buscar notificações: {e}")
        finally:
            if conn:
                conn.close()

        return notificacoes

    def _processar_notificacao(self, notif: Notificacao):
        """Processa uma notificação (som + toast)"""
        # Tocar som baseado no tipo
        if notif.tipo == 'NOVO_CHAMADO':
            self.play_new_chamado()
        elif notif.tipo in ['RESPOSTA_ANALISTA', 'RESPOSTA_USUARIO']:
            self.play_resposta()
        elif notif.tipo == 'SLA_CRITICO':
            self.play_alerta()
        else:
            self._beep_default()

        # Mostrar toast notification
        self.show_notification(
            title=notif.titulo,
            message=notif.mensagem,
            timeout=8
        )

    def buscar_contagem_pendentes(self) -> int:
        """Busca quantidade de notificações não lidas (para badge)"""
        from config.database import get_connection

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT COUNT(*) FROM PCS_CHAMADOS_TI_NOTIF
                WHERE MATRICULA_DESTINO = :mat AND LIDA = 'N'
            """, {"mat": self._matricula})

            count = cur.fetchone()[0]
            cur.close()
            return count

        except Exception as e:
            logger.error(f"Erro ao contar notificações: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    # ========== Métodos de conveniência ==========

    def notify_new_chamado(self, id_chamado: int, categoria: str) -> bool:
        """Notifica novo chamado (chamado manualmente se necessário)"""
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
            title="⚠️ SLA Crítico!",
            message=f"Chamado #{id_chamado} - Tempo restante: {tempo_restante}"
        )


# Instância global
notification_service = NotificationService()
