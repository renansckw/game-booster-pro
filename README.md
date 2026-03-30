# ⚡ Game Booster PRO V4

App desktop para otimizar FPS e monitorar hardware em tempo real no Windows.

## 🚀 Funcionalidades
- Monitor em tempo real de CPU, RAM, GPU e Ping
- Boost automático ao detectar o jogo
- Whitelist de processos editável
- Suporte a Valorant, CS2, League of Legends e Fortnite
- Ping medido direto no servidor BR do jogo

## 🛠️ Como usar

### Rodando pelo código
pip install -r requirements.txt
python booster_v4.py

### Gerando o .exe
python -m PyInstaller --onedir --windowed --uac-admin --name "GameBoosterV4" booster_v4.py

## 📦 Dependências
- customtkinter
- psutil
- wmi

## ⚠️ Aviso
Execute como Administrador para otimização completa.
