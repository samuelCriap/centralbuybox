# app_principal.py — Interface principal Flet com menu lateral moderno
"""
Central do Comercial — Versão Flet
Design Moderno: Menu Gradiente Expansível, Splash Animado
"""
import flet as ft
import os
import time
import threading
from typing import Optional

# Importação das telas
from inicio import criar_tela_inicio
from configuracoes import criar_tela_configuracoes, carregar_tema
from netshoes_dashboard import criar_tela_dashboard
from analises_avancadas import criar_tela_analises
from relatorios import criar_tela_relatorios
from tela_relatorio_ia import criar_tela_relatorio_ia  # Nova importação
from usuarios_admin import criar_tela_usuarios # Importacao nova
from login import criar_login, verificar_login
from tela_servidor import criar_tela_servidor  # Configuração de servidor
from network_config import get_current_mode, get_network_info  # Info de rede
from notificacoes import mostrar_notificacao_com_timeout  # Notificações de update
from auto_updater import verificar_atualizacao_async, get_current_version  # Auto-atualização

def main(page: ft.Page):
    page.title = "Central do Comercial — Netshoes"
    page.padding = 0
    page.spacing = 0
    
    # Carregar tema salvo (mas sempre inicia em modo claro)
    tema_salvo = carregar_tema()
    # Login e Splash sempre em modo claro - tema só aplica no app principal
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.window.width = 1200
    page.window.height = 800
    page.window.center()
    
    # Estado global
    usuario_logado = [{"username": None, "role": None}]
    pagina_atual = [0]
    menu_expandido = [False]
    is_dark = [False]  # Sempre inicia em modo claro
    auto_refresh_active = [False]  # Controle do auto-refresh
    refresh_interval = 600  # 10 minutos entre cada refresh
    
    # FilePicker para uso nas telas
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    
    # ══════════════════════════════════════════════════════════════
    # CORES E TEMA
    # ══════════════════════════════════════════════════════════════
    def get_bg():
        return "#1E1E1E" if is_dark[0] else "#FFFFFF"
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    # ══════════════════════════════════════════════════════════════
    # SPLASH SCREEN - Animado
    # ══════════════════════════════════════════════════════════════
    def mostrar_splash(dados_usuario):
        usuario_logado[0] = dados_usuario # Guardar dados do usuario
        
        page.window.width = 1000
        page.window.height = 700
        page.window.center()
        page.clean()
        
        # Texto animado (entra da direita)
        texto_titulo = ft.Container(
            content=ft.Stack([
                # Sombra
                ft.Text(
                    "Central BuyBox", 
                    size=90, 
                    weight=ft.FontWeight.BOLD, 
                    color=ft.Colors.with_opacity(0.3, "#FFFFFF"),
                    font_family="Georgia",
                ),
                # Texto principal
                ft.Container(
                    content=ft.Text(
                        "Central BuyBox", 
                        size=90, 
                        weight=ft.FontWeight.BOLD, 
                        color="#000000",
                        font_family="Georgia",
                    ),
                    left=2,
                    top=2,
                ),
            ]),
            offset=ft.Offset(2, 0),
            animate_offset=ft.Animation(1200, ft.AnimationCurve.EASE_OUT_CUBIC),
        )
        
        texto_bemvindo = ft.Container(
            content=ft.Text(
                f"Bem-vindo, {dados_usuario.get('username', '')}!", 
                size=22, 
                weight=ft.FontWeight.W_400, 
                color="#000000",
                opacity=0.9,
            ),
            opacity=0,
            animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_OUT),
        )
        
        splash = ft.Container(
            content=ft.Column([
                texto_titulo,
                ft.Container(height=45),
                texto_bemvindo,
                ft.Text(f"Perfil: {dados_usuario.get('role', 'user').upper()}", color="grey", size=12)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
               alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#FF6B35", "#F7931E", "#16A34A", "#0D9488", "#1F2937", "#111827"],
            ),
        )
        
        page.add(splash)
        page.update()
        
        # Animação: texto entra
        time.sleep(0.1)
        texto_titulo.offset = ft.Offset(0, 0)
        page.update()
        
        # Animação: bem-vindo aparece
        time.sleep(1.2)
        texto_bemvindo.opacity = 1
        page.update()
        
        time.sleep(2.0)
        abrir_app()
        
        # Mostrar notificação de atualização após app abrir
        def mostrar_notificacao_delayed():
            time.sleep(1.0)  # Aguardar app carregar
            mostrar_notificacao_com_timeout(page, is_dark, timeout_segundos=10)
        
        threading.Thread(target=mostrar_notificacao_delayed, daemon=True).start()
        
        # Verificar atualizações do GitHub em background
        def verificar_updates_delayed():
            time.sleep(3.0)  # Aguardar app e notificação
            verificar_atualizacao_async(page, is_dark, silencioso=True)
        
        threading.Thread(target=verificar_updates_delayed, daemon=True).start()
    
    # ══════════════════════════════════════════════════════════════
    # APP PRINCIPAL
    # ══════════════════════════════════════════════════════════════
    def abrir_app():
        page.window.maximized = True
        page.clean()
        page.bgcolor = get_bg()
        
        conteudo = ft.Container(expand=True, padding=20, bgcolor=get_bg())
        
        # Definir cargos e permissões
        user_role = usuario_logado[0].get("role", "user")
        is_master = user_role == "master"  # Super admin - acesso total
        is_admin = user_role == "admin"    # Admin - gerencia usuários, mas não vê Início
        is_regular = user_role == "user"   # Usuário normal - sem acesso a Início e Usuários
        
        # Página inicial baseada no cargo
        if is_master:
            pagina_atual[0] = 0  # Master começa no Início
        else:
            pagina_atual[0] = 1  # Outros começam no Dashboard
        
        def nav(idx):
            pagina_atual[0] = idx
            if idx == 0 and is_master:  # Apenas Master vê Início
                conteudo.content = criar_tela_inicio(page, file_picker, is_dark)
            elif idx == 1:
                conteudo.content = criar_tela_dashboard(page, is_dark)
            elif idx == 2:
                conteudo.content = criar_tela_analises(page, is_dark)
            elif idx == 3:
                conteudo.content = criar_tela_relatorios(page, file_picker, is_dark)
            elif idx == 4:
                conteudo.content = criar_tela_relatorio_ia(page, is_dark)
            elif idx == 5:
                conteudo.content = criar_tela_configuracoes(page, is_dark, toggle_theme)
            elif idx == 6 and (is_master or is_admin):  # Master e Admin veem Usuários
                conteudo.content = criar_tela_usuarios(page, is_dark, is_master)
            atualizar_menu()
            page.update()
        
        def toggle_theme(e=None):
            is_dark[0] = not is_dark[0]
            page.theme_mode = ft.ThemeMode.DARK if is_dark[0] else ft.ThemeMode.LIGHT
            page.bgcolor = get_bg()
            conteudo.bgcolor = get_bg()
            
            # Atualizar cor do rodapé
            rodape.content.color = get_text_color()
            rodape.bgcolor = get_bg()  # Atualizar fundo do rodapé
            
            nav(pagina_atual[0])
            page.update()
        
        # Auto-refresh desabilitado temporariamente para evitar travamentos
        # Para reativar, descomente as linhas abaixo
        # def auto_refresh_loop():
        #     while auto_refresh_active[0]:
        #         time.sleep(refresh_interval)
        #         if auto_refresh_active[0]:
        #             try:
        #                 nav(pagina_atual[0])
        #                 page.update()
        #             except:
        #                 pass
        # 
        # def iniciar_auto_refresh():
        #     auto_refresh_active[0] = True
        #     refresh_thread = threading.Thread(target=auto_refresh_loop, daemon=True)
        #     refresh_thread.start()
        # 
        # iniciar_auto_refresh()
        
        def criar_menu_item(icone, texto, idx):
            ativo = pagina_atual[0] == idx
            cor_item = "#FFFFFF" if ativo else "#E0E0E0"
            bg_ativo = "#16A34A" if ativo else ft.Colors.TRANSPARENT
            
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icone, size=22, color=cor_item),
                    ft.AnimatedSwitcher(
                        content=ft.Text(texto, size=13, color=cor_item, weight=ft.FontWeight.W_500) if menu_expandido[0] else ft.Container(),
                        duration=200, 
                        transition=ft.AnimatedSwitcherTransition.FADE,
                    ),
                ], spacing=15),
                padding=12,
                bgcolor=bg_ativo,
                border_radius=10,
                on_click=lambda e, i=idx: nav(i),
                ink=True,
                tooltip=texto if not menu_expandido[0] else None,
            )
        
        menu_items = []
        
        def atualizar_menu():
            nonlocal menu_items
            menu_items.clear()
            
            # Construção condicional do menu baseada no cargo
            if is_master:  # Apenas Master vê Início
                menu_items.append(criar_menu_item(ft.Icons.HOME, "Início", 0))
                
            menu_items.append(criar_menu_item(ft.Icons.SHOPPING_CART, "Netshoes", 1))
            menu_items.append(criar_menu_item(ft.Icons.ANALYTICS, "Análises", 2))
            menu_items.append(criar_menu_item(ft.Icons.DESCRIPTION, "Relatórios", 3))
            menu_items.append(criar_menu_item(ft.Icons.AUTO_AWESOME, "Oportunidades IA", 4))
            menu_items.append(criar_menu_item(ft.Icons.SETTINGS, "Configurações", 5))
            
            if is_master or is_admin:  # Master e Admin veem Usuários
                menu_items.append(criar_menu_item(ft.Icons.PEOPLE, "Usuários", 6))
            
            menu_col.controls = [
                ft.Container(height=30),
                ft.Container(
                    content=ft.Icon(ft.Icons.SPORTS_SOCCER, size=32, color="#FFFFFF"), 
                    padding=15
                ),
                ft.Container(height=30),
                *menu_items,
                ft.Container(expand=True),
                # Indicador de usuário online
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                width=10, 
                                height=10, 
                                bgcolor="#22C55E",  # Verde
                                border_radius=5,  # Bolinha
                            ),
                            ft.AnimatedSwitcher(
                                content=ft.Text(
                                    usuario_logado[0].get("username", "")[:12], 
                                    size=11, 
                                    color="#FFFFFF",
                                    weight=ft.FontWeight.W_500,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ) if menu_expandido[0] else ft.Container(),
                                duration=200,
                                transition=ft.AnimatedSwitcherTransition.FADE,
                            ),
                        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                        ft.AnimatedSwitcher(
                            content=ft.Text(
                                "Online", 
                                size=9, 
                                color="#22C55E",
                                opacity=0.8,
                            ) if menu_expandido[0] else ft.Container(),
                            duration=200,
                            transition=ft.AnimatedSwitcherTransition.FADE,
                        ),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.only(bottom=10),
                ),
                ft.Column([
                    ft.IconButton(
                        ft.Icons.BRIGHTNESS_6, 
                        icon_color="#E0E0E0", 
                        tooltip="Alternar tema", 
                        on_click=toggle_theme
                    ),
                    ft.IconButton(
                        ft.Icons.LOGOUT, 
                        icon_color="#E0E0E0", 
                        tooltip="Sair", 
                        on_click=lambda e: page.window.close()
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=15),
            ]
        
        def on_menu_hover(e):
            menu_expandido[0] = e.data == "true"
            menu_container.width = 200 if menu_expandido[0] else 70
            atualizar_menu()
            page.update()
        
        menu_col = ft.Column([], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        atualizar_menu()
        
        menu_container = ft.Container(
            content=menu_col,
            width=70,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#FF6B35", "#F7931E", "#16A34A", "#0D9488", "#1F2937", "#111827"],
            ),
            padding=ft.padding.symmetric(horizontal=10),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=on_menu_hover,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "#000000")),
        )
        
        # Tela inicial
        if pagina_atual[0] == 0:
            conteudo.content = criar_tela_inicio(page, file_picker, is_dark)
        elif pagina_atual[0] == 1:
            conteudo.content = criar_tela_dashboard(page, is_dark)
            
        # Rodapé
        rodape = ft.Container(
            content=ft.Text(
                f"Desenvolvido por Samuel Rodrigues  v{get_current_version()}",
                size=10,
                color=get_text_color(),
                opacity=0.6,
            ),
            bgcolor=get_bg(),  # Fundo adaptável ao tema
            alignment=ft.alignment.center_right,
            padding=ft.padding.only(right=20, bottom=10),
        )
        
        main_content = ft.Column([
            ft.Container(content=conteudo, expand=True),
            rodape,
        ], expand=True, spacing=0)
        
        page.add(ft.Row([
            menu_container,
            ft.Container(content=main_content, expand=True, bgcolor=get_bg()),
        ], expand=True, spacing=0))
    
    # ══════════════════════════════════════════════════════════════
    # FLUXO: SERVIDOR -> LOGIN -> SPLASH -> APP
    # ══════════════════════════════════════════════════════════════
    
    def mostrar_login():
        """Mostra tela de login"""
        page.clean()
        login_view = criar_login(page, on_login_success)
        page.add(login_view)
    
    def on_servidor_configurado():
        """Callback após configurar servidor"""
        # Mostrar informações de conexão
        info = get_network_info()
        print(f"[INFO] Modo: {info['mode']}")
        print(f"[INFO] Banco de dados: {info['database_path']}")
        
        # Prosseguir para login
        mostrar_login()
    
    def on_login_success(dados_usuario):
        """Callback após login bem-sucedido"""
        mostrar_splash(dados_usuario)
    
    # Verificar se já tem configuração de servidor
    modo_atual = get_current_mode()
    
    # Se for primeira vez ou usuário quiser reconfigurar, mostrar tela de servidor
    # Por enquanto, sempre mostrar login direto (usuário pode configurar depois nas configurações)
    # Para forçar tela de servidor, descomentar a linha abaixo:
    # servidor_view = criar_tela_servidor(page, on_servidor_configurado)
    # page.add(servidor_view)
    
    # Ir direto para login (configuração de servidor opcional)
    mostrar_login()


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # Necessário para PyInstaller
    ft.app(target=main)
