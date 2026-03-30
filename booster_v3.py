# =========================================
# GAME BOOSTER PRO V3 - VISUAL GAMER
# =========================================
import customtkinter as ctk
from tkinter import messagebox
import psutil
import subprocess
import os
import ctypes
import GPUtil

GAME_NAME = "valorant"
WHITELIST = [
    "vgc.exe", "vgtray.exe", "explorer.exe", "dwm.exe", "svchost.exe", 
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", 
    "services.exe", "lsass.exe", "discord.exe", "taskmgr.exe"
]
auto_boost_applied = False

# --- CONFIGURAÇÃO DO VISUAL MODERNO ---
ctk.set_appearance_mode("dark")  # Modo escuro nativo
ctk.set_default_color_theme("green")  # Tema verde hacker/gamer

# =========================================
# FUNÇÕES DO SISTEMA (MANTIDAS DA V2)
# =========================================
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def set_high_performance():
    subprocess.run("powercfg /setactive SCHEME_MIN", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

def optimize_network():
    subprocess.run("ipconfig /flushdns", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

def clean_temp():
    temp = os.getenv('TEMP')
    if not temp: return
    for file in os.listdir(temp):
        try: os.remove(os.path.join(temp, file))
        except: pass

def kill_heavy_processes():
    killed = []
    for p in psutil.process_iter(['name', 'memory_percent']):
        try:
            name = p.info['name'].lower()
            mem = p.info['memory_percent']
            if mem > 5 and GAME_NAME not in name and name not in WHITELIST:
                killed.append(name)
                p.kill()
        except: pass
    return killed

def set_game_priority():
    for p in psutil.process_iter(['name']):
        try:
            if GAME_NAME in p.info['name'].lower():
                p.nice(psutil.HIGH_PRIORITY_CLASS)
        except: pass

def detect_game_running():
    for p in psutil.process_iter(['name']):
        try:
            if GAME_NAME in p.info['name'].lower(): return True
        except: pass
    return False

# =========================================
# NOVOS MONITORES (PING E GPU)
# =========================================
def get_ping():
    try:
        # Dá um ping no servidor DNS do Google
        output = subprocess.check_output("ping 8.8.8.8 -n 1", shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if "tempo=" in output: return output.split("tempo=")[1].split("ms")[0] + " ms"
        elif "time=" in output: return output.split("time=")[1].split("ms")[0] + " ms"
        return "--"
    except:
        return "Erro"

def get_gpu_stats():
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            return f"Uso: {gpus[0].load * 100:.0f}% | Temp: {gpus[0].temperature}°C"
        return "N/A"
    except:
        return "N/A"

# =========================================
# LÓGICA DE INTERFACE E BOOST
# =========================================
def boost(silent=False):
    status_label.configure(text="⚡ Otimizando Sistema e Rede...", text_color="#fbbf24")
    app.update()

    set_high_performance()
    optimize_network()
    killed = kill_heavy_processes()
    clean_temp()
    set_game_priority()

    status_label.configure(text="🚀 BOOST ATIVO", text_color="#22c55e")

    log_box.delete("1.0", ctk.END)
    log_box.insert(ctk.END, "[ SISTEMA OTIMIZADO ]\n")
    if killed:
        log_box.insert(ctk.END, f"💀 {len(killed)} Processos pesados encerrados:\n")
        for k in killed:
            log_box.insert(ctk.END, f"  - {k}\n")
    else:
        log_box.insert(ctk.END, "✅ Nenhum processo extra pesando na RAM.\n")
    
    log_box.insert(ctk.END, "🌐 Cache de rede limpo (DNS Flush).")

    if not silent:
        messagebox.showinfo("BOOST", "Sistema e rede otimizados com sucesso!")

def update_loop():
    global auto_boost_applied
    
    # Atualiza Hardware
    cpu_val.configure(text=f"{psutil.cpu_percent()}%")
    ram_val.configure(text=f"{psutil.virtual_memory().percent}%")
    gpu_val.configure(text=get_gpu_stats())
    ping_val.configure(text=get_ping())

    # Lógica Automática
    if auto_mode.get():
        game_running = detect_game_running()
        if game_running and not auto_boost_applied:
            status_label.configure(text="🎮 Jogo detectado - Aplicando Boost...", text_color="#38bdf8")
            boost(silent=True)
            auto_boost_applied = True
        elif not game_running and auto_boost_applied:
            status_label.configure(text="Aguardando jogo...", text_color="white")
            auto_boost_applied = False

    app.after(2000, update_loop)

# =========================================
# UI (CUSTOM TKINTER)
# =========================================
app = ctk.CTk()
app.title("Game Booster PRO V3")
app.geometry("550x550")
app.resizable(False, False)

if not is_admin():
    messagebox.showwarning("Atenção", "Execute como Administrador para otimização completa!")

# Título
title = ctk.CTkLabel(app, text="GAME BOOSTER PRO", font=("Arial", 24, "bold"), text_color="#22c55e")
title.pack(pady=(20, 5))

status_label = ctk.CTkLabel(app, text="Aguardando comando...", font=("Arial", 14, "italic"), text_color="gray")
status_label.pack(pady=(0, 15))

# Painel de Status (Grid)
stats_frame = ctk.CTkFrame(app, fg_color="#1e293b", corner_radius=15)
stats_frame.pack(pady=10, padx=20, fill="x")

# Linha 1: CPU e RAM
ctk.CTkLabel(stats_frame, text="💻 CPU:", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=20, pady=10, sticky="w")
cpu_val = ctk.CTkLabel(stats_frame, text="0%", font=("Arial", 14), text_color="#38bdf8")
cpu_val.grid(row=0, column=1, padx=10, pady=10, sticky="w")

ctk.CTkLabel(stats_frame, text="🧠 RAM:", font=("Arial", 14, "bold")).grid(row=0, column=2, padx=20, pady=10, sticky="w")
ram_val = ctk.CTkLabel(stats_frame, text="0%", font=("Arial", 14), text_color="#fbbf24")
ram_val.grid(row=0, column=3, padx=10, pady=10, sticky="w")

# Linha 2: GPU e PING
ctk.CTkLabel(stats_frame, text="🎮 GPU:", font=("Arial", 14, "bold")).grid(row=1, column=0, padx=20, pady=10, sticky="w")
gpu_val = ctk.CTkLabel(stats_frame, text="Lendo...", font=("Arial", 14), text_color="#f87171")
gpu_val.grid(row=1, column=1, padx=10, pady=10, sticky="w")

ctk.CTkLabel(stats_frame, text="🌐 PING:", font=("Arial", 14, "bold")).grid(row=1, column=2, padx=20, pady=10, sticky="w")
ping_val = ctk.CTkLabel(stats_frame, text="Lendo...", font=("Arial", 14), text_color="#a855f7")
ping_val.grid(row=1, column=3, padx=10, pady=10, sticky="w")

# Botão Principal
boost_btn = ctk.CTkButton(app, text="🚀 INICIAR BOOST", font=("Arial", 16, "bold"), height=45, corner_radius=10, command=lambda: boost(silent=False))
boost_btn.pack(pady=15)

# Modo Automático
auto_mode = ctk.BooleanVar()
auto_check = ctk.CTkSwitch(app, text="Modo Inteligente Automático", variable=auto_mode, font=("Arial", 12))
auto_check.pack(pady=5)

# Log do Sistema
log_box = ctk.CTkTextbox(app, height=120, fg_color="#020617", text_color="#22c55e", font=("Consolas", 12), corner_radius=10)
log_box.pack(pady=15, padx=20, fill="both")
log_box.insert(ctk.END, "> Sistema pronto. Aguardando inicialização...\n")

app.after(1000, update_loop)
app.mainloop()

# =========================================
# MODO OVERLAY (SEMPRE NO TOPO)
# =========================================
def toggle_overlay():
    app.attributes('-topmost', overlay_mode.get())

overlay_mode = ctk.BooleanVar()
overlay_switch = ctk.CTkSwitch(app, text="Modo Overlay (Sempre no Topo)", variable=overlay_mode, font=("Arial", 12), command=toggle_overlay)
overlay_switch.pack(pady=5)

app.after(1000, update_loop)
app.mainloop()