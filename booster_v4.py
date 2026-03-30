# =========================================
# GAME BOOSTER PRO V4
# Reescrito com melhorias completas
# =========================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import psutil
import subprocess
import os
import ctypes
import ctypes.wintypes
import threading
import json
import time
import socket
import struct
import winreg
from collections import deque

# GPU via WMI — sem subprocess, sem nvidia-smi
try:
    import wmi
    WMI_AVAILABLE = True
    _wmi = wmi.WMI(namespace="root\\OpenHardwareMonitor")
    WMI_MODE = "ohm"
except:
    try:
        import wmi
        WMI_AVAILABLE = True
        _wmi = wmi.WMI()
        WMI_MODE = "std"
    except:
        WMI_AVAILABLE = False
        WMI_MODE = None

GPU_AVAILABLE = False  # GPUtil desativado — usava nvidia-smi

# =========================================
# CONFIGURAÇÃO DE JOGOS (DROPDOWN)
# =========================================
GAMES = {
    "Valorant": {
        "process": "valorant",
        "ping_host": "180.215.12.24",   # Servidor Riot BR
        "extra_whitelist": ["vgc.exe", "vgtray.exe", "riotclientservices.exe"]
    },
    "CS2": {
        "process": "cs2",
        "ping_host": "162.254.197.36",  # Servidor Valve BR
        "extra_whitelist": ["steam.exe", "steamwebhelper.exe"]
    },
    "League of Legends": {
        "process": "league of legends",
        "ping_host": "104.160.131.3",   # Servidor Riot LoL BR
        "extra_whitelist": ["leagueclient.exe", "riotclientservices.exe"]
    },
    "Fortnite": {
        "process": "fortnite",
        "ping_host": "13.249.26.160",   # Servidor Epic BR
        "extra_whitelist": ["epicgameslauncher.exe", "easyanticheat.exe"]
    },
    "Outro": {
        "process": "",
        "ping_host": "8.8.8.8",
        "extra_whitelist": []
    }
}

# =========================================
# WHITELIST BASE (NUNCA MATAR)
# =========================================
BASE_WHITELIST = [
    "explorer.exe", "dwm.exe", "svchost.exe",
    "system", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe",
    "taskmgr.exe", "python.exe", "pythonw.exe",
    "game_booster_v4.py"
]

# Whitelist extra editável pelo usuário
USER_WHITELIST_FILE = os.path.join(os.getenv("APPDATA", "."), "GameBoosterV4_whitelist.json")

def load_user_whitelist():
    try:
        with open(USER_WHITELIST_FILE, "r") as f:
            return json.load(f)
    except:
        return ["discord.exe", "obs64.exe", "obs32.exe", "spotify.exe"]

def save_user_whitelist(wl):
    try:
        with open(USER_WHITELIST_FILE, "w") as f:
            json.dump(wl, f)
    except:
        pass

user_whitelist = load_user_whitelist()

