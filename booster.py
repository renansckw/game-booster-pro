# =========================================
# GAME BOOSTER PRO V2.1 - BY RENAN
# =========================================
# pip install psutil

import tkinter as tk
from tkinter import messagebox
import psutil
import subprocess
import os
import ctypes
import sys

GAME_NAME = "valorant"

# Lista de processos que NÃO podem ser fechados (Anti-cheat, Windows, etc.)
WHITELIST = [
    "vgc.exe", "vgtray.exe", "explorer.exe", "dwm.exe", "svchost.exe", 
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", 
    "services.exe", "lsass.exe", "discord.exe", "taskmgr.exe"
]

# Variável para controlar se o auto-boost já foi aplicado na sessão atual do jogo
auto_boost_applied = False

# =========================================
# SISTEMA
# =========================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def set_high_performance():
    subprocess.run("powercfg /setactive SCHEME_MIN", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

def optimize_network():
    # Limpa o cache de DNS para ajudar na estabilidade da conexão
    subprocess.run("ipconfig /flushdns", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

def clean_temp():
    temp = os.getenv('TEMP')
    if not temp: return
    for file in os.listdir(temp):
        try:
            os.remove(os.path.join(temp, file))
        except:
            pass # Arquivos em uso não podem ser apagados, ignoramos silenciosamente

def kill_heavy_processes():
    killed = []
    for p in psutil.process_iter(['name', 'memory_percent']):
        try:
            name = p.info['name'].lower()
            mem = p.info['memory_percent']
            
            # Se consome mais de 5% de RAM, NÃO é o jogo e NÃO está na Whitelist
            if mem > 5 and GAME_NAME not in name and name not in WHITELIST:
                killed.append(name)
                p.kill()
        except:
            pass
    return killed

def set_game_priority():
    for p in psutil.process_iter(['name']):
        try:
            if GAME_NAME in p.info['name'].lower():
                # Define a prioridade do processo do jogo como ALTA
                p.nice(psutil.HIGH_PRIORITY_CLASS)
        except:
            pass

def detect_game_running():
    for p in psutil.process_iter(['name']):
        try:
            if GAME_NAME in p.info['name'].lower():
                return True
        except:
            pass
    return False

# =========================================
# LÓGICA DE BOOST E MONITORAMENTO
# =========================================

def boost(silent=False):
    status_label.config(text="Otimizando Sistema e Rede...")
    root.update()

    set_high_performance()
    optimize_network()
    killed = kill_heavy_processes()
    clean_temp()
    set_game_priority()

    status_label.config(text="BOOST ATIVO 🚀")

    log_box.delete(1.0, tk.END)
    log_box.insert(tk.END, "Processos pesados encerrados:\n")
    if killed:
        for k in killed:
            log_box.insert(tk.END, f"- {k}\n")
    else:
        log_box.insert(tk.END, "- Nenhum processo extra consumindo muita RAM.\n")

    log_box.insert(tk.END, "\nRede (DNS) limpa e Cache esvaziado!")

    if not silent:
        messagebox.showinfo("BOOST", "Sistema e rede otimizados com sucesso!")

def update_loop():
    global auto_boost_applied
    
    # Atualiza Status de Hardware
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    cpu_label.config(text=f"CPU: {cpu}%")
    ram_label.config(text=f"RAM: {ram}%")

    # Lógica do Modo Automático
    if auto_mode.get():
        game_running = detect_game_running()
        
        if game_running and not auto_boost_applied:
            status_label.config(text="Jogo detectado 🎮 - Aplicando Boost...")
            boost(silent=True) # Boost silencioso sem popup
            auto_boost_applied = True
            
        elif not game_running and auto_boost_applied:
            # Reseta o estado quando o jogo é fechado
            status_label.config(text="Aguardando jogo...")
            auto_boost_applied = False

    # Chama essa mesma função novamente após 2000 milissegundos (2 segundos)
    root.after(2000, update_loop)

# =========================================
# UI (INTERFACE)
# =========================================

root = tk.Tk()
root.title("Game Booster PRO V2.1")
root.geometry("500x480")
root.configure(bg="#0f172a")

# Aviso de Administrador
if not is_admin():
    messagebox.showwarning("Atenção", "Execute este programa como Administrador para que todas as funções operem corretamente (Prioridade e Processos).")

title = tk.Label(root, text="GAME BOOSTER PRO", font=("Arial", 20, "bold"), fg="#22c55e", bg="#0f172a")
title.pack(pady=10)

status_label = tk.Label(root, text="Pronto para otimizar", fg="white", bg="#0f172a", font=("Arial", 10, "italic"))
status_label.pack(pady=5)

# Container de Monitoramento
monitor_frame = tk.Frame(root, bg="#1e293b", padx=20, pady=10)
monitor_frame.pack(pady=10)

cpu_label = tk.Label(monitor_frame, text="CPU: 0%", fg="#38bdf8", bg="#1e293b", font=("Arial", 12, "bold"))
cpu_label.pack(side="left", padx=10)

ram_label = tk.Label(monitor_frame, text="RAM: 0%", fg="#fbbf24", bg="#1e293b", font=("Arial", 12, "bold"))
ram_label.pack(side="left", padx=10)

boost_btn = tk.Button(root, text="🚀 BOOST FPS & REDE", font=("Arial", 14, "bold"), bg="#22c55e", fg="black", cursor="hand2", command=lambda: boost(silent=False))
boost_btn.pack(pady=10)

auto_mode = tk.BooleanVar()
auto_check = tk.Checkbutton(root, text="Modo Inteligente Automático (Sem Popups)", variable=auto_mode, fg="white", bg="#0f172a", selectcolor="#0f172a", activebackground="#0f172a", activeforeground="white")
auto_check.pack()

log_box = tk.Text(root, height=8, bg="#020617", fg="#22c55e", font=("Consolas", 9))
log_box.pack(pady=10, padx=20, fill="both")

footer = tk.Label(root, text="by Renan - PRO V2.1", fg="#64748b", bg="#0f172a")
footer.pack(side="bottom", pady=5)

# Inicia o loop seguro do Tkinter
root.after(1000, update_loop)

root.mainloop()