# -*- coding: utf-8 -*-
"""
Tela de Loading/Splash Screen
"""
import tkinter as tk
from tkinter import ttk
import threading


class SplashScreen:
    """Tela de carregamento do sistema"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")

        # Remover bordas e barra de título
        self.root.overrideredirect(True)

        # Tamanho da janela
        width = 400
        height = 250

        # Centralizar na tela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Cor de fundo
        self.root.configure(bg="#1a1a2e")

        # Manter no topo
        self.root.attributes('-topmost', True)

        # Frame principal
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Ícone/Logo (emoji grande)
        logo_label = tk.Label(
            main_frame,
            text="🎫",
            font=("Segoe UI Emoji", 48),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        logo_label.pack(pady=(20, 10))

        # Título
        title_label = tk.Label(
            main_frame,
            text="Chamados TI",
            font=("Segoe UI", 24, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        title_label.pack(pady=(0, 5))

        # Subtítulo
        subtitle_label = tk.Label(
            main_frame,
            text="Sistema de Gestão de Chamados",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#64748b"
        )
        subtitle_label.pack(pady=(0, 20))

        # Barra de progresso
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#2d2d44',
            background='#3b82f6',
            thickness=6
        )

        self.progress = ttk.Progressbar(
            main_frame,
            style="Custom.Horizontal.TProgressbar",
            orient="horizontal",
            length=300,
            mode="indeterminate"
        )
        self.progress.pack(pady=(0, 10))

        # Status
        self.status_var = tk.StringVar(value="Iniciando...")
        self.status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#1a1a2e",
            fg="#94a3b8"
        )
        self.status_label.pack()

        # Versão
        version_label = tk.Label(
            main_frame,
            text="v6.0",
            font=("Segoe UI", 8),
            bg="#1a1a2e",
            fg="#475569"
        )
        version_label.pack(side='bottom', pady=(10, 0))

        # Iniciar animação da barra de progresso
        self.progress.start(15)

    def update_status(self, message: str):
        """Atualiza mensagem de status"""
        self.status_var.set(message)
        self.root.update()

    def close(self):
        """Fecha a splash screen"""
        try:
            self.progress.stop()
            self.root.destroy()
        except:
            pass

    def run(self):
        """Executa o loop principal"""
        self.root.mainloop()


def show_splash_and_load(load_function, *args, **kwargs):
    """
    Mostra splash screen enquanto carrega a aplicação.

    Args:
        load_function: Função que carrega/inicia a aplicação principal
        *args, **kwargs: Argumentos para a função de carregamento
    """
    splash = SplashScreen()
    result = [None]
    error = [None]

    def load_app():
        try:
            # Simular etapas de carregamento
            import time

            splash.update_status("Carregando configurações...")
            time.sleep(0.3)

            splash.update_status("Conectando ao banco de dados...")
            time.sleep(0.3)

            splash.update_status("Carregando módulos...")
            time.sleep(0.3)

            splash.update_status("Iniciando interface...")
            time.sleep(0.2)

            # Executar função de carregamento
            result[0] = load_function(*args, **kwargs)

        except Exception as e:
            error[0] = e
        finally:
            # Fechar splash na thread principal
            splash.root.after(100, splash.close)

    # Iniciar carregamento em thread separada
    thread = threading.Thread(target=load_app, daemon=True)
    thread.start()

    # Executar splash screen
    splash.run()

    # Verificar erro
    if error[0]:
        raise error[0]

    return result[0]
