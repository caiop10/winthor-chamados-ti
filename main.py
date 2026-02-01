# -*- coding: utf-8 -*-
"""
Chamados TI - SOTRIGO
Entry Point da Aplicação GUI

Versão 6.0 - Arquitetura Modular
"""
import sys
import os

# Configurar Oracle ANTES de qualquer import
os.environ['ORACLE_HOME'] = r'C:\oracle\instantclient_23_0'
os.environ['TNS_ADMIN'] = r'C:\oracle\instantclient_23_0'
os.environ['PATH'] = r'C:\oracle\instantclient_23_0;' + os.environ.get('PATH', '')


def show_loading():
    """Mostra tela de loading enquanto carrega o sistema"""
    import tkinter as tk
    from tkinter import ttk

    loading = tk.Tk()
    loading.overrideredirect(True)
    loading.attributes('-topmost', True)
    loading.configure(bg='#0f172a')

    w, h = 400, 250
    screen_w = loading.winfo_screenwidth()
    screen_h = loading.winfo_screenheight()
    x = (screen_w - w) // 2
    y = (screen_h - h) // 2
    loading.geometry(f"{w}x{h}+{x}+{y}")

    frame = tk.Frame(loading, bg='#0f172a')
    frame.pack(expand=True, fill='both', padx=20, pady=20)

    tk.Label(
        frame,
        text="SOTRIGO",
        font=("Segoe UI", 28, "bold"),
        fg="#3b82f6",
        bg="#0f172a"
    ).pack(pady=(20, 5))

    tk.Label(
        frame,
        text="Sistema de Chamados TI",
        font=("Segoe UI", 12),
        fg="#94a3b8",
        bg="#0f172a"
    ).pack(pady=(0, 30))

    status = tk.Label(
        frame,
        text="Iniciando sistema...",
        font=("Segoe UI", 10),
        fg="#cbd5e1",
        bg="#0f172a"
    )
    status.pack(pady=(0, 15))

    style = ttk.Style()
    style.theme_use('clam')
    style.configure(
        "Blue.Horizontal.TProgressbar",
        troughcolor='#1e293b',
        background='#3b82f6'
    )

    progress = ttk.Progressbar(
        frame,
        style="Blue.Horizontal.TProgressbar",
        length=300,
        mode='indeterminate'
    )
    progress.pack(pady=(0, 20))
    progress.start(20)

    tk.Label(
        frame,
        text="v6.0 - Modular",
        font=("Segoe UI", 8),
        fg="#64748b",
        bg="#0f172a"
    ).pack(side='bottom', pady=(10, 0))

    return loading, status


def main():
    """Função principal"""
    # Mostrar loading
    loading, status_label = show_loading()
    loading.update()

    def update_status(msg):
        status_label.config(text=msg)
        loading.update_idletasks()

    # Ler parâmetros
    update_status("Lendo parâmetros...")

    usuario_wt = sys.argv[1].strip() if len(sys.argv) >= 2 else None
    senha_bd = sys.argv[2] if len(sys.argv) >= 3 else None
    alias_bd = sys.argv[3] if len(sys.argv) >= 4 else None
    usuario_bd = sys.argv[4].strip() if len(sys.argv) >= 5 else None
    cod_rotina = sys.argv[5] if len(sys.argv) >= 6 else None

    # Validar parâmetros
    if not usuario_wt:
        loading.destroy()
        import tkinter.messagebox as mb
        mb.showerror("Erro", "USUARIOWT não foi informado.\n\nExecute a rotina pelo WinThor.")
        sys.exit(1)

    # Carregar módulos
    update_status("Carregando módulos...")

    try:
        from gui.app import App
        update_status("Inicializando conexão...")
    except ImportError as e:
        loading.destroy()
        import tkinter.messagebox as mb
        mb.showerror("Erro", f"Erro ao carregar módulos:\n{e}")
        sys.exit(1)

    # Fechar loading e iniciar app
    update_status("Iniciando aplicação...")
    loading.destroy()

    # Executar aplicação
    app = App(
        usuario_wt=usuario_wt,
        senha_bd=senha_bd,
        alias_bd=alias_bd,
        usuario_bd=usuario_bd,
        cod_rotina=cod_rotina
    )
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
