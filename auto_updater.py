# auto_updater.py - Sistema de auto-atualização via GitHub Releases
"""
Verifica atualizações no GitHub e baixa nova versão automaticamente.
Repositório: https://github.com/samuelCriap/centralbuybox
"""
import os
import sys
import json
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# Versão atual da aplicação
CURRENT_VERSION = "2.1.0"

# Configurações do GitHub
GITHUB_REPO = "samuelCriap/centralbuybox"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
VERSION_CHECK_INTERVAL = 3600  # Verificar a cada 1 hora (em segundos)


def get_current_version():
    """Retorna a versão atual da aplicação"""
    return CURRENT_VERSION


def parse_version(version_str):
    """Converte string de versão para tupla comparável"""
    try:
        # Remove 'v' se existir
        v = version_str.strip().lower().lstrip('v')
        parts = v.split('.')
        return tuple(int(p) for p in parts)
    except:
        return (0, 0, 0)


def check_for_updates():
    """
    Verifica se há atualização disponível no GitHub.
    Retorna: (tem_atualizacao, info_versao) ou (False, None) se erro
    """
    try:
        import urllib.request
        import ssl
        
        # Criar contexto SSL que ignora verificação (para evitar problemas de certificado)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'CentralBuyBox-Updater'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        latest_version = data.get('tag_name', '0.0.0')
        release_notes = data.get('body', '')
        published_at = data.get('published_at', '')
        
        # Procurar asset do tipo .exe
        download_url = None
        for asset in data.get('assets', []):
            if asset['name'].endswith('.exe'):
                download_url = asset['browser_download_url']
                break
        
        # Comparar versões
        current = parse_version(CURRENT_VERSION)
        latest = parse_version(latest_version)
        
        if latest > current:
            return True, {
                'version': latest_version,
                'current_version': CURRENT_VERSION,
                'release_notes': release_notes,
                'published_at': published_at,
                'download_url': download_url,
            }
        
        return False, None
        
    except Exception as e:
        print(f"[UPDATE] Erro ao verificar atualizações: {e}")
        return False, None


def download_update(download_url, progress_callback=None):
    """
    Baixa a atualização do GitHub.
    progress_callback(bytes_baixados, total_bytes) para atualizar UI
    Retorna: caminho do arquivo baixado ou None se erro
    """
    try:
        import urllib.request
        import ssl
        
        if not download_url:
            return None
        
        # Criar contexto SSL
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            download_url,
            headers={'User-Agent': 'CentralBuyBox-Updater'}
        )
        
        # Pasta de downloads temporária
        temp_dir = Path(os.environ.get('TEMP', '.')) / 'CentralBuyBox_Updates'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        download_path = temp_dir / 'CentralBuyBox_new.exe'
        
        with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                while True:
                    chunk = response.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        
        return str(download_path)
        
    except Exception as e:
        print(f"[UPDATE] Erro ao baixar atualização: {e}")
        return None


