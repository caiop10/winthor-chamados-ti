# -*- coding: utf-8 -*-
"""
Diálogo de Resposta com Anexo
"""
import os
import customtkinter as ctk
from tkinter import filedialog


class RespostaDialog(ctk.CTkToplevel):
    """Diálogo para resposta com opção de anexar arquivo"""

    def __init__(self, parent, titulo="Responder Chamado", is_analista=False):
        super().__init__(parent)

        self.title(titulo)
        self.geometry("500x350")
        self.resizable(False, False)

        # Centralizar na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 350) // 2
        self.geometry(f"500x350+{x}+{y}")

        # Resultado
        self.resultado = None
        self.anexo_path = None

        # Tornar modal
        self.transient(parent)
        self.grab_set()

        # Título
        ctk.CTkLabel(
            self,
            text=titulo,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 10))

        # Texto da resposta
        ctk.CTkLabel(
            self,
            text="Digite sua resposta:",
            font=("Segoe UI", 12)
        ).pack(anchor='w', padx=20)

        self.text_resposta = ctk.CTkTextbox(self, height=150)
        self.text_resposta.pack(fill='x', padx=20, pady=10)

        # Frame de anexo
        anexo_frame = ctk.CTkFrame(self, fg_color="transparent")
        anexo_frame.pack(fill='x', padx=20)

        ctk.CTkButton(
            anexo_frame,
            text="📎 Anexar Arquivo",
            command=self._selecionar_anexo,
            width=140
        ).pack(side='left')

        self.lbl_anexo = ctk.CTkLabel(
            anexo_frame,
            text="Nenhum arquivo",
            text_color="#64748b"
        )
        self.lbl_anexo.pack(side='left', padx=10)

        self.btn_remover = ctk.CTkButton(
            anexo_frame,
            text="✕",
            width=30,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self._remover_anexo
        )

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill='x', padx=20, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self._cancelar,
            fg_color="#6b7280",
            hover_color="#4b5563",
            width=100
        ).pack(side='right', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Enviar",
            command=self._enviar,
            fg_color="#22c55e",
            hover_color="#16a34a",
            width=100
        ).pack(side='right', padx=5)

        # Focar no texto
        self.text_resposta.focus_set()

        # Bind Enter para enviar
        self.bind('<Return>', lambda e: self._enviar() if e.state & 0x4 else None)  # Ctrl+Enter
        self.bind('<Escape>', lambda e: self._cancelar())

    def _selecionar_anexo(self):
        """Seleciona arquivo para anexar"""
        path = filedialog.askopenfilename(
            title="Selecione um arquivo",
            filetypes=[
                ("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("PDF", "*.pdf"),
                ("Documentos", "*.doc;*.docx;*.xls;*.xlsx;*.txt"),
                ("Todos", "*.*")
            ]
        )
        if path:
            self.anexo_path = path
            self.lbl_anexo.configure(text=os.path.basename(path), text_color="#22c55e")
            self.btn_remover.pack(side='left', padx=5)

    def _remover_anexo(self):
        """Remove o anexo selecionado"""
        self.anexo_path = None
        self.lbl_anexo.configure(text="Nenhum arquivo", text_color="#64748b")
        self.btn_remover.pack_forget()

    def _enviar(self):
        """Confirma e fecha o diálogo"""
        resposta = self.text_resposta.get('1.0', 'end').strip()
        if not resposta:
            self.lbl_anexo.configure(text="Digite uma resposta!", text_color="#ef4444")
            return

        self.resultado = {
            'resposta': resposta,
            'anexo': self.anexo_path
        }
        self.destroy()

    def _cancelar(self):
        """Cancela e fecha o diálogo"""
        self.resultado = None
        self.destroy()

    def get_resultado(self):
        """Retorna o resultado após o diálogo fechar"""
        self.wait_window()
        return self.resultado


class HistoricoAnexosDialog(ctk.CTkToplevel):
    """Diálogo para visualizar anexos do histórico"""

    def __init__(self, parent, id_chamado, anexos_list):
        super().__init__(parent)

        self.title(f"Anexos do Chamado #{id_chamado}")
        self.geometry("600x400")

        # Centralizar
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 400) // 2
        self.geometry(f"600x400+{x}+{y}")

        self.transient(parent)
        self.grab_set()

        # Título
        ctk.CTkLabel(
            self,
            text=f"📎 Anexos do Chamado #{id_chamado}",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=20)

        # Lista de anexos
        if not anexos_list:
            ctk.CTkLabel(
                self,
                text="Nenhum anexo encontrado.",
                text_color="#64748b"
            ).pack(pady=20)
        else:
            scroll_frame = ctk.CTkScrollableFrame(self, height=250)
            scroll_frame.pack(fill='both', expand=True, padx=20, pady=10)

            for idx, anexo in enumerate(anexos_list):
                frame = ctk.CTkFrame(scroll_frame)
                frame.pack(fill='x', pady=5)

                # Ícone baseado na extensão
                ext = os.path.splitext(anexo)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    icon = "🖼️"
                elif ext == '.pdf':
                    icon = "📄"
                else:
                    icon = "📁"

                ctk.CTkLabel(
                    frame,
                    text=f"{icon} {os.path.basename(anexo)}",
                    font=("Segoe UI", 11)
                ).pack(side='left', padx=10, pady=5)

                ctk.CTkButton(
                    frame,
                    text="Abrir",
                    command=lambda a=anexo: self._abrir_anexo(a),
                    width=70,
                    fg_color="#3b82f6"
                ).pack(side='right', padx=5, pady=5)

                ctk.CTkButton(
                    frame,
                    text="Pasta",
                    command=lambda a=anexo: self._abrir_pasta(a),
                    width=70,
                    fg_color="#6b7280"
                ).pack(side='right', padx=5, pady=5)

        # Botão fechar
        ctk.CTkButton(
            self,
            text="Fechar",
            command=self.destroy,
            width=100
        ).pack(pady=20)

    def _abrir_anexo(self, caminho):
        """Abre o anexo"""
        try:
            if os.path.exists(caminho):
                os.startfile(caminho)
            else:
                from tkinter import messagebox
                messagebox.showerror("Erro", f"Arquivo não encontrado:\n{caminho}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro", str(e))

    def _abrir_pasta(self, caminho):
        """Abre a pasta do anexo"""
        try:
            pasta = os.path.dirname(caminho)
            if os.path.exists(pasta):
                os.startfile(pasta)
            else:
                from tkinter import messagebox
                messagebox.showerror("Erro", f"Pasta não encontrada:\n{pasta}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro", str(e))


