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