def apply_update(new_exe_path):
    """
    Aplica a atualização substituindo o executável atual.
    Cria um script batch para fazer a substituição após o app fechar.
    """
    try:
        if not new_exe_path or not os.path.exists(new_exe_path):
            return False
        
        # Pegar caminho do executável atual
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            # Em desenvolvimento, não fazer nada
            print("[UPDATE] Modo desenvolvimento - atualização simulada")
            return True
        
        # Criar script batch para substituição
        temp_dir = Path(os.environ.get('TEMP', '.'))
        update_script = temp_dir / 'update_centralbuybox.bat'
        
        script_content = f'''@echo off
echo Atualizando Central BuyBox...
timeout /t 2 /nobreak > nul
copy /Y "{new_exe_path}" "{current_exe}"
del /Q "{new_exe_path}"
start "" "{current_exe}"
del "%~f0"
'''
        
        with open(update_script, 'w') as f:
            f.write(script_content)
        
        # Executar script e fechar app
        subprocess.Popen(
            ['cmd', '/c', str(update_script)],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        return True
        
    except Exception as e:
        print(f"[UPDATE] Erro ao aplicar atualização: {e}")
        return False


# ============================================================
# Interface Flet para diálogo de atualização
# ============================================================

def criar_dialogo_atualizacao(page, info_versao, on_update_accepted, on_update_declined):
    """Cria diálogo de atualização com Flet"""
    import flet as ft
    
    def fechar_dialogo(e):
        dialog.open = False
        page.update()
        on_update_declined()
    
    def iniciar_atualizacao(e):
        dialog.open = False
        page.update()
        on_update_accepted(info_versao)
    
    release_notes = info_versao.get('release_notes', 'Melhorias e correções.')
    # Limitar notas a 500 caracteres
    if len(release_notes) > 500:
        release_notes = release_notes[:500] + "..."
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.SYSTEM_UPDATE, color="#3B82F6"),
            ft.Text("Nova Atualização Disponível!", weight=ft.FontWeight.BOLD),
        ]),
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Versão atual:", opacity=0.7),
                    ft.Text(info_versao.get('current_version', '?'), weight=ft.FontWeight.BOLD),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=16),
                    ft.Text(info_versao.get('version', '?'), weight=ft.FontWeight.BOLD, color="#22C55E"),
                ], spacing=8),
                ft.Container(height=10),
                ft.Text("Novidades:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(release_notes, size=12),
                    bgcolor="#F5F5F5",
                    padding=10,
                    border_radius=5,
                    height=150,
                ),
            ], spacing=5),
            width=400,
        ),
        actions=[
            ft.TextButton("Depois", on_click=fechar_dialogo),
            ft.ElevatedButton(
                "Atualizar Agora",
                icon=ft.Icons.DOWNLOAD,
                on_click=iniciar_atualizacao,
                bgcolor="#22C55E",
                color="#FFFFFF",
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    return dialog


def criar_dialogo_progresso(page):
    """Cria diálogo de progresso de download"""
    import flet as ft
    
    progress_bar = ft.ProgressBar(width=350, value=0)
    progress_text = ft.Text("Baixando atualização...", size=12)
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.ProgressRing(width=20, height=20, stroke_width=2),
            ft.Text("Baixando Atualização", weight=ft.FontWeight.BOLD),
        ], spacing=10),
        content=ft.Container(
            content=ft.Column([
                progress_text,
                ft.Container(height=10),
                progress_bar,
            ], spacing=5),
            width=400,
        ),
    )
    
    return dialog, progress_bar, progress_text


def verificar_atualizacao_async(page, is_dark, silencioso=True):
    """
    Verifica atualizações em background.
    silencioso=True: só mostra diálogo se houver atualização
    silencioso=False: mostra mensagem mesmo se estiver atualizado
    """
    import flet as ft
    
    def check_and_notify():
        tem_atualizacao, info = check_for_updates()
        
        if tem_atualizacao and info:
            # Há atualização disponível
            def on_update_accepted(info_versao):
                # Mostrar progresso
                dialog_prog, progress_bar, progress_text = criar_dialogo_progresso(page)
                page.overlay.append(dialog_prog)
                dialog_prog.open = True
                page.update()
                
                def update_progress(downloaded, total):
                    if total > 0:
                        pct = downloaded / total
                        progress_bar.value = pct
                        mb_down = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        progress_text.value = f"Baixando: {mb_down:.1f} MB / {mb_total:.1f} MB"
                        page.update()
                
                # Baixar em thread separada
                def do_download():
                    path = download_update(info_versao.get('download_url'), update_progress)
                    
                    if path:
                        progress_text.value = "Aplicando atualização..."
                        page.update()
                        
                        if apply_update(path):
                            dialog_prog.open = False
                            page.update()
                            # Fechar app para aplicar atualização
                            page.window.close()
                        else:
                            progress_text.value = "Erro ao aplicar atualização"
                            page.update()
                    else:
                        progress_text.value = "Erro ao baixar atualização"
                        page.update()
                
                threading.Thread(target=do_download, daemon=True).start()
            
            def on_update_declined():
                pass  # Usuário escolheu "Depois"
            
            # Mostrar diálogo de atualização
            dialog = criar_dialogo_atualizacao(page, info, on_update_accepted, on_update_declined)
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
            
        elif not silencioso:
            # Mostrar que está atualizado
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Você está usando a versão mais recente ({CURRENT_VERSION})"),
                bgcolor="#22C55E",
            )
            page.snack_bar.open = True
            page.update()
    
    # Executar em thread separada para não travar a UI
    threading.Thread(target=check_and_notify, daemon=True).start()