class SelecionarCategoriaDialog(ctk.CTkToplevel):
    """Diálogo para selecionar categoria"""

    def __init__(self, parent, categorias: list, categoria_atual: str = None):
        super().__init__(parent)

        self.title("Mover Categoria")
        self.geometry("400x450")
        self.resizable(False, False)

        # Centralizar
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 450) // 2
        self.geometry(f"400x450+{x}+{y}")

        self.resultado = None
        self.transient(parent)
        self.grab_set()

        # Título
        ctk.CTkLabel(
            self,
            text="📁 Selecione a Nova Categoria",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 10))

        if categoria_atual:
            ctk.CTkLabel(
                self,
                text=f"Categoria atual: {categoria_atual}",
                text_color="#64748b"
            ).pack(pady=(0, 10))

        # Frame com scroll para categorias
        scroll_frame = ctk.CTkScrollableFrame(self, height=280)
        scroll_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.var_categoria = ctk.StringVar(value="")

        for cat in categorias:
            btn = ctk.CTkRadioButton(
                scroll_frame,
                text=cat,
                variable=self.var_categoria,
                value=cat,
                font=("Segoe UI", 12)
            )
            btn.pack(anchor='w', pady=5, padx=10)

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill='x', padx=20, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self._cancelar,
            fg_color="#6b7280",
            hover_color="#4b5563",
            width=100
        ).pack(side='right', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Confirmar",
            command=self._confirmar,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            width=100
        ).pack(side='right', padx=5)

        self.bind('<Escape>', lambda e: self._cancelar())

    def _confirmar(self):
        """Confirma a seleção"""
        cat = self.var_categoria.get()
        if cat:
            self.resultado = cat
            self.destroy()
        else:
            from tkinter import messagebox
            messagebox.showwarning("Aviso", "Selecione uma categoria.")

    def _cancelar(self):
        """Cancela"""
        self.resultado = None
        self.destroy()

    def get_resultado(self):
        """Retorna a categoria selecionada"""
        self.wait_window()
        return self.resultado


class SelecionarPrioridadeDialog(ctk.CTkToplevel):
    """Diálogo para selecionar prioridade"""

    def __init__(self, parent, prioridade_atual: str = None):
        super().__init__(parent)

        self.title("Alterar Prioridade")
        self.geometry("350x280")
        self.resizable(False, False)

        # Centralizar
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 350) // 2
        y = (self.winfo_screenheight() - 280) // 2
        self.geometry(f"350x280+{x}+{y}")

        self.resultado = None
        self.transient(parent)
        self.grab_set()

        # Título
        ctk.CTkLabel(
            self,
            text="⚡ Selecione a Nova Prioridade",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 10))

        if prioridade_atual:
            ctk.CTkLabel(
                self,
                text=f"Prioridade atual: {prioridade_atual}",
                text_color="#64748b"
            ).pack(pady=(0, 10))

        # Frame para prioridades
        prio_frame = ctk.CTkFrame(self, fg_color="transparent")
        prio_frame.pack(fill='x', padx=40, pady=10)

        self.var_prioridade = ctk.StringVar(value="")

        prioridades = [
            ("🔴 ALTA", "ALTA", "#ef4444"),
            ("🟡 MEDIA", "MEDIA", "#f59e0b"),
            ("🟢 BAIXA", "BAIXA", "#22c55e")
        ]

        for texto, valor, cor in prioridades:
            btn = ctk.CTkRadioButton(
                prio_frame,
                text=texto,
                variable=self.var_prioridade,
                value=valor,
                font=("Segoe UI", 14)
            )
            btn.pack(anchor='w', pady=8)

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill='x', padx=20, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self._cancelar,
            fg_color="#6b7280",
            hover_color="#4b5563",
            width=100
        ).pack(side='right', padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Confirmar",
            command=self._confirmar,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            width=100
        ).pack(side='right', padx=5)

        self.bind('<Escape>', lambda e: self._cancelar())

    def _confirmar(self):
        """Confirma a seleção"""
        prio = self.var_prioridade.get()
        if prio:
            self.resultado = prio
            self.destroy()
        else:
            from tkinter import messagebox
            messagebox.showwarning("Aviso", "Selecione uma prioridade.")

    def _cancelar(self):
        """Cancela"""
        self.resultado = None
        self.destroy()

    def get_resultado(self):
        """Retorna a prioridade selecionada"""
        self.wait_window()
        return self.resultado
