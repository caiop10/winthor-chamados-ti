# -*- coding: utf-8 -*-
"""
Script para compilar o executável standalone
Inclui todos os arquivos necessários no executável
"""
import PyInstaller.__main__
import os
import shutil

# Diretório do projeto
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Diretório de saída
OUTPUT_DIR = r"C:\winthor\Prod\PSAAP"

# Arquivos e pastas a incluir
add_data = [
    (os.path.join(PROJECT_DIR, "config"), "config"),
    (os.path.join(PROJECT_DIR, "gui"), "gui"),
    (os.path.join(PROJECT_DIR, "models"), "models"),
    (os.path.join(PROJECT_DIR, "services"), "services"),
    (os.path.join(PROJECT_DIR, "utils"), "utils"),
    (os.path.join(PROJECT_DIR, "templates"), "templates"),
    (os.path.join(PROJECT_DIR, "sounds"), "sounds"),
]

# Construir argumentos do PyInstaller
args = [
    os.path.join(PROJECT_DIR, "PSAAP9805_LAUNCHER_novo.pyw"),
    "--onefile",
    "--windowed",
    "--name=PSAAP9805_LAUNCHER",
    f"--distpath={OUTPUT_DIR}",
    "--workpath=" + os.path.join(os.environ["TEMP"], "pyinstaller_build"),
    "--specpath=" + os.path.join(os.environ["TEMP"], "pyinstaller_build"),
    "--clean",
]

# Adicionar dados
for src, dest in add_data:
    if os.path.exists(src):
        args.append(f"--add-data={src};{dest}")

# Hidden imports necessários
hidden_imports = [
    "customtkinter",
    "tkcalendar",
    "babel.numbers",
    "oracledb",
    "dotenv",
    "PIL",
    "plyer",
    "plyer.platforms.win.notification",
]

for imp in hidden_imports:
    args.append(f"--hidden-import={imp}")

print("=" * 60)
print("Compilando executável standalone...")
print("=" * 60)
print(f"Saída: {OUTPUT_DIR}")
print()

# Executar PyInstaller
PyInstaller.__main__.run(args)

print()
print("=" * 60)
print("Compilação concluída!")
print("=" * 60)
