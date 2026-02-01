# -*- coding: utf-8 -*-
"""
Barra de Status - Indicador de conexão e informações
"""
import customtkinter as ctk
from typing import Callable, Optional


class StatusBar(ctk.CTkFrame):
    """Barra de status com indicador de conexão e auto-refresh"""

    def __init__(
        self,
        master,
        usuario: str = "",
        on_refresh: Callable = None,
        **kwargs
    ):
        super().__init__(master, height=30, **kwargs)

        self.on_refresh = on_refresh
        self._auto_refresh_job = None
        self._refresh_interval = 0

        # Configuração do layout
        self.grid_columnconfigure(2, weight=1)

        # Indicador de conexão
        self.connection_indicator = ctk.CTkLabel(
            self,
            text="●",
            font=("Segoe UI", 14),
            text_color="#22c55e",
            width=20
        )
        self.connection_indicator.grid(row=0, column=0, padx=(10, 2), pady=5)

        self.connection_label = ctk.CTkLabel(
            self,
            text="Conectado",
            font=("Segoe UI", 10),
            text_color="#64748b"
        )
        self.connection_label.grid(row=0, column=1, padx=(0, 15), pady=5)

        # Usuário logado
        self.user_label = ctk.CTkLabel(
            self,
            text=f"Usuário: {usuario}",
            font=("Segoe UI", 10),
            text_color="#64748b"
        )
        self.user_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # Auto-refresh status
        self.refresh_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 10),
            text_color="#64748b"
        )
        self.refresh_label.grid(row=0, column=3, padx=10, pady=5)

        # Última atualização
        self.last_update_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 10),
            text_color="#94a3b8"
        )
        self.last_update_label.grid(row=0, column=4, padx=(10, 15), pady=5)

    def set_connected(self, connected: bool = True):
        """Atualiza indicador de conexão"""
        if connected:
            self.connection_indicator.configure(text_color="#22c55e")
            self.connection_label.configure(text="Conectado")
        else:
            self.connection_indicator.configure(text_color="#ef4444")
            self.connection_label.configure(text="Desconectado")

    def set_user(self, nome: str):
        """Atualiza nome do usuário"""
        self.user_label.configure(text=f"Usuário: {nome}")

    def set_last_update(self, timestamp: str):
        """Atualiza timestamp da última atualização"""
        self.last_update_label.configure(text=f"Última atualização: {timestamp}")

    def set_auto_refresh(self, interval_seconds: int):
        """Configura auto-refresh"""
        self._refresh_interval = interval_seconds

        # Cancela job anterior
        if self._auto_refresh_job:
            self.after_cancel(self._auto_refresh_job)
            self._auto_refresh_job = None

        if interval_seconds > 0:
            self.refresh_label.configure(
                text=f"Auto-refresh: {interval_seconds}s"
            )
            self._schedule_refresh()
        else:
            self.refresh_label.configure(text="Auto-refresh: Off")

    def _schedule_refresh(self):
        """Agenda próximo refresh"""
        if self._refresh_interval > 0 and self.on_refresh:
            self._auto_refresh_job = self.after(
                self._refresh_interval * 1000,
                self._do_refresh
            )

    def _do_refresh(self):
        """Executa refresh"""
        if self.on_refresh:
            try:
                self.on_refresh()
            except Exception:
                pass
        self._schedule_refresh()

    def stop_auto_refresh(self):
        """Para o auto-refresh"""
        if self._auto_refresh_job:
            self.after_cancel(self._auto_refresh_job)
            self._auto_refresh_job = None