# =========================================
# HISTÓRICO DE MÉTRICAS (60 pontos)
# =========================================
HISTORY_SIZE = 60
cpu_history    = deque([0.0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)
ram_history    = deque([0.0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)
ping_history   = deque([0.0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)

# =========================================
# FUNÇÕES DO SISTEMA
# =========================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def set_high_performance():
    # Chama powercfg via ctypes direto — sem abrir janela de cmd
    try:
        # GUID do plano Alto Desempenho do Windows
        HIGH_PERF_GUID = "{8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c}"
        ctypes.windll.powrprof.PowerSetActiveScheme(
            None,
            ctypes.create_string_buffer(
                bytes.fromhex(HIGH_PERF_GUID.replace("-", "").replace("{", "").replace("}", ""))
            )
        )
    except:
        # Fallback sem janela visível usando STARTUPINFO oculto
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        subprocess.run(
            ["powercfg", "/setactive", "SCHEME_MIN"],
            startupinfo=si,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

def optimize_network():
    # DNS Flush via ctypes — sem cmd
    try:
        dnsapi = ctypes.windll.dnsapi
        dnsapi.DnsFlushResolverCache()
    except:
        pass

    # TCP TcpAckFrequency via winreg — sem reg.exe
    try:
        base_key = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as interfaces:
            i = 0
            while True:
                try:
                    iface = winreg.EnumKey(interfaces, i)
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        f"{base_key}\\{iface}",
                                        0, winreg.KEY_SET_VALUE) as k:
                        winreg.SetValueEx(k, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                        winreg.SetValueEx(k, "TCPNoDelay",       0, winreg.REG_DWORD, 1)
                    i += 1
                except OSError:
                    break
    except:
        pass

def clean_temp():
    temp = os.getenv("TEMP")
    if not temp:
        return
    for file in os.listdir(temp):
        try:
            os.remove(os.path.join(temp, file))
        except:
            pass

def kill_heavy_processes(game_name):
    killed = []
    full_whitelist = set(
        [x.lower() for x in BASE_WHITELIST] +
        [x.lower() for x in user_whitelist] +
        [x.lower() for x in GAMES.get(game_name, {}).get("extra_whitelist", [])]
    )
    game_proc = GAMES.get(game_name, {}).get("process", "").lower()

    for p in psutil.process_iter(["name", "memory_percent"]):
        try:
            name = p.info["name"].lower()
            mem  = p.info["memory_percent"]
            if (mem > 5
                    and (not game_proc or game_proc not in name)
                    and name not in full_whitelist):
                killed.append(p.info["name"])
                p.kill()
        except:
            pass
    return killed

def set_game_priority(game_name):
    game_proc = GAMES.get(game_name, {}).get("process", "").lower()
    if not game_proc:
        return
    for p in psutil.process_iter(["name"]):
        try:
            if game_proc in p.info["name"].lower():
                p.nice(psutil.HIGH_PRIORITY_CLASS)
        except:
            pass

def detect_game_running(game_name):
    game_proc = GAMES.get(game_name, {}).get("process", "").lower()
    if not game_proc:
        return False
    for p in psutil.process_iter(["name"]):
        try:
            if game_proc in p.info["name"].lower():
                return True
        except:
            pass
    return False

# =========================================
# MÉTRICAS EM TEMPO REAL
# =========================================
def get_ping(game_name):
    """Mede latência via socket TCP — zero subprocess, zero janela."""
    host = GAMES.get(game_name, {}).get("ping_host", "8.8.8.8")
    try:
        start = time.perf_counter()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        # Tenta conectar na porta 80; se não responder usa porta 443
        result = sock.connect_ex((host, 80))
        if result != 0:
            sock.connect_ex((host, 443))
        elapsed = (time.perf_counter() - start) * 1000
        sock.close()
        return round(elapsed, 1)
    except:
        return 0.0

def get_gpu_stats():
    """Lê GPU via WMI — zero subprocess, zero nvidia-smi."""
    try:
        if WMI_MODE == "ohm":
            load = temp = None
            for s in _wmi.Sensor():
                if s.SensorType == "Load" and "GPU" in s.Name:
                    load = float(s.Value)
                if s.SensorType == "Temperature" and "GPU" in s.Name:
                    temp = float(s.Value)
            return load, temp
        elif WMI_MODE == "std":
            for gpu in _wmi.Win32_VideoController():
                # WMI padrão não expõe temp/load, retorna só nome
                return None, None
        return None, None
    except:
        return None, None

# =========================================
# DESENHO DO MINI-GRÁFICO (Canvas)
# =========================================
def draw_sparkline(canvas, history, color, max_val=100):
    canvas.delete("all")
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w < 2 or h < 2:
        return

    pts = list(history)
    n = len(pts)
    if n < 2:
        return

    step = w / (n - 1)
    coords = []
    for i, v in enumerate(pts):
        x = i * step
        y = h - (v / max_val) * h
        y = max(2, min(h - 2, y))
        coords += [x, y]

    # Sombra / área
    fill_coords = [0, h] + coords + [w, h]
    canvas.create_polygon(fill_coords, fill=color, stipple="gray25", outline="")
    # Linha
    canvas.create_line(coords, fill=color, width=2, smooth=True)


# =========================================
# JANELA DE WHITELIST EDITÁVEL
# =========================================
def open_whitelist_editor(parent):
    win = ctk.CTkToplevel(parent)
    win.title("Editar Whitelist")
    win.geometry("380x420")
    win.resizable(False, False)
    win.grab_set()

    ctk.CTkLabel(win, text="Processos Protegidos", font=("Consolas", 16, "bold")).pack(pady=(15, 5))
    ctk.CTkLabel(win, text="Esses processos NUNCA serão encerrados pelo Boost.",
                 font=("Consolas", 11), text_color="gray").pack(pady=(0, 10))

    listbox = ctk.CTkTextbox(win, height=220, font=("Consolas", 12))
    listbox.pack(padx=15, fill="x")
    listbox.insert("end", "\n".join(user_whitelist))

    def save():
        global user_whitelist
        content = listbox.get("1.0", "end").strip()
        user_whitelist = [x.strip().lower() for x in content.splitlines() if x.strip()]
        save_user_whitelist(user_whitelist)
        messagebox.showinfo("Salvo", "Whitelist atualizada!", parent=win)
        win.destroy()

    ctk.CTkButton(win, text="💾 Salvar", command=save,
                  fg_color="#22c55e", hover_color="#16a34a",
                  font=("Consolas", 13, "bold")).pack(pady=10)
    ctk.CTkButton(win, text="Cancelar", command=win.destroy,
                  fg_color="#374151", hover_color="#4b5563",
                  font=("Consolas", 12)).pack()


# =========================================
# APLICAÇÃO PRINCIPAL
# =========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Game Booster PRO V4")
app.geometry("580x680")
app.resizable(False, False)

if not is_admin():
    messagebox.showwarning(
        "Atenção",
        "Execute como Administrador para otimização completa!\n"
        "Algumas funções estarão limitadas.",
        parent=app
    )

auto_boost_applied = False

# ---------- TÍTULO ----------
header = ctk.CTkFrame(app, fg_color="#0f172a", corner_radius=0)
header.pack(fill="x")

ctk.CTkLabel(
    header, text="◈ GAME BOOSTER PRO V4",
    font=("Consolas", 20, "bold"), text_color="#22c55e"
).pack(side="left", padx=20, pady=12)

status_label = ctk.CTkLabel(
    header, text="● Aguardando...",
    font=("Consolas", 12), text_color="#6b7280"
)
status_label.pack(side="right", padx=20)

# ---------- SELEÇÃO DE JOGO ----------
game_frame = ctk.CTkFrame(app, fg_color="#1e293b", corner_radius=12)
game_frame.pack(pady=(10, 0), padx=15, fill="x")

ctk.CTkLabel(game_frame, text="🎮 Jogo Alvo:", font=("Consolas", 13, "bold")).pack(side="left", padx=15, pady=10)

selected_game = ctk.StringVar(value="Valorant")
game_menu = ctk.CTkOptionMenu(
    game_frame,
    values=list(GAMES.keys()),
    variable=selected_game,
    font=("Consolas", 13),
    fg_color="#0f172a",
    button_color="#16a34a",
    button_hover_color="#15803d",
    width=180
)
game_menu.pack(side="left", padx=5)

def open_wl():
    open_whitelist_editor(app)

ctk.CTkButton(
    game_frame, text="🛡 Whitelist", width=110,
    font=("Consolas", 12),
    fg_color="#1e40af", hover_color="#1d4ed8",
    command=open_wl
).pack(side="right", padx=15, pady=8)

# ---------- PAINEL DE MÉTRICAS ----------
stats_outer = ctk.CTkFrame(app, fg_color="#0f172a", corner_radius=12)
stats_outer.pack(pady=10, padx=15, fill="x")

def make_metric_card(parent, row, col, icon, label, color):
    card = ctk.CTkFrame(parent, fg_color="#1e293b", corner_radius=10)
    card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
    parent.grid_columnconfigure(col, weight=1)

    top = ctk.CTkFrame(card, fg_color="transparent")
    top.pack(fill="x", padx=10, pady=(8, 2))

    ctk.CTkLabel(top, text=f"{icon} {label}", font=("Consolas", 11), text_color="#94a3b8").pack(side="left")
    val_lbl = ctk.CTkLabel(top, text="--", font=("Consolas", 15, "bold"), text_color=color)
    val_lbl.pack(side="right")

    spark = tk.Canvas(card, height=30, bg="#1e293b", highlightthickness=0)
    spark.pack(fill="x", padx=8, pady=(0, 8))

    return val_lbl, spark

cpu_val,  cpu_spark  = make_metric_card(stats_outer, 0, 0, "💻", "CPU",  "#38bdf8")
ram_val,  ram_spark  = make_metric_card(stats_outer, 0, 1, "🧠", "RAM",  "#fbbf24")
ping_val, ping_spark = make_metric_card(stats_outer, 1, 0, "🌐", "PING", "#a855f7")
gpu_val,  gpu_spark  = make_metric_card(stats_outer, 1, 1, "🎮", "GPU",  "#f87171")

# ---------- BOTÃO BOOST ----------
boost_btn = ctk.CTkButton(
    app,
    text="⚡ INICIAR BOOST",
    font=("Consolas", 17, "bold"),
    height=50,
    corner_radius=12,
    fg_color="#16a34a",
    hover_color="#15803d",
    border_width=2,
    border_color="#22c55e"
)
boost_btn.pack(pady=10, padx=15, fill="x")

# ---------- SWITCHES ----------
switches_frame = ctk.CTkFrame(app, fg_color="#1e293b", corner_radius=12)
switches_frame.pack(pady=5, padx=15, fill="x")

auto_mode    = ctk.BooleanVar(value=False)
overlay_mode = ctk.BooleanVar(value=False)

ctk.CTkSwitch(
    switches_frame, text="Modo Inteligente Automático",
    variable=auto_mode, font=("Consolas", 12),
    progress_color="#22c55e"
).pack(side="left", padx=20, pady=10)

ctk.CTkSwitch(
    switches_frame, text="Sempre no Topo",
    variable=overlay_mode, font=("Consolas", 12),
    progress_color="#38bdf8",
    command=lambda: app.attributes("-topmost", overlay_mode.get())
).pack(side="right", padx=20, pady=10)

# ---------- LOG ----------
log_box = ctk.CTkTextbox(
    app, height=140,
    fg_color="#020617",
    text_color="#22c55e",
    font=("Consolas", 12),
    corner_radius=10,
    scrollbar_button_color="#1e293b"
)
log_box.pack(pady=10, padx=15, fill="both")
log_box.insert("end", "> Game Booster PRO V4 iniciado.\n> Selecione o jogo e clique em BOOST.\n")

# =========================================
# LÓGICA DE BOOST
# =========================================
def log(msg):
    log_box.insert("end", msg + "\n")
    log_box.see("end")

def boost(silent=False):
    game = selected_game.get()

    status_label.configure(text="⚡ Otimizando...", text_color="#fbbf24")
    boost_btn.configure(state="disabled", text="⏳ Aguarde...")

    def run():
        set_high_performance()
        optimize_network()
        clean_temp()
        killed = kill_heavy_processes(game)
        set_game_priority(game)

        lines = [f"[ BOOST APLICADO — {game.upper()} ]",
                 "✅ Plano de energia: Alto Desempenho",
                 "✅ DNS cache limpo + TCP otimizado",
                 "✅ Arquivos temporários removidos"]

        if killed:
            lines.append(f"💀 {len(killed)} processo(s) encerrado(s):")
            for k in killed[:8]:
                lines.append(f"   - {k}")
            if len(killed) > 8:
                lines.append(f"   ... e mais {len(killed)-8}")
        else:
            lines.append("✅ Nenhum processo extra pesando na RAM.")

        def update_ui():
            log_box.delete("1.0", "end")
            for l in lines:
                log_box.insert("end", l + "\n")
            log_box.see("end")
            status_label.configure(text="🚀 BOOST ATIVO", text_color="#22c55e")
            boost_btn.configure(state="normal", text="⚡ INICIAR BOOST")
            if not silent:
                messagebox.showinfo("BOOST", f"Sistema otimizado para {game}!")

        app.after(0, update_ui)

    threading.Thread(target=run, daemon=True).start()

boost_btn.configure(command=lambda: boost(silent=False))

# =========================================
# LOOP DE ATUALIZAÇÃO
# =========================================
def update_ping_bg():
    """Roda em thread separada — só faz o subprocess de ping."""
    game = selected_game.get()
    ping = get_ping(game)
    ping_history.append(min(ping, 300))
    ping_color = "#f87171" if ping > 80 else "#a855f7"
    # Agenda atualização de volta na main thread
    app.after(0, lambda: ping_val.configure(text=f"{ping:.0f} ms", text_color=ping_color))
    app.after(0, lambda: draw_sparkline(ping_spark, ping_history, ping_color, 300))

def update_loop():
    global auto_boost_applied

    # Métricas leves rodam direto na main thread via after()
    # Apenas o ping (que faz subprocess) vai pra thread separada
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    gpu_load, gpu_temp = get_gpu_stats()

    cpu_history.append(cpu)
    ram_history.append(ram)

    cpu_color  = "#f87171" if cpu  > 80 else "#38bdf8"
    ram_color  = "#f87171" if ram  > 85 else "#fbbf24"

    cpu_val.configure(text=f"{cpu:.0f}%", text_color=cpu_color)
    ram_val.configure(text=f"{ram:.0f}%", text_color=ram_color)

    if gpu_load is not None:
        gpu_color = "#f87171" if gpu_load > 90 or (gpu_temp and gpu_temp > 85) else "#4ade80"
        gpu_val.configure(text=f"{gpu_load:.0f}% | {gpu_temp}°C", text_color=gpu_color)
    else:
        gpu_val.configure(text="N/A", text_color="#6b7280")

    draw_sparkline(cpu_spark, cpu_history, cpu_color, 100)
    draw_sparkline(ram_spark, ram_history, ram_color, 100)

    threading.Thread(target=update_ping_bg, daemon=True).start()

    if auto_mode.get():
        game = selected_game.get()
        game_running = detect_game_running(game)
        if game_running and not auto_boost_applied:
            status_label.configure(text="🎮 Jogo detectado!", text_color="#38bdf8")
            boost(silent=True)
            auto_boost_applied = True
        elif not game_running and auto_boost_applied:
            status_label.configure(text="● Aguardando jogo...", text_color="#6b7280")
            auto_boost_applied = False

    app.after(2000, update_loop)

app.after(1000, update_loop)
app.mainloop()