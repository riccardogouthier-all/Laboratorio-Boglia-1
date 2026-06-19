
import os
import sys
import platform

def detect_os(system, version, architecture, processor):
    print("=" * 40)
    print("  Rilevamento Sistema Operativo")
    print("=" * 40)
    
    if system:
        print(f"  Sistema      : {system} ")
        print(f"  Kernel       : {version}")
        print(f"  Architettura : {architecture}")
        print(f"  Processore   : {processor}")
    else:
        print(f"  Sistema      : {system} (non riconosciuto)")

    print(f"  Python       : {sys.version.split()[0]}")
    print("=" * 40)

def install_python_docx(system):
    # --- Conferma installazione ---
    risposta = input(
        "E' necessaria l'installazione delle librerie python-docx per un report testuale e matplotlib, seaborn, pandas, numpy per la produzione di grafici"
        "per il funzionamento del programma, premere y per procedere (Y/n): "
    ).strip().upper() or "Y"  # maiuscola predefinita

    if risposta != "Y":
        print("Installazione annullata.")
        return

    # --- Verifica ambiente virtuale ---
    ambiente = input("Ti trovi dentro un environment? (y/N): ").strip().upper() or "N"

    in_venv = ambiente == "Y"

    # --- Logica di installazione ---
    if not in_venv and system == "Windows":
        os.system("pip install python-docx")  # windows
    elif not in_venv and system == "Linux":
        os.system("pip install python-docx matplotlib seaborn pandas numpy --break-system-packages")  # linux
    elif not in_venv and system == "Darwin":
        os.system("pip3 install python-docx matplotlib seaborn pandas numpy --user")  # mac

    elif in_venv and system == "Windows":
        os.system("python -m pip install python-docx matplotlib seaborn pandas numpy")  # w
    elif in_venv and (system == "Linux" or system == "Darwin"):
        os.system("python3 -m pip install python-docx matplotlib seaborn pandas numpy")  # l, m
    else:
        print(f"Sistema operativo non riconosciuto: {system}")

def install_procedure():
    system = platform.system()  # Windows, Linux, Darwin
    version = platform.version()
    architecture = platform.architecture()
    processor = platform.processor()
    # 
    detect_os(system, version, architecture, processor)
    install_python_docx(system)
