# -*- coding: utf-8 -*-
"""
Treeview customizado para chamados com cores SLA
"""
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
from datetime import datetime
from services.sla_service import SLAService
from config.settings import settings


class ChamadoTreeview(ttk.Treeview):
    """Treeview com suporte a cores de SLA"""

    def __init__(
        self,
        master,
        columns: List[str],
        column_widths: dict = None,
        on_select: Callable = None,
        on_double_click: Callable = None,
        show_user_info: bool = False,
        **kwargs
    ):
        """
        Args:
            master: Widget pai
            columns: Lista de nomes de colunas
            column_widths: Dict com largura de cada coluna
            on_select: Callback ao selecionar item
            on_double_click: Callback ao duplo clique
            show_user_info: Se True, exibe colunas de usuário/setor
        """
        super().__init__(master, columns=columns, show='headings', **kwargs)

        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        self.show_user_info = show_user_info
        self._chamados_map = {}  # id -> dados do chamado

        # Configurar colunas
        default_widths = {
            'ID': 60,
            'Data': 130,
            'Usuário': 120,
            'Setor': 100,
            'Categoria': 100,
            'Prioridade': 80,
            'Status': 100,
            'SLA': 120,
            'Descrição': 200
        }

        widths = column_widths or default_widths

        for col in columns:
            width = widths.get(col, 100)
            self.heading(col, text=col, anchor='w')
            self.column(col, width=width, minwidth=50, anchor='w')

        # Configurar tags de cores
        self._setup_tags()

        # Bind eventos
        self.bind('<<TreeviewSelect>>', self._on_select)
        self.bind('<Double-1>', self._on_double_click)

        # Scrollbar
        self._setup_scrollbar(master)

    def _setup_tags(self):
        """Configura tags para cores de SLA"""
        self.tag_configure('sla_ok', background='#dcfce7')  # Verde claro
        self.tag_configure('sla_atencao', background='#fef3c7')  # Amarelo claro
        self.tag_configure('sla_atrasado', background='#fee2e2')  # Vermelho claro
        self.tag_configure('sla_finalizado', background='#f3f4f6')  # Cinza claro
        self.tag_configure('sla_sem', background='#ffffff')  # Branco

        # Linhas alternadas
        self.tag_configure('even', background='#f8fafc')
        self.tag_configure('odd', background='#ffffff')

    def _setup_scrollbar(self, master):
        """Adiciona scrollbar vertical"""
        scrollbar = ttk.Scrollbar(master, orient='vertical', command=self.yview)
        self.configure(yscrollcommand=scrollbar.set)

        # Posicionar scrollbar (assumindo grid)
        try:
            scrollbar.grid(row=0, column=1, sticky='ns')
        except Exception:
            pass

    def _on_select(self, event):
        """Handler de seleção"""
        if self.on_select_callback:
            selected = self.selection()
            if selected:
                item_id = selected[0]
                chamado_id = self._chamados_map.get(item_id)
                self.on_select_callback(chamado_id)

    def _on_double_click(self, event):
        """Handler de duplo clique"""
        if self.on_double_click_callback:
            selected = self.selection()
            if selected:
                item_id = selected[0]
                chamado_id = self._chamados_map.get(item_id)
                self.on_double_click_callback(chamado_id)

    def carregar_chamados(self, chamados: list):
        """
        Carrega lista de chamados na treeview.

        Args:
            chamados: Lista de objetos Chamado ou tuplas
        """
        # Limpar itens existentes
        for item in self.get_children():
            self.delete(item)
        self._chamados_map.clear()

        # Adicionar novos itens
        for idx, chamado in enumerate(chamados):
            self._add_chamado(chamado, idx)

    def _add_chamado(self, chamado, idx: int):
        """Adiciona um chamado à treeview"""
        # Determinar valores das colunas
        if hasattr(chamado, 'id'):
            # Objeto Chamado
            chamado_id = chamado.id
            data = chamado.data_abertura.strftime('%d/%m/%Y %H:%M') if chamado.data_abertura else ''

            if self.show_user_info:
                values = (
                    chamado.id,
                    data,
                    chamado.nome_usuario or '',
                    chamado.setor or '',
                    chamado.categoria or '',
                    chamado.prioridade or '',
                    chamado.status or '',
                    self._format_sla(chamado),
                )
            else:
                values = (
                    chamado.id,
                    data,
                    chamado.categoria or '',
                    chamado.prioridade or '',
                    chamado.status or '',
                    self._format_sla(chamado),
                )

            # Determinar tag de cor
            sla_info = SLAService.analisar_chamado(chamado)
            tag = self._get_sla_tag(sla_info['status'])

        else:
            # Tupla (formato legado)
            chamado_id = chamado[0]
            values = chamado
            tag = 'sla_sem'

        # Adicionar linha
        item_id = self.insert('', 'end', values=values, tags=(tag,))
        self._chamados_map[item_id] = chamado_id

    def _format_sla(self, chamado) -> str:
        """Formata informação de SLA para exibição"""
        sla_info = SLAService.analisar_chamado(chamado)
        return sla_info['descricao']

    def _get_sla_tag(self, status: str) -> str:
        """Retorna tag de cor baseada no status do SLA"""
        tags = {
            'NO_PRAZO': 'sla_ok',
            'ATENCAO': 'sla_atencao',
            'ATRASADO': 'sla_atrasado',
            'FINALIZADO': 'sla_finalizado',
            'SEM_SLA': 'sla_sem'
        }
        return tags.get(status, 'sla_sem')

    def get_selected_id(self) -> Optional[int]:
        """Retorna ID do chamado selecionado"""
        selected = self.selection()
        if selected:
            return self._chamados_map.get(selected[0])
        return None

    def refresh(self):
        """Atualiza visual da treeview"""
        self.update_idletasks()


class FilterableTreeview(ChamadoTreeview):
    """Treeview com suporte a filtros"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._all_chamados = []
        self._filters = {}

    def carregar_chamados(self, chamados: list):
        """Carrega chamados e guarda cópia para filtros"""
        self._all_chamados = chamados.copy()
        self._apply_filters()

    def set_filter(self, field: str, value):
        """Define um filtro"""
        if value and value not in ('Todos', 'Todas', ''):
            self._filters[field] = value
        elif field in self._filters:
            del self._filters[field]
        self._apply_filters()

    def clear_filters(self):
        """Remove todos os filtros"""
        self._filters.clear()
        self._apply_filters()

    def _apply_filters(self):
        """Aplica filtros e atualiza exibição"""
        filtered = self._all_chamados

        for field, value in self._filters.items():
            filtered = [
                c for c in filtered
                if self._match_filter(c, field, value)
            ]

        super().carregar_chamados(filtered)

    def _match_filter(self, chamado, field: str, value) -> bool:
        """Verifica se chamado corresponde ao filtro"""
        if hasattr(chamado, field):
            return getattr(chamado, field) == value
        return True
