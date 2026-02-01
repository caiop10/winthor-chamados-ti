# -*- coding: utf-8 -*-
"""
PSAAP9805 - Chamados TI (Versão Refatorada)
Launcher para integração com WinThor

Este launcher recebe os parâmetros do WinThor e inicia a aplicação
de chamados de TI na versão modular refatorada.

Parâmetros esperados do WinThor:
    sys.argv[1] = USUARIOWT (matrícula ou nome do usuário)
    sys.argv[2] = SENHABD (senha do banco)
    sys.argv[3] = ALIASBD (alias de conexão)
    sys.argv[4] = USUARIOBD (usuário do banco)
    sys.argv[5] = CODROTINA (código da rotina - 9805)
"""
import sys
import os

# Detectar diretório do projeto
# Se executando como .exe (PyInstaller), usar pasta P: (compartilhada via VPN)
# Se executando como .py/.pyw, usar diretório do script
if getattr(sys, 'frozen', False):
    # Executável compilado - usar pasta P: compartilhada
    PROJETO_DIR = r"P:\ROTINA-CHAMADO"
else:
    # Executando como script Python
    PROJETO_DIR = os.path.dirname(os.path.abspath(__file__))

# Adicionar diretório do projeto ao path
sys.path.insert(0, PROJETO_DIR)

# Mudar diretório de trabalho (com tratamento de erro)
try:
    os.chdir(PROJETO_DIR)
except Exception:
    pass  # Ignorar se não conseguir mudar


def show_splash():
    """Mostra tela de loading"""
    from gui.splash_screen import SplashScreen
    return SplashScreen()


def load_and_run(splash, usuario_wt, senha_bd, alias_bd, usuario_bd, cod_rotina):
    """Carrega e executa a aplicação"""
    import time

    try:
        splash.update_status("Carregando configurações...")
        from config.settings import settings
        time.sleep(0.2)

        splash.update_status("Conectando ao banco de dados...")
        from config.database import db_pool
        time.sleep(0.3)

        splash.update_status("Carregando serviços...")
        from services.chamado_service import ChamadoService
        from services.sla_service import SLAService
        time.sleep(0.2)

        splash.update_status("Iniciando interface...")
        from gui.app import App
        time.sleep(0.2)

        splash.update_status("Preparando aplicação...")
        time.sleep(0.1)

        # Fechar splash
        splash.close()

        # Iniciar aplicação
        app = App(
            usuario_wt=usuario_wt,
            senha_bd=senha_bd,
            alias_bd=alias_bd,
            usuario_bd=usuario_bd,
            cod_rotina=cod_rotina
        )
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()

    except Exception as e:
        splash.close()
        raise e


def main():
    """Função principal do launcher"""
    # Extrair parâmetros do WinThor
    usuario_wt = sys.argv[1] if len(sys.argv) > 1 else None
    senha_bd = sys.argv[2] if len(sys.argv) > 2 else None
    alias_bd = sys.argv[3] if len(sys.argv) > 3 else None
    usuario_bd = sys.argv[4] if len(sys.argv) > 4 else None
    cod_rotina = sys.argv[5] if len(sys.argv) > 5 else "9805"

    # Validar parâmetros obrigatórios
    if not usuario_wt:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Erro",
                "USUARIOWT não foi informado.\n\n"
                "Esta rotina deve ser executada através do WinThor."
            )
            root.destroy()
        except:
            print("ERRO: USUARIOWT não foi informado")
        return

    # Mostrar splash screen
    splash = show_splash()

    # Log de inicialização
    try:
        splash.update_status("Iniciando logs...")
        from utils.logger import logger
        logger.info(f"Launcher iniciado - Usuário: {usuario_wt}")
    except:
        pass

    # Carregar e executar aplicação
    try:
        # Usar after para permitir que a splash seja exibida
        splash.root.after(100, lambda: load_and_run(
            splash, usuario_wt, senha_bd, alias_bd, usuario_bd, cod_rotina
        ))
        splash.run()

    except Exception as e:
        try:
            splash.close()
        except:
            pass

        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Erro ao iniciar",
                f"Falha ao iniciar Chamados TI:\n\n{str(e)}\n\nDiretório: {PROJETO_DIR}"
            )
            root.destroy()
        except:
            print(f"ERRO: {e}")

        try:
            from utils.logger import logger
            logger.error(f"Erro no launcher: {e}")
        except:
            pass


if __name__ == "__main__":
    main()
