# inicio.py — Tela inicial Flet com logo dinâmica e execução de main.py
"""
Tela de início com botões de ação e logs em tempo real
"""
import flet as ft
import os
import subprocess
import threading
from utils import resource_path


def criar_tela_inicio(page: ft.Page, file_picker: ft.FilePicker, is_dark: list):
    """Cria a tela inicial com logo e botões"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    # Logo
    logo_path = resource_path("data/logo.png" if is_dark[0] else "data/logo2.png")
    
    # Status label para logs
    status_text = ft.Text("", size=12, color=get_text_color())
    log_container = ft.Container(
        content=ft.Column([status_text], scroll=ft.ScrollMode.AUTO),
        height=200,
        bgcolor=get_surface(),
        border_radius=8,
        padding=10,
        visible=False,
    )
    
    def abrir_link(e):
        import webbrowser
        webbrowser.open_new_tab("https://docs.google.com/spreadsheets/d/1wdrOwKS0rqviNHsQsQQg80zf8eShVb7eIjHDXjMVY7s/edit?gid=0#gid=0")
    
    def atualizar_netshoes(e):
        import sys
        
        status_text.value = "Iniciando atualização da Netshoes..."
        log_container.visible = True
        page.update()
        
        def executar():
            try:
                # Verificar se estamos rodando como exe
                if getattr(sys, 'frozen', False):
                    # Executando como exe - importar e rodar diretamente
                    import importlib.util
                    caminho_script = resource_path("main.py")
                    
                    if not os.path.exists(caminho_script):
                        status_text.value = f"[ERRO] main.py não encontrado em: {caminho_script}"
                        page.update()
                        return
                    
                    status_text.value = "Carregando módulo main.py..."
                    page.update()
                    
                    # Carregar o módulo
                    spec = importlib.util.spec_from_file_location("main_scraper", caminho_script)
                    main_module = importlib.util.module_from_spec(spec)
                    
                    try:
                        # Redirecionar stdout/stderr para evitar erro NoneType
                        import io
                        original_stdout = sys.stdout
                        original_stderr = sys.stderr
                        
                        # Se stdout for None (comum em exe), criar um buffer
                        if sys.stdout is None:
                            sys.stdout = io.StringIO()
                        if sys.stderr is None:
                            sys.stderr = io.StringIO()
                        
                        # Carregar o módulo (importar funções e classes)
                        spec.loader.exec_module(main_module)
                        
                        status_text.value = "Executando atualização (isso pode levar vários minutos)...\nAguarde, não feche o aplicativo."
                        page.update()
                        
                        # Chamar a função main() explicitamente com asyncio
                        import asyncio
                        asyncio.run(main_module.main())
                        
                        # Restaurar stdout/stderr
                        sys.stdout = original_stdout if original_stdout else sys.stdout
                        sys.stderr = original_stderr if original_stderr else sys.stderr
                        
                        status_text.value = "✅ Atualização concluída com sucesso!"
                        
                    except Exception as ex:
                        # Restaurar stdout/stderr em caso de erro
                        if 'original_stdout' in locals() and original_stdout:
                            sys.stdout = original_stdout
                        if 'original_stderr' in locals() and original_stderr:
                            sys.stderr = original_stderr
                        status_text.value = f"❌ Erro ao executar: {ex}"
                    
                else:
                    # Executando como script - usar subprocess normal
                    caminho_script = resource_path("main.py")
                    
                    if not os.path.exists(caminho_script):
                        status_text.value = f"[ERRO] main.py não encontrado em: {caminho_script}"
                        page.update()
                        return
                    
                    processo = subprocess.Popen(
                        [sys.executable, "-u", caminho_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        bufsize=1
                    )
                    
                    logs = []
                    for linha in processo.stdout:
                        linha = linha.strip()
                        if not linha:
                            continue
                        print(linha)
                        logs.append(linha)
                        if len(logs) > 20:
                            logs = logs[-20:]
                        status_text.value = "\n".join(logs)
                        page.update()
                    
                    processo.wait()
                    if processo.returncode == 0:
                        status_text.value += "\n\n✅ Atualização concluída com sucesso!"
                    else:
                        status_text.value += f"\n\n❌ Erro na execução (código {processo.returncode})"
                
                page.update()
                
            except Exception as ex:
                status_text.value = f"❌ Erro: {ex}"
                page.update()
        
        threading.Thread(target=executar, daemon=True).start()
    
    def abrir_alteracao_planilha(e):
        try:
            import alteracao
            alteracao.abrir_janela_alteracao()
        except Exception as ex:
            status_text.value = f"Erro ao abrir alterador: {ex}"
            log_container.visible = True
            page.update()
    
    return ft.Container(
        content=ft.Column([
            ft.Container(height=20),
            ft.Text(
                "Bem-vindo",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=get_text_color(),
            ),
            ft.Container(height=20),
            
            # Logo
            ft.Container(
                content=ft.Image(
                    src=logo_path,
                    width=250,
                    height=250,
                    fit=ft.ImageFit.CONTAIN,
                ) if os.path.exists(logo_path) else ft.Icon(
                    ft.Icons.SPORTS_SOCCER,
                    size=150,
                    color=get_text_color(),
                ),
                alignment=ft.alignment.center,
            ),
            
            ft.Container(height=20),
            ft.Text(
                "Selecione uma opção no menu lateral para começar.",
                size=14,
                color=get_text_color(),
                opacity=0.7,
            ),
            
            ft.Container(height=20),
            
            # Botões de ação
            ft.Row([
                ft.ElevatedButton(
                    "🔄 Atualizar Netshoes",
                    on_click=atualizar_netshoes,
                    bgcolor="#3B82F6",
                    color="#FFFFFF",
                    height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            
            ft.Container(height=20),
            
            # Container de logs
            log_container,
            
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        padding=20,
    )
