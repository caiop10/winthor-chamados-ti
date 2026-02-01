# -*- coding: utf-8 -*-
"""
Aplicação Principal - Chamados TI
Versão refatorada com arquitetura modular
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, timedelta
import shutil

import customtkinter as ctk
from tkcalendar import DateEntry

from config.settings import settings
from config.database import db_pool
from services.chamado_service import ChamadoService
from services.sla_service import SLAService
from services.notification_service import notification_service
from utils.logger import logger, audit_logger
from utils.helpers import format_datetime


class App(ctk.CTk):
    """Aplicação principal do sistema de chamados"""

    VERSION = "6.0"

    def __init__(self, usuario_wt: str = None, senha_bd: str = None,
                 alias_bd: str = None, usuario_bd: str = None, cod_rotina: str = None):
        super().__init__()

        # Parâmetros de inicialização
        self.usuario_wt = usuario_wt
        self.senha_bd = senha_bd
        self.alias_bd = alias_bd
        self.usuario_bd = usuario_bd
        self.cod_rotina = cod_rotina

        # Estado do usuário
        self.usuario = None
        self.matricula_logada = None
        self.nome_logado = None
        self.codsetor_logado = None

        # Cache
        self._dados_ti_cache = []
        self._rede_conectada_ate = 0

        # Widgets globais (serão criados no setup)
        self.notebook = None
        self.status_bar = None

        # Configurar aparência
        ctk.set_appearance_mode("light")

        # Configuração da janela
        self.title(f"Chamados TI - SOTRIGO v{self.VERSION}")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        # Inicializar
        self._initialize()

    def _initialize(self):
        """Inicializa o sistema"""
        try:
            # Inicializar pool de conexões
            db_pool.initialize()
            logger.info("Pool de conexões inicializado")

            # Carregar dados do usuário
            if self.usuario_wt:
                self.usuario = ChamadoService.carregar_usuario(
                    self.usuario_wt,
                    self.usuario_bd
                )

                if self.usuario:
                    self.matricula_logada = self.usuario.matricula
                    self.nome_logado = self.usuario.nome
                    self.codsetor_logado = self.usuario.codsetor
                    logger.info(f"Usuário logado: {self.nome_logado} ({self.matricula_logada})")
                else:
                    messagebox.showerror("Erro", f"Usuário não encontrado: {self.usuario_wt}")
                    self.destroy()
                    return
            else:
                messagebox.showerror("Erro", "USUARIOWT não foi recebido.")
                self.destroy()
                return

            # Criar interface
            self._setup_ui()

            # Configurar atalhos de teclado
            self._setup_keybindings()

            # Configurar auto-refresh
            if settings.AUTO_REFRESH_INTERVAL > 0:
                self.after(
                    settings.AUTO_REFRESH_INTERVAL * 1000,
                    self._auto_refresh
                )

        except Exception as e:
            logger.error(f"Erro na inicialização: {e}")
            messagebox.showerror("Erro", f"Erro ao inicializar: {e}")
            self.destroy()

    def _setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Header com informações do usuário
        self._setup_header()

        # Notebook com abas
        self._setup_notebook()

        # Status bar
        self._setup_status_bar()

    def _setup_header(self):
        """Configura cabeçalho"""
        header = ctk.CTkFrame(self.main_frame, height=50)
        header.pack(fill='x', pady=(0, 10))

        # Logo/Título
        ctk.CTkLabel(
            header,
            text="SOTRIGO - Sistema de Chamados TI",
            font=("Segoe UI", 18, "bold"),
            text_color="#1e40af"
        ).pack(side='left', padx=20, pady=10)

        # Info usuário
        ctk.CTkLabel(
            header,
            text=f"Olá, {self.nome_logado}",
            font=("Segoe UI", 12),
            text_color="#64748b"
        ).pack(side='right', padx=20, pady=10)

    def _setup_notebook(self):
        """Configura notebook com abas"""
        self.notebook = ctk.CTkTabview(self.main_frame)
        self.notebook.pack(fill='both', expand=True)

        # Abas
        self.notebook.add("Meus Chamados")
        self.notebook.add("Novo Chamado")

        # Aba TI (apenas para usuários TI)
        if self._is_ti():
            self.notebook.add("Painel TI")

        # Aba Gerência (apenas para gerência)
        if self._is_gerencia():
            self.notebook.add("Painel Gerência")

        # Configurar conteúdo das abas
        self._setup_tab_meus_chamados()
        self._setup_tab_novo_chamado()

        if self._is_ti():
            self._setup_tab_painel_ti()

        if self._is_gerencia():
            self._setup_tab_painel_gerencia()

    def _setup_status_bar(self):
        """Configura barra de status"""
        self.status_bar = ctk.CTkFrame(self.main_frame, height=30)
        self.status_bar.pack(fill='x', pady=(10, 0))

        # Indicador de conexão
        self.conn_indicator = ctk.CTkLabel(
            self.status_bar,
            text="● Conectado",
            font=("Segoe UI", 10),
            text_color="#22c55e"
        )
        self.conn_indicator.pack(side='left', padx=10)

        # Info refresh
        self.refresh_label = ctk.CTkLabel(
            self.status_bar,
            text=f"Auto-refresh: {settings.AUTO_REFRESH_INTERVAL}s" if settings.AUTO_REFRESH_INTERVAL > 0 else "Auto-refresh: Off",
            font=("Segoe UI", 10),
            text_color="#64748b"
        )
        self.refresh_label.pack(side='left', padx=20)

        # Última atualização
        self.last_update = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=("Segoe UI", 10),
            text_color="#94a3b8"
        )
        self.last_update.pack(side='right', padx=10)

    def _setup_tab_meus_chamados(self):
        """Configura aba Meus Chamados"""
        tab = self.notebook.tab("Meus Chamados")

        # Frame de filtros
        filtros_frame = ctk.CTkFrame(tab)
        filtros_frame.pack(fill='x', pady=(0, 10))

        ctk.CTkLabel(filtros_frame, text="Período:").pack(side='left', padx=5)

        # Data início
        self.date_ini_meus = DateEntry(
            filtros_frame,
            width=12,
            date_pattern='dd/mm/yyyy'
        )
        self.date_ini_meus.set_date(datetime.now() - timedelta(days=30))
        self.date_ini_meus.pack(side='left', padx=5)

        ctk.CTkLabel(filtros_frame, text="até").pack(side='left', padx=5)

        self.date_fim_meus = DateEntry(
            filtros_frame,
            width=12,
            date_pattern='dd/mm/yyyy'
        )
        self.date_fim_meus.pack(side='left', padx=5)

        ctk.CTkLabel(filtros_frame, text="Status:").pack(side='left', padx=(20, 5))

        self.combo_status_meus = ctk.CTkComboBox(
            filtros_frame,
            values=settings.LISTA_STATUS,
            width=120
        )
        self.combo_status_meus.set("Todos")
        self.combo_status_meus.pack(side='left', padx=5)

        ctk.CTkButton(
            filtros_frame,
            text="Buscar",
            command=self._carregar_meus_chamados,
            width=100
        ).pack(side='left', padx=20)

        # Treeview
        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill='both', expand=True)

        columns = ('ID', 'Data', 'Categoria', 'Prioridade', 'Status', 'SLA')

        self.tree_meus = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=15
        )

        for col in columns:
            self.tree_meus.heading(col, text=col)
            self.tree_meus.column(col, width=100)

        self.tree_meus.column('ID', width=60)
        self.tree_meus.column('Data', width=130)
        self.tree_meus.column('SLA', width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_meus.yview)
        self.tree_meus.configure(yscrollcommand=scrollbar.set)

        self.tree_meus.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree_meus.bind('<<TreeviewSelect>>', self._on_select_meus)

        # Configurar tags de cores
        self.tree_meus.tag_configure('sla_ok', background='#dcfce7')
        self.tree_meus.tag_configure('sla_atencao', background='#fef3c7')
        self.tree_meus.tag_configure('sla_atrasado', background='#fee2e2')
        self.tree_meus.tag_configure('sla_finalizado', background='#f3f4f6')

        # Frame de detalhes
        detalhes_frame = ctk.CTkFrame(tab)
        detalhes_frame.pack(fill='x', pady=(10, 0))

        ctk.CTkLabel(
            detalhes_frame,
            text="Histórico:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor='w', padx=10, pady=5)

        self.txt_hist_meus = ctk.CTkTextbox(detalhes_frame, height=150)
        self.txt_hist_meus.pack(fill='x', padx=10, pady=5)

        # Botões de ação
        btn_frame = ctk.CTkFrame(detalhes_frame)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Responder",
            command=self._responder_meus
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Finalizar",
            command=self._finalizar_meus
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Ver Anexos",
            command=self._ver_anexos_meus
        ).pack(side='left', padx=5)

    def _setup_tab_novo_chamado(self):
        """Configura aba Novo Chamado"""
        tab = self.notebook.tab("Novo Chamado")

        # Frame central
        form_frame = ctk.CTkFrame(tab)
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Categoria
        ctk.CTkLabel(
            form_frame,
            text="Categoria:",
            font=("Segoe UI", 12)
        ).pack(anchor='w', pady=(10, 5))

        self.combo_categoria = ctk.CTkComboBox(
            form_frame,
            values=settings.LISTA_CATEGORIA_ABERTURA,
            width=300
        )
        self.combo_categoria.set(settings.LISTA_CATEGORIA_ABERTURA[0])
        self.combo_categoria.pack(anchor='w')

        # Prioridade
        ctk.CTkLabel(
            form_frame,
            text="Prioridade:",
            font=("Segoe UI", 12)
        ).pack(anchor='w', pady=(20, 5))

        self.combo_prioridade = ctk.CTkComboBox(
            form_frame,
            values=["BAIXA", "MEDIA", "ALTA"],
            width=300
        )
        self.combo_prioridade.set("MEDIA")
        self.combo_prioridade.pack(anchor='w')

        # Descrição
        ctk.CTkLabel(
            form_frame,
            text="Descrição do problema:",
            font=("Segoe UI", 12)
        ).pack(anchor='w', pady=(20, 5))

        self.text_descricao = ctk.CTkTextbox(form_frame, height=200)
        self.text_descricao.pack(fill='x', pady=5)

        # Anexo
        anexo_frame = ctk.CTkFrame(form_frame)
        anexo_frame.pack(fill='x', pady=20)

        ctk.CTkButton(
            anexo_frame,
            text="Anexar Arquivo",
            command=self._selecionar_anexo
        ).pack(side='left')

        self.lbl_anexo = ctk.CTkLabel(
            anexo_frame,
            text="Nenhum arquivo selecionado",
            text_color="#64748b"
        )
        self.lbl_anexo.pack(side='left', padx=10)

        self._anexo_path = None

        # Botão enviar
        ctk.CTkButton(
            form_frame,
            text="Abrir Chamado",
            command=self._abrir_chamado,
            width=200,
            height=40,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

    def _setup_tab_painel_ti(self):
        """Configura aba Painel TI"""
        tab = self.notebook.tab("Painel TI")

        # Frame de filtros
        filtros_frame = ctk.CTkFrame(tab)
        filtros_frame.pack(fill='x', pady=(0, 10))

        ctk.CTkLabel(filtros_frame, text="Status:").pack(side='left', padx=5)
        self.combo_filtro_status = ctk.CTkComboBox(
            filtros_frame,
            values=settings.LISTA_STATUS,
            width=120,
            command=self._filtrar_ti
        )
        self.combo_filtro_status.set("Todos")
        self.combo_filtro_status.pack(side='left', padx=5)

        ctk.CTkLabel(filtros_frame, text="Prioridade:").pack(side='left', padx=5)
        self.combo_filtro_prioridade = ctk.CTkComboBox(
            filtros_frame,
            values=settings.LISTA_PRIORIDADE,
            width=100,
            command=self._filtrar_ti
        )
        self.combo_filtro_prioridade.set("Todas")
        self.combo_filtro_prioridade.pack(side='left', padx=5)

        ctk.CTkLabel(filtros_frame, text="Categoria:").pack(side='left', padx=5)
        self.combo_filtro_categoria = ctk.CTkComboBox(
            filtros_frame,
            values=settings.LISTA_CATEGORIA,
            width=120,
            command=self._filtrar_ti
        )
        self.combo_filtro_categoria.set("Todas")
        self.combo_filtro_categoria.pack(side='left', padx=5)

        ctk.CTkButton(
            filtros_frame,
            text="Atualizar (F5)",
            command=self._carregar_chamados_ti
        ).pack(side='right', padx=10)

        self.lbl_contador_ti = ctk.CTkLabel(
            filtros_frame,
            text="0 chamados",
            font=("Segoe UI", 11, "bold")
        )
        self.lbl_contador_ti.pack(side='right', padx=10)

        # Treeview
        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill='both', expand=True)

        columns = ('ID', 'Data', 'Usuário', 'Setor', 'Categoria', 'Prioridade', 'Status', 'SLA')

        self.tree_ti = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=15
        )

        for col in columns:
            self.tree_ti.heading(col, text=col)
            self.tree_ti.column(col, width=100)

        self.tree_ti.column('ID', width=60)
        self.tree_ti.column('Data', width=130)
        self.tree_ti.column('SLA', width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_ti.yview)
        self.tree_ti.configure(yscrollcommand=scrollbar.set)

        self.tree_ti.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree_ti.bind('<<TreeviewSelect>>', self._on_select_ti)
        self.tree_ti.bind('<Double-1>', self._on_double_click_ti)

        # Tags de cores
        self.tree_ti.tag_configure('sla_ok', background='#dcfce7')
        self.tree_ti.tag_configure('sla_atencao', background='#fef3c7')
        self.tree_ti.tag_configure('sla_atrasado', background='#fee2e2')
        self.tree_ti.tag_configure('sla_finalizado', background='#f3f4f6')

        # Frame de detalhes
        detalhes_frame = ctk.CTkFrame(tab)
        detalhes_frame.pack(fill='x', pady=(10, 0))

        ctk.CTkLabel(
            detalhes_frame,
            text="Histórico:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor='w', padx=10, pady=5)

        self.txt_hist_ti = ctk.CTkTextbox(detalhes_frame, height=120)
        self.txt_hist_ti.pack(fill='x', padx=10, pady=5)

        # Botões de ação
        btn_frame = ctk.CTkFrame(detalhes_frame)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Assumir",
            command=self._assumir_chamado
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Responder",
            command=self._responder_ti
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Mover Categoria",
            command=self._mover_categoria
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Alterar Prioridade",
            command=self._mover_prioridade
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Ver Anexos",
            command=self._ver_anexos_ti
        ).pack(side='left', padx=5)

        # Carregar dados
        self.after(100, self._carregar_chamados_ti)

    def _create_kpi_card(self, parent, icon, title, key, color="#3b82f6", width=140):
        """Cria um card KPI estilizado"""
        card = ctk.CTkFrame(parent, width=width, height=90, corner_radius=10)
        card.pack_propagate(False)

        # Header com ícone
        header = ctk.CTkFrame(card, fg_color="transparent", height=25)
        header.pack(fill='x', padx=10, pady=(8, 0))

        ctk.CTkLabel(
            header,
            text=icon,
            font=("Segoe UI", 16),
            text_color=color
        ).pack(side='left')

        ctk.CTkLabel(
            header,
            text=title,
            font=("Segoe UI", 10),
            text_color="#64748b"
        ).pack(side='left', padx=5)

        # Valor principal
        self.kpi_labels[key] = ctk.CTkLabel(
            card,
            text="0",
            font=("Segoe UI", 28, "bold"),
            text_color=color
        )
        self.kpi_labels[key].pack(pady=(5, 0))

        # Subtítulo
        self.kpi_subtitles[key] = ctk.CTkLabel(
            card,
            text="",
            font=("Segoe UI", 9),
            text_color="#94a3b8"
        )
        self.kpi_subtitles[key].pack()

        return card

    def _setup_tab_painel_gerencia(self):
        """Configura aba Painel Gerência"""
        tab = self.notebook.tab("Painel Gerência")

        # Scrollable frame para todo conteúdo
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill='both', expand=True)

        # ===== HEADER COM FILTROS =====
        header_frame = ctk.CTkFrame(scroll_frame, fg_color="#1e40af", corner_radius=10)
        header_frame.pack(fill='x', pady=(0, 15), padx=5)

        ctk.CTkLabel(
            header_frame,
            text="Dashboard de Chamados TI",
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        ).pack(side='left', padx=15, pady=10)

        # Filtros à direita
        filtros_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        filtros_inner.pack(side='right', padx=15, pady=10)

        ctk.CTkLabel(filtros_inner, text="Período:", text_color="white").pack(side='left', padx=5)

        self.date_ini_gerencia = DateEntry(
            filtros_inner,
            width=10,
            date_pattern='dd/mm/yyyy',
            background='#1e40af',
            foreground='white'
        )
        self.date_ini_gerencia.set_date(datetime.now() - timedelta(days=30))
        self.date_ini_gerencia.pack(side='left', padx=3)

        ctk.CTkLabel(filtros_inner, text="a", text_color="white").pack(side='left', padx=3)

        self.date_fim_gerencia = DateEntry(
            filtros_inner,
            width=10,
            date_pattern='dd/mm/yyyy'
        )
        self.date_fim_gerencia.pack(side='left', padx=3)

        ctk.CTkButton(
            filtros_inner,
            text="Atualizar",
            command=self._carregar_dashboard,
            width=90,
            height=28,
            fg_color="#22c55e",
            hover_color="#16a34a"
        ).pack(side='left', padx=10)

        # ===== KPIs LINHA 1 - VOLUME =====
        self.kpi_labels = {}
        self.kpi_subtitles = {}

        kpis_row1 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        kpis_row1.pack(fill='x', pady=5, padx=5)

        # Novos Hoje
        self._create_kpi_card(kpis_row1, "📥", "Novos Hoje", "novos_hoje", "#3b82f6").pack(side='left', padx=5, expand=True)

        # Total no Período
        self._create_kpi_card(kpis_row1, "📊", "Total Período", "total", "#6366f1").pack(side='left', padx=5, expand=True)

        # Em Aberto
        self._create_kpi_card(kpis_row1, "📂", "Em Aberto", "abertos", "#f59e0b").pack(side='left', padx=5, expand=True)

        # Finalizados
        self._create_kpi_card(kpis_row1, "✅", "Finalizados", "finalizados", "#22c55e").pack(side='left', padx=5, expand=True)

        # ===== KPIs LINHA 2 - PERFORMANCE =====
        kpis_row2 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        kpis_row2.pack(fill='x', pady=5, padx=5)

        # Atrasados (SLA)
        self._create_kpi_card(kpis_row2, "⚠️", "Atrasados", "atrasados", "#ef4444").pack(side='left', padx=5, expand=True)

        # Sem Analista
        self._create_kpi_card(kpis_row2, "👤", "Sem Analista", "sem_analista", "#f97316").pack(side='left', padx=5, expand=True)

        # Tempo Médio
        self._create_kpi_card(kpis_row2, "⏱️", "Tempo Médio", "tempo_medio", "#8b5cf6").pack(side='left', padx=5, expand=True)

        # SLA Cumprido
        self._create_kpi_card(kpis_row2, "🎯", "SLA Cumprido", "sla_percent", "#10b981").pack(side='left', padx=5, expand=True)

        # ===== TABELAS =====
        tabelas_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        tabelas_frame.pack(fill='both', expand=True, pady=10, padx=5)
        tabelas_frame.grid_columnconfigure(0, weight=1)
        tabelas_frame.grid_columnconfigure(1, weight=1)

        # ----- Top 10 Usuários -----
        frame_usuarios = ctk.CTkFrame(tabelas_frame, corner_radius=10)
        frame_usuarios.grid(row=0, column=0, sticky='nsew', padx=(0, 5), pady=5)

        header_usuarios = ctk.CTkFrame(frame_usuarios, fg_color="#f59e0b", corner_radius=8, height=35)
        header_usuarios.pack(fill='x', padx=5, pady=5)
        header_usuarios.pack_propagate(False)
        ctk.CTkLabel(
            header_usuarios,
            text="🏆 Top 10 Usuários (mais chamados)",
            font=("Segoe UI", 11, "bold"),
            text_color="white"
        ).pack(side='left', padx=10, pady=5)

        columns_usuarios = ('Usuário', 'Total', 'Abertos', 'Finalizados')
        self.tree_usuarios = ttk.Treeview(frame_usuarios, columns=columns_usuarios, show='headings', height=6)
        for col in columns_usuarios:
            self.tree_usuarios.heading(col, text=col)
            self.tree_usuarios.column(col, width=70, anchor='center')
        self.tree_usuarios.column('Usuário', width=140, anchor='w')
        self.tree_usuarios.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # ----- Por Categoria -----
        frame_categoria = ctk.CTkFrame(tabelas_frame, corner_radius=10)
        frame_categoria.grid(row=0, column=1, sticky='nsew', padx=(5, 0), pady=5)

        header_cat = ctk.CTkFrame(frame_categoria, fg_color="#6366f1", corner_radius=8, height=35)
        header_cat.pack(fill='x', padx=5, pady=5)
        header_cat.pack_propagate(False)
        ctk.CTkLabel(
            header_cat,
            text="📁 Por Categoria",
            font=("Segoe UI", 11, "bold"),
            text_color="white"
        ).pack(side='left', padx=10, pady=5)

        columns_cat = ('Categoria', 'Total', 'Abertos', 'Finalizados')
        self.tree_categoria = ttk.Treeview(frame_categoria, columns=columns_cat, show='headings', height=6)
        for col in columns_cat:
            self.tree_categoria.heading(col, text=col)
            self.tree_categoria.column(col, width=70, anchor='center')
        self.tree_categoria.column('Categoria', width=110, anchor='w')
        self.tree_categoria.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # ----- Por Status -----
        frame_status = ctk.CTkFrame(tabelas_frame, corner_radius=10)
        frame_status.grid(row=1, column=0, sticky='nsew', padx=(0, 5), pady=5)

        header_status = ctk.CTkFrame(frame_status, fg_color="#22c55e", corner_radius=8, height=35)
        header_status.pack(fill='x', padx=5, pady=5)
        header_status.pack_propagate(False)
        ctk.CTkLabel(
            header_status,
            text="📋 Por Status",
            font=("Segoe UI", 11, "bold"),
            text_color="white"
        ).pack(side='left', padx=10, pady=5)

        columns_status = ('Status', 'Quantidade', '%')
        self.tree_status = ttk.Treeview(frame_status, columns=columns_status, show='headings', height=5)
        for col in columns_status:
            self.tree_status.heading(col, text=col)
            self.tree_status.column(col, width=100, anchor='center')
        self.tree_status.column('Status', width=120, anchor='w')
        self.tree_status.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # ----- Por Analista -----
        frame_analista = ctk.CTkFrame(tabelas_frame, corner_radius=10)
        frame_analista.grid(row=1, column=1, sticky='nsew', padx=(5, 0), pady=5)

        header_analista = ctk.CTkFrame(frame_analista, fg_color="#ef4444", corner_radius=8, height=35)
        header_analista.pack(fill='x', padx=5, pady=5)
        header_analista.pack_propagate(False)
        ctk.CTkLabel(
            header_analista,
            text="👨‍💻 Por Analista TI",
            font=("Segoe UI", 11, "bold"),
            text_color="white"
        ).pack(side='left', padx=10, pady=5)

        columns_analista = ('Analista', 'Total', 'Abertos', 'Atrasados')
        self.tree_analista = ttk.Treeview(frame_analista, columns=columns_analista, show='headings', height=5)
        for col in columns_analista:
            self.tree_analista.heading(col, text=col)
            self.tree_analista.column(col, width=70, anchor='center')
        self.tree_analista.column('Analista', width=120, anchor='w')
        self.tree_analista.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Configurar cores alternadas nas treeviews
        for tree in [self.tree_usuarios, self.tree_categoria, self.tree_status, self.tree_analista]:
            tree.tag_configure('oddrow', background='#f8fafc')
            tree.tag_configure('evenrow', background='#ffffff')

        # Carregar dados
        self.after(200, self._carregar_dashboard)

    def _setup_keybindings(self):
        """Configura atalhos de teclado"""
        self.bind('<F5>', lambda e: self._refresh_current_tab())
        self.bind('<Control-n>', lambda e: self.notebook.set("Novo Chamado"))
        self.bind('<Escape>', lambda e: self.focus_set())

    # ========== Métodos auxiliares ==========

    def _is_ti(self) -> bool:
        """Verifica se usuário é TI"""
        return (self.codsetor_logado == 10) or (
            self.matricula_logada in settings.USUARIOS_TI if self.matricula_logada else False
        )

    def _is_gerencia(self) -> bool:
        """Verifica se usuário é gerência"""
        return self.matricula_logada in settings.USUARIOS_GERENCIA if self.matricula_logada else False

    def _get_selected_id_meus(self) -> int:
        """Retorna ID do chamado selecionado em Meus Chamados"""
        selected = self.tree_meus.selection()
        if selected:
            return int(self.tree_meus.item(selected[0])['values'][0])
        return None

    def _get_selected_id_ti(self) -> int:
        """Retorna ID do chamado selecionado no Painel TI"""
        selected = self.tree_ti.selection()
        if selected:
            return int(self.tree_ti.item(selected[0])['values'][0])
        return None

    def _update_last_update(self):
        """Atualiza timestamp da última atualização"""
        self.last_update.configure(
            text=f"Última atualização: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _auto_refresh(self):
        """Auto-refresh periódico"""
        self._refresh_current_tab()
        if settings.AUTO_REFRESH_INTERVAL > 0:
            self.after(
                settings.AUTO_REFRESH_INTERVAL * 1000,
                self._auto_refresh
            )

    def _refresh_current_tab(self):
        """Atualiza aba atual"""
        current = self.notebook.get()
        if current == "Meus Chamados":
            self._carregar_meus_chamados()
        elif current == "Painel TI":
            self._carregar_chamados_ti()
        elif current == "Painel Gerência":
            self._carregar_dashboard()

    # ========== Handlers Meus Chamados ==========

    def _carregar_meus_chamados(self):
        """Carrega chamados do usuário"""
        try:
            data_ini = datetime.combine(
                self.date_ini_meus.get_date(),
                datetime.min.time()
            )
            data_fim = datetime.combine(
                self.date_fim_meus.get_date(),
                datetime.min.time()
            )
            status = self.combo_status_meus.get()

            chamados = ChamadoService.listar_chamados_usuario(
                self.matricula_logada,
                data_inicio=data_ini,
                data_fim=data_fim,
                status=status if status != "Todos" else None
            )

            # Limpar treeview
            for item in self.tree_meus.get_children():
                self.tree_meus.delete(item)

            # Adicionar chamados
            for chamado in chamados:
                sla_info = SLAService.analisar_chamado(chamado)
                tag = self._get_sla_tag(sla_info['status'])

                self.tree_meus.insert('', 'end', values=(
                    chamado.id,
                    chamado.data_abertura.strftime('%d/%m/%Y %H:%M') if chamado.data_abertura else '',
                    chamado.categoria,
                    chamado.prioridade,
                    chamado.status,
                    sla_info['descricao']
                ), tags=(tag,))

            self._update_last_update()

        except Exception as e:
            logger.error(f"Erro ao carregar chamados: {e}")
            messagebox.showerror("Erro", str(e))

    def _on_select_meus(self, event):
        """Handler de seleção em Meus Chamados"""
        id_chamado = self._get_selected_id_meus()
        if id_chamado:
            self._carregar_historico_meus(id_chamado)

    def _carregar_historico_meus(self, id_chamado: int):
        """Carrega histórico do chamado com indicação de anexos"""
        historico = ChamadoService.buscar_historico(id_chamado)
        anexos = ChamadoService.buscar_anexos(id_chamado)

        self.txt_hist_meus.configure(state='normal')
        self.txt_hist_meus.delete('1.0', 'end')

        # Mostrar anexos no topo se houver
        if anexos:
            self.txt_hist_meus.insert('end', f"📎 {len(anexos)} ANEXO(S) - Clique em 'Ver Anexos' para visualizar\n")
            self.txt_hist_meus.insert('end', "─" * 50 + "\n\n")

        for item in historico:
            data = item.datahora.strftime('%d/%m/%Y %H:%M') if item.datahora else ''

            # Destacar anexos no histórico
            if item.tipo == 'ANEXO':
                self.txt_hist_meus.insert('end', f"[{data}] 📎 {item.tipo}\n{item.mensagem}\n\n")
            elif item.tipo == 'RESPOSTA_ANALISTA':
                self.txt_hist_meus.insert('end', f"[{data}] 👨‍💻 {item.tipo}\n{item.mensagem}\n\n")
            elif item.tipo == 'RESPOSTA_USUARIO':
                self.txt_hist_meus.insert('end', f"[{data}] 👤 {item.tipo}\n{item.mensagem}\n\n")
            else:
                self.txt_hist_meus.insert('end', f"[{data}] {item.tipo}\n{item.mensagem}\n\n")

        self.txt_hist_meus.configure(state='disabled')

        # Guardar ID do chamado selecionado para ver anexos
        self._chamado_selecionado_meus = id_chamado

    def _responder_meus(self):
        """Responde ao chamado selecionado com opção de anexo"""
        id_chamado = self._get_selected_id_meus()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        # Usar diálogo customizado com anexo
        from gui.dialogs.resposta_dialog import RespostaDialog
        dialog = RespostaDialog(self, titulo="Responder ao Analista")
        resultado = dialog.get_resultado()

        if resultado:
            resposta = resultado['resposta']
            anexo = resultado['anexo']

            # Enviar resposta
            if ChamadoService.resposta_usuario(id_chamado, self.matricula_logada, resposta, False):
                # Se houver anexo, copiar e registrar
                if anexo:
                    try:
                        destino = self._copiar_anexo(anexo, id_chamado)
                        ChamadoService.registrar_anexo_adicional(id_chamado, self.matricula_logada, destino)
                        messagebox.showinfo("Sucesso", "Resposta enviada com anexo!")
                    except Exception as e:
                        logger.warning(f"Erro ao copiar anexo: {e}")
                        messagebox.showinfo("Sucesso", "Resposta enviada! (Anexo não foi salvo)")
                else:
                    messagebox.showinfo("Sucesso", "Resposta enviada!")

                self._carregar_meus_chamados()
                self._carregar_historico_meus(id_chamado)
            else:
                messagebox.showerror("Erro", "Falha ao enviar resposta.")

    def _finalizar_meus(self):
        """Finaliza o chamado selecionado"""
        id_chamado = self._get_selected_id_meus()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        if messagebox.askyesno("Confirmar", "Deseja finalizar este chamado?"):
            if ChamadoService.resposta_usuario(id_chamado, self.matricula_logada, "Chamado finalizado pelo usuário.", True):
                messagebox.showinfo("Sucesso", "Chamado finalizado!")
                self._carregar_meus_chamados()
            else:
                messagebox.showerror("Erro", "Falha ao finalizar chamado.")

    def _ver_anexos_meus(self):
        """Abre diálogo com lista de anexos do chamado"""
        id_chamado = self._get_selected_id_meus()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        anexos = ChamadoService.buscar_anexos(id_chamado)

        if not anexos:
            messagebox.showinfo("Aviso", "Nenhum anexo encontrado neste chamado.")
            return

        # Usar diálogo customizado para listar anexos
        from gui.dialogs.resposta_dialog import HistoricoAnexosDialog
        HistoricoAnexosDialog(self, id_chamado, anexos)

    # ========== Handlers Novo Chamado ==========

    def _selecionar_anexo(self):
        """Seleciona arquivo para anexar"""
        path = filedialog.askopenfilename(
            title="Selecione um arquivo",
            filetypes=[
                ("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("PDF", "*.pdf"),
                ("Todos", "*.*")
            ]
        )
        if path:
            self._anexo_path = path
            self.lbl_anexo.configure(text=os.path.basename(path))

    def _abrir_chamado(self):
        """Abre novo chamado"""
        categoria = self.combo_categoria.get()
        prioridade = self.combo_prioridade.get()
        descricao = self.text_descricao.get('1.0', 'end').strip()

        if not descricao:
            messagebox.showwarning("Aviso", "Descreva o problema.")
            return

        try:
            # Copiar anexo se houver
            caminho_anexo = None
            if self._anexo_path:
                # Criar chamado primeiro para obter ID
                pass

            id_chamado = ChamadoService.abrir_chamado(
                self.matricula_logada,
                prioridade,
                categoria,
                descricao,
                None  # Anexo será adicionado depois
            )

            if id_chamado:
                # Copiar anexo se houver
                if self._anexo_path:
                    try:
                        destino = self._copiar_anexo(self._anexo_path, id_chamado)
                        ChamadoService.atualizar_anexo(id_chamado, self.matricula_logada, destino)
                    except Exception as e:
                        logger.warning(f"Erro ao copiar anexo: {e}")

                messagebox.showinfo("Sucesso", f"Chamado #{id_chamado} aberto com sucesso!")

                # Limpar formulário
                self.text_descricao.delete('1.0', 'end')
                self._anexo_path = None
                self.lbl_anexo.configure(text="Nenhum arquivo selecionado")

                # Ir para meus chamados
                self.notebook.set("Meus Chamados")
                self._carregar_meus_chamados()
            else:
                messagebox.showerror("Erro", "Falha ao abrir chamado.")

        except Exception as e:
            logger.error(f"Erro ao abrir chamado: {e}")
            messagebox.showerror("Erro", str(e))

    # ========== Handlers Painel TI ==========

    def _carregar_chamados_ti(self):
        """Carrega chamados para Painel TI"""
        try:
            chamados = ChamadoService.listar_chamados_ti(apenas_nao_finalizados=True)
            self._dados_ti_cache = chamados

            self._filtrar_ti()
            self._update_last_update()

        except Exception as e:
            logger.error(f"Erro ao carregar chamados TI: {e}")

    def _filtrar_ti(self, *args):
        """Aplica filtros no Painel TI"""
        status = self.combo_filtro_status.get()
        prioridade = self.combo_filtro_prioridade.get()
        categoria = self.combo_filtro_categoria.get()

        filtrados = self._dados_ti_cache

        if status != "Todos":
            filtrados = [c for c in filtrados if c.status == status]
        if prioridade != "Todas":
            filtrados = [c for c in filtrados if c.prioridade == prioridade]
        if categoria != "Todas":
            filtrados = [c for c in filtrados if c.categoria == categoria]

        # Limpar treeview
        for item in self.tree_ti.get_children():
            self.tree_ti.delete(item)

        # Adicionar chamados
        for chamado in filtrados:
            sla_info = SLAService.analisar_chamado(chamado)
            tag = self._get_sla_tag(sla_info['status'])

            self.tree_ti.insert('', 'end', values=(
                chamado.id,
                chamado.data_abertura.strftime('%d/%m/%Y %H:%M') if chamado.data_abertura else '',
                chamado.nome_usuario,
                chamado.setor,
                chamado.categoria,
                chamado.prioridade,
                chamado.status,
                sla_info['descricao']
            ), tags=(tag,))

        self.lbl_contador_ti.configure(text=f"{len(filtrados)} chamados")

    def _on_select_ti(self, event):
        """Handler de seleção no Painel TI"""
        id_chamado = self._get_selected_id_ti()
        if id_chamado:
            self._carregar_historico_ti(id_chamado)

    def _on_double_click_ti(self, event):
        """Handler de duplo clique no Painel TI"""
        id_chamado = self._get_selected_id_ti()
        if id_chamado:
            # Assumir chamado automaticamente
            self._assumir_chamado()

    def _carregar_historico_ti(self, id_chamado: int):
        """Carrega histórico do chamado com indicação de anexos"""
        historico = ChamadoService.buscar_historico(id_chamado)
        anexos = ChamadoService.buscar_anexos(id_chamado)

        self.txt_hist_ti.configure(state='normal')
        self.txt_hist_ti.delete('1.0', 'end')

        # Mostrar anexos no topo se houver
        if anexos:
            self.txt_hist_ti.insert('end', f"📎 {len(anexos)} ANEXO(S) - Clique em 'Ver Anexos' para visualizar\n")
            self.txt_hist_ti.insert('end', "─" * 50 + "\n\n")

        for item in historico:
            data = item.datahora.strftime('%d/%m/%Y %H:%M') if item.datahora else ''

            # Destacar tipos no histórico
            if item.tipo == 'ANEXO':
                self.txt_hist_ti.insert('end', f"[{data}] 📎 {item.tipo}\n{item.mensagem}\n\n")
            elif item.tipo == 'RESPOSTA_ANALISTA':
                self.txt_hist_ti.insert('end', f"[{data}] 👨‍💻 {item.tipo}\n{item.mensagem}\n\n")
            elif item.tipo == 'RESPOSTA_USUARIO':
                self.txt_hist_ti.insert('end', f"[{data}] 👤 {item.tipo}\n{item.mensagem}\n\n")
            else:
                self.txt_hist_ti.insert('end', f"[{data}] {item.tipo}\n{item.mensagem}\n\n")

        self.txt_hist_ti.configure(state='disabled')

        # Guardar ID do chamado selecionado
        self._chamado_selecionado_ti = id_chamado

    def _verificar_chamado_assumido(self, id_chamado: int) -> bool:
        """
        Verifica se o chamado foi assumido pelo analista logado.
        Retorna True se o analista pode operar no chamado.
        """
        from config.database import get_connection

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT ANALISTA_RESP FROM PCS_CHAMADOS_TI WHERE ID = :id",
                {"id": id_chamado}
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row and row[0]:
                analista_resp = row[0]
                if analista_resp == self.matricula_logada:
                    return True
                else:
                    messagebox.showwarning(
                        "Acesso Negado",
                        f"Este chamado está atribuído a outro analista.\n\n"
                        f"Apenas o analista responsável pode executar esta ação."
                    )
                    return False
            else:
                messagebox.showwarning(
                    "Chamado Não Assumido",
                    "Você precisa ASSUMIR o chamado antes de executar esta ação.\n\n"
                    "Clique no botão 'Assumir' primeiro."
                )
                return False

        except Exception as e:
            logger.error(f"Erro ao verificar responsável: {e}")
            return False

    def _assumir_chamado(self):
        """Assume o chamado selecionado"""
        id_chamado = self._get_selected_id_ti()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        # Verificar se já está assumido por outro analista
        from config.database import get_connection
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT ANALISTA_RESP, STATUS FROM PCS_CHAMADOS_TI WHERE ID = :id",
                {"id": id_chamado}
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                analista_atual, status = row[0], row[1]

                if status == 'FINALIZADO':
                    messagebox.showwarning("Aviso", "Este chamado já foi finalizado.")
                    return

                if analista_atual and analista_atual != self.matricula_logada:
                    if not messagebox.askyesno(
                        "Chamado já assumido",
                        f"Este chamado já está atribuído a outro analista.\n\n"
                        f"Deseja transferir para você?"
                    ):
                        return

                if analista_atual == self.matricula_logada:
                    messagebox.showinfo("Info", "Você já é o responsável por este chamado.")
                    return

        except Exception as e:
            logger.error(f"Erro ao verificar chamado: {e}")

        if ChamadoService.assumir_chamado(id_chamado, self.matricula_logada):
            messagebox.showinfo("Sucesso", f"Chamado #{id_chamado} assumido com sucesso!\n\nAgora você pode responder, mover e alterar prioridade.")
            self._carregar_chamados_ti()
        else:
            messagebox.showerror("Erro", "Falha ao assumir chamado.")

    def _responder_ti(self):
        """Responde ao chamado selecionado (requer assumir primeiro) com opção de anexo"""
        id_chamado = self._get_selected_id_ti()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        # Verificar se assumiu o chamado
        if not self._verificar_chamado_assumido(id_chamado):
            return

        # Usar diálogo customizado com anexo
        from gui.dialogs.resposta_dialog import RespostaDialog
        dialog = RespostaDialog(self, titulo="Responder ao Usuário", is_analista=True)
        resultado = dialog.get_resultado()

        if resultado:
            resposta = resultado['resposta']
            anexo = resultado['anexo']

            # Enviar resposta
            if ChamadoService.resposta_analista(id_chamado, self.matricula_logada, resposta):
                # Se houver anexo, copiar e registrar
                if anexo:
                    try:
                        destino = self._copiar_anexo(anexo, id_chamado)
                        ChamadoService.registrar_anexo_adicional(id_chamado, self.matricula_logada, destino)
                        messagebox.showinfo("Sucesso", "Resposta enviada com anexo!")
                    except Exception as e:
                        logger.warning(f"Erro ao copiar anexo: {e}")
                        messagebox.showinfo("Sucesso", "Resposta enviada! (Anexo não foi salvo)")
                else:
                    messagebox.showinfo("Sucesso", "Resposta enviada!")

                self._carregar_chamados_ti()
                self._carregar_historico_ti(id_chamado)
            else:
                messagebox.showerror("Erro", "Falha ao enviar resposta.")

    def _mover_categoria(self):
        """Move chamado para outra categoria (requer assumir primeiro)"""
        id_chamado = self._get_selected_id_ti()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        # Verificar se assumiu o chamado
        if not self._verificar_chamado_assumido(id_chamado):
            return

        # Criar diálogo para selecionar categoria
        nova_categoria = simpledialog.askstring(
            "Mover Categoria",
            f"Categorias: {', '.join(settings.LISTA_CATEGORIA_MOVER)}\n\nDigite a nova categoria:"
        )

        if nova_categoria and nova_categoria in settings.LISTA_CATEGORIA_MOVER:
            if ChamadoService.mover_categoria(id_chamado, self.matricula_logada, nova_categoria):
                messagebox.showinfo("Sucesso", f"Chamado movido para {nova_categoria}!")
                self._carregar_chamados_ti()
            else:
                messagebox.showerror("Erro", "Falha ao mover categoria.")

    def _mover_prioridade(self):
        """Altera prioridade do chamado (requer assumir primeiro)"""
        id_chamado = self._get_selected_id_ti()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        # Verificar se assumiu o chamado
        if not self._verificar_chamado_assumido(id_chamado):
            return

        nova_prioridade = simpledialog.askstring(
            "Alterar Prioridade",
            "Opções: ALTA, MEDIA, BAIXA\n\nDigite a nova prioridade:"
        )

        if nova_prioridade and nova_prioridade.upper() in ['ALTA', 'MEDIA', 'BAIXA']:
            if ChamadoService.mover_prioridade(id_chamado, self.matricula_logada, nova_prioridade.upper()):
                messagebox.showinfo("Sucesso", f"Prioridade alterada para {nova_prioridade.upper()}!")
                self._carregar_chamados_ti()
            else:
                messagebox.showerror("Erro", "Falha ao alterar prioridade.")

    def _ver_anexos_ti(self):
        """Abre diálogo com lista de anexos do chamado (requer assumir primeiro)"""
        id_chamado = self._get_selected_id_ti()
        if not id_chamado:
            messagebox.showwarning("Aviso", "Selecione um chamado.")
            return

        # Verificar se assumiu o chamado
        if not self._verificar_chamado_assumido(id_chamado):
            return

        anexos = ChamadoService.buscar_anexos(id_chamado)

        if not anexos:
            messagebox.showinfo("Aviso", "Nenhum anexo encontrado neste chamado.")
            return

        # Usar diálogo customizado para listar anexos
        from gui.dialogs.resposta_dialog import HistoricoAnexosDialog
        HistoricoAnexosDialog(self, id_chamado, anexos)

    # ========== Handlers Dashboard ==========

    def _carregar_dashboard(self):
        """Carrega dados do dashboard com métricas completas"""
        try:
            from config.database import get_connection

            # Obter período selecionado
            data_ini = datetime.combine(
                self.date_ini_gerencia.get_date(),
                datetime.min.time()
            )
            data_fim = datetime.combine(
                self.date_fim_gerencia.get_date(),
                datetime.max.time()
            )

            conn = get_connection()
            cur = conn.cursor()

            # ===== KPIs COMPLETOS =====
            cur.execute("""
                SELECT
                    COUNT(*) AS TOTAL,
                    SUM(CASE WHEN STATUS != 'FINALIZADO' THEN 1 ELSE 0 END) AS ABERTOS,
                    SUM(CASE WHEN STATUS = 'FINALIZADO' THEN 1 ELSE 0 END) AS FINALIZADOS,
                    SUM(CASE WHEN STATUS_SLA = 'ATRASADO' AND STATUS != 'FINALIZADO' THEN 1 ELSE 0 END) AS ATRASADOS,
                    SUM(CASE WHEN ANALISTA_RESP IS NULL AND STATUS IN ('ABERTO', 'EM_RESOLUCAO') THEN 1 ELSE 0 END) AS SEM_ANALISTA,
                    SUM(CASE WHEN TRUNC(DATA_ABERTURA) = TRUNC(SYSDATE) THEN 1 ELSE 0 END) AS NOVOS_HOJE
                FROM PCS_CHAMADOS_TI
                WHERE DATA_ABERTURA BETWEEN :dt_ini AND :dt_fim
            """, {"dt_ini": data_ini, "dt_fim": data_fim})
            row = cur.fetchone()

            total = row[0] or 0
            abertos = row[1] or 0
            finalizados = row[2] or 0
            atrasados = row[3] or 0
            sem_analista = row[4] or 0
            novos_hoje = row[5] or 0

            # Tempo médio de resolução
            cur.execute("""
                SELECT ROUND(AVG((DATA_FECHAMENTO - DATA_ABERTURA) * 24 * 60), 0)
                FROM PCS_CHAMADOS_TI
                WHERE STATUS = 'FINALIZADO'
                  AND DATA_ABERTURA BETWEEN :dt_ini AND :dt_fim
                  AND DATA_FECHAMENTO IS NOT NULL
            """, {"dt_ini": data_ini, "dt_fim": data_fim})
            row_tempo = cur.fetchone()
            tempo_min = row_tempo[0] or 0
            if tempo_min >= 60:
                tempo_texto = f"{int(tempo_min // 60)}h{int(tempo_min % 60):02d}"
            else:
                tempo_texto = f"{int(tempo_min)}min"

            # SLA compliance
            cur.execute("""
                SELECT
                    COUNT(*) AS TOTAL,
                    SUM(CASE WHEN DATA_FECHAMENTO <= DATA_LIMITE_SLA THEN 1 ELSE 0 END) AS DENTRO
                FROM PCS_CHAMADOS_TI
                WHERE STATUS = 'FINALIZADO'
                  AND DATA_LIMITE_SLA IS NOT NULL
                  AND DATA_ABERTURA BETWEEN :dt_ini AND :dt_fim
            """, {"dt_ini": data_ini, "dt_fim": data_fim})
            row_sla = cur.fetchone()
            sla_total = row_sla[0] or 0
            sla_dentro = row_sla[1] or 0
            sla_percent = round((sla_dentro / sla_total * 100), 1) if sla_total > 0 else 100

            # Taxa de resolução
            taxa_resolucao = round((finalizados / total * 100), 1) if total > 0 else 0

            # ===== ATUALIZAR KPIs =====
            # Novos Hoje
            self.kpi_labels['novos_hoje'].configure(text=str(novos_hoje), text_color="#3b82f6")
            self.kpi_subtitles['novos_hoje'].configure(text="abertos hoje")

            # Total no Período
            self.kpi_labels['total'].configure(text=str(total), text_color="#6366f1")
            dias = (data_fim - data_ini).days + 1
            self.kpi_subtitles['total'].configure(text=f"em {dias} dias")

            # Em Aberto
            self.kpi_labels['abertos'].configure(
                text=str(abertos),
                text_color="#f59e0b" if abertos > 0 else "#22c55e"
            )
            self.kpi_subtitles['abertos'].configure(text="pendentes")

            # Finalizados
            self.kpi_labels['finalizados'].configure(text=str(finalizados), text_color="#22c55e")
            self.kpi_subtitles['finalizados'].configure(text=f"{taxa_resolucao}% resolvidos")

            # Atrasados
            self.kpi_labels['atrasados'].configure(
                text=str(atrasados),
                text_color="#ef4444" if atrasados > 0 else "#22c55e"
            )
            self.kpi_subtitles['atrasados'].configure(text="SLA vencido")

            # Sem Analista
            self.kpi_labels['sem_analista'].configure(
                text=str(sem_analista),
                text_color="#f97316" if sem_analista > 0 else "#22c55e"
            )
            self.kpi_subtitles['sem_analista'].configure(text="não atribuídos")

            # Tempo Médio
            self.kpi_labels['tempo_medio'].configure(text=tempo_texto, text_color="#8b5cf6")
            self.kpi_subtitles['tempo_medio'].configure(text="resolução")

            # SLA Cumprido
            self.kpi_labels['sla_percent'].configure(
                text=f"{sla_percent}%",
                text_color="#10b981" if sla_percent >= 80 else "#ef4444"
            )
            self.kpi_subtitles['sla_percent'].configure(text=f"{sla_dentro}/{sla_total} no prazo")

            # ===== TABELAS =====

            # Top 10 Usuários
            cur.execute("""
                SELECT
                    NVL(NOME_USUARIO, 'Não identificado') AS USUARIO,
                    COUNT(*) AS TOTAL,
                    SUM(CASE WHEN STATUS != 'FINALIZADO' THEN 1 ELSE 0 END) AS ABERTOS,
                    SUM(CASE WHEN STATUS = 'FINALIZADO' THEN 1 ELSE 0 END) AS FINALIZADOS
                FROM PCS_CHAMADOS_TI
                WHERE DATA_ABERTURA BETWEEN :dt_ini AND :dt_fim
                GROUP BY NOME_USUARIO
                ORDER BY TOTAL DESC
                FETCH FIRST 10 ROWS ONLY
            """, {"dt_ini": data_ini, "dt_fim": data_fim})

            for item in self.tree_usuarios.get_children():
                self.tree_usuarios.delete(item)
            for idx, row in enumerate(cur.fetchall()):
                tag = 'oddrow' if idx % 2 else 'evenrow'
                self.tree_usuarios.insert('', 'end', values=row, tags=(tag,))

            # Por Categoria
            cur.execute("""
                SELECT
                    NVL(CATEGORIA, 'Outros') AS CATEGORIA,
                    COUNT(*) AS TOTAL,
                    SUM(CASE WHEN STATUS != 'FINALIZADO' THEN 1 ELSE 0 END) AS ABERTOS,
                    SUM(CASE WHEN STATUS = 'FINALIZADO' THEN 1 ELSE 0 END) AS FINALIZADOS
                FROM PCS_CHAMADOS_TI
                WHERE DATA_ABERTURA BETWEEN :dt_ini AND :dt_fim
                GROUP BY CATEGORIA
                ORDER BY TOTAL DESC
            """, {"dt_ini": data_ini, "dt_fim": data_fim})

            for item in self.tree_categoria.get_children():
                self.tree_categoria.delete(item)
            for idx, row in enumerate(cur.fetchall()):
                tag = 'oddrow' if idx % 2 else 'evenrow'
                self.tree_categoria.insert('', 'end', values=row, tags=(tag,))

            # Por Status (com percentual)
            cur.execute("""
                SELECT STATUS, COUNT(*) AS QTD
                FROM PCS_CHAMADOS_TI
                WHERE DATA_ABERTURA BETWEEN :dt_ini AND :dt_fim
                GROUP BY STATUS
                ORDER BY
                    CASE STATUS
                        WHEN 'ABERTO' THEN 1
                        WHEN 'EM_RESOLUCAO' THEN 2
                        WHEN 'AGUARDANDO' THEN 3
                        WHEN 'FINALIZADO' THEN 4
                    END
            """, {"dt_ini": data_ini, "dt_fim": data_fim})

            for item in self.tree_status.get_children():
                self.tree_status.delete(item)
            for idx, row in enumerate(cur.fetchall()):
                status, qtd = row
                pct = round((qtd / total * 100), 1) if total > 0 else 0
                tag = 'oddrow' if idx % 2 else 'evenrow'
                self.tree_status.insert('', 'end', values=(status, qtd, f"{pct}%"), tags=(tag,))

            # Por Analista
            cur.execute("""
                SELECT
                    NVL((SELECT nome_guerra FROM pcempr WHERE matricula = c.ANALISTA_RESP), 'Não atribuído') AS ANALISTA,
                    COUNT(*) AS TOTAL,
                    SUM(CASE WHEN STATUS != 'FINALIZADO' THEN 1 ELSE 0 END) AS ABERTOS,
                    SUM(CASE WHEN STATUS_SLA = 'ATRASADO' AND STATUS != 'FINALIZADO' THEN 1 ELSE 0 END) AS ATRASADOS
                FROM PCS_CHAMADOS_TI c
                WHERE DATA_ABERTURA BETWEEN :dt_ini AND :dt_fim
                GROUP BY ANALISTA_RESP
                ORDER BY TOTAL DESC
            """, {"dt_ini": data_ini, "dt_fim": data_fim})

            for item in self.tree_analista.get_children():
                self.tree_analista.delete(item)
            for idx, row in enumerate(cur.fetchall()):
                tag = 'oddrow' if idx % 2 else 'evenrow'
                self.tree_analista.insert('', 'end', values=row, tags=(tag,))

            cur.close()
            conn.close()

            self._update_last_update()

        except Exception as e:
            logger.error(f"Erro ao carregar dashboard: {e}")
            import traceback
            traceback.print_exc()

    # ========== Métodos utilitários ==========

    def _get_sla_tag(self, status: str) -> str:
        """Retorna tag de cor para SLA"""
        tags = {
            'NO_PRAZO': 'sla_ok',
            'ATENCAO': 'sla_atencao',
            'ATRASADO': 'sla_atrasado',
            'FINALIZADO': 'sla_finalizado',
            'SEM_SLA': ''
        }
        return tags.get(status, '')

    def _copiar_anexo(self, origem: str, id_chamado: int) -> str:
        """Copia anexo para servidor"""
        # Conectar compartilhamento
        if not os.path.exists(settings.SERVIDOR_REDE):
            raise Exception("Servidor de arquivos não disponível")

        # Criar pasta do chamado
        pasta_chamado = os.path.join(settings.ANEXOS_DIR, str(id_chamado))
        os.makedirs(pasta_chamado, exist_ok=True)

        # Copiar arquivo
        destino = os.path.join(pasta_chamado, os.path.basename(origem))
        shutil.copy2(origem, destino)

        return destino

    def _abrir_anexos(self, id_chamado: int):
        """Abre pasta de anexos do chamado"""
        anexos = ChamadoService.buscar_anexos(id_chamado)

        if not anexos:
            messagebox.showinfo("Aviso", "Nenhum anexo encontrado.")
            return

        # Abrir primeiro anexo ou pasta
        try:
            pasta = os.path.join(settings.ANEXOS_DIR, str(id_chamado))
            if os.path.exists(pasta):
                os.startfile(pasta)
            elif anexos:
                os.startfile(anexos[0])
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_closing(self):
        """Handler de fechamento"""
        try:
            db_pool.close()
        except Exception:
            pass
        self.destroy()


def run_app(usuario_wt=None, senha_bd=None, alias_bd=None, usuario_bd=None, cod_rotina=None):
    """Função para executar a aplicação"""
    app = App(
        usuario_wt=usuario_wt,
        senha_bd=senha_bd,
        alias_bd=alias_bd,
        usuario_bd=usuario_bd,
        cod_rotina=cod_rotina
    )
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
