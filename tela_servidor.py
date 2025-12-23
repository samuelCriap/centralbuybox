# tela_servidor.py - Configuração de Servidor de Rede
"""
Interface para configurar conexão local vs rede
"""
import flet as ft
from network_config import (
    load_config, save_config, test_network_connection,
    set_local_mode, set_network_mode, get_network_info
)


def criar_tela_servidor(page: ft.Page, on_success_callback):
    """Cria tela de configuração de servidor"""
    
    config = load_config()
    modo_atual = [config.get("mode", "local")]
    
    # Componentes
    status_text = ft.Text("", size=12)
    
    # Radio buttons para modo
    modo_radio = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="local", label="Localhost (Banco de dados local)"),
            ft.Radio(value="network", label="Rede (Banco de dados compartilhado)"),
        ]),
        value=modo_atual[0],
    )
    
    # Campo de IP/Caminho de rede
    network_input = ft.TextField(
        label="IP do Servidor ou Caminho UNC",
        hint_text="Ex: 192.168.1.100 ou \\\\192.168.1.100\\NetShoes",
        value=config.get("network_ip", "") or config.get("network_path", ""),
        width=400,
        disabled=modo_atual[0] == "local",
    )
    
    share_input = ft.TextField(
        label="Nome do Compartilhamento",
        hint_text="Ex: NetShoes",
        value=config.get("share_name", "NetShoes"),
        width=200,
        disabled=modo_atual[0] == "local",
    )
    
    def on_modo_change(e):
        """Quando o modo muda"""
        modo_atual[0] = modo_radio.value
        network_input.disabled = modo_atual[0] == "local"
        share_input.disabled = modo_atual[0] == "local"
        page.update()
    
    modo_radio.on_change = on_modo_change
    
    def testar_conexao(e):
        """Testa conexão com o servidor de rede"""
        if modo_atual[0] == "local":
            status_text.value = "Modo local não requer teste de conexão"
            status_text.color = "#3B82F6"
            page.update()
            return
        
        ip_or_path = network_input.value.strip()
        
        if not ip_or_path:
            status_text.value = "Digite o IP ou caminho de rede"
            status_text.color = "#EF4444"
            page.update()
            return
        
        status_text.value = "Testando conexão..."
        status_text.color = "#3B82F6"
        page.update()
        
        sucesso, mensagem = test_network_connection(ip_or_path)
        
        status_text.value = mensagem
        status_text.color = "#22C55E" if sucesso else "#EF4444"
        page.update()
    
    def salvar_configuracao(e):
        """Salva configuração e prossegue"""
        if modo_atual[0] == "local":
            set_local_mode()
            status_text.value = "Configuração salva! Modo: Localhost"
            status_text.color = "#22C55E"
        else:
            ip_or_path = network_input.value.strip()
            share_name = share_input.value.strip() or "NetShoes"
            
            if not ip_or_path:
                status_text.value = "Digite o IP ou caminho de rede"
                status_text.color = "#EF4444"
                page.update()
                return
            
            # Testar conexão antes de salvar
            sucesso, mensagem = test_network_connection(ip_or_path)
            
            if not sucesso:
                status_text.value = f"Erro: {mensagem}"
                status_text.color = "#EF4444"
                page.update()
                return
            
            set_network_mode(ip_or_path, share_name)
            status_text.value = f"Configuração salva! Modo: Rede ({ip_or_path})"
            status_text.color = "#22C55E"
        
        page.update()
        
        # Chamar callback de sucesso após 1 segundo
        import time
        time.sleep(1)
        on_success_callback()
    
    # Layout
    return ft.Container(
        content=ft.Column([
            ft.Container(height=40),
            ft.Icon(ft.Icons.STORAGE, size=64, color="#3B82F6"),
            ft.Container(height=20),
            ft.Text(
                "Configuração de Servidor",
                size=28,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Escolha onde o banco de dados está localizado",
                size=14,
                color="#6B7280",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=30),
            
            # Modo
            ft.Container(
                content=modo_radio,
                bgcolor="#F5F5F5",
                padding=20,
                border_radius=10,
            ),
            
            ft.Container(height=20),
            
            # Configuração de rede
            ft.Container(
                content=ft.Column([
                    ft.Text("Configuração de Rede", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    network_input,
                    ft.Container(height=10),
                    share_input,
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        "Testar Conexão",
                        icon=ft.Icons.WIFI_FIND,
                        on_click=testar_conexao,
                        bgcolor="#3B82F6",
                        color="#FFFFFF",
                    ),
                ]),
                bgcolor="#F5F5F5",
                padding=20,
                border_radius=10,
            ),
            
            ft.Container(height=20),
            status_text,
            ft.Container(height=20),
            
            # Botões
            ft.Row([
                ft.ElevatedButton(
                    "Salvar e Continuar",
                    icon=ft.Icons.SAVE,
                    on_click=salvar_configuracao,
                    bgcolor="#22C55E",
                    color="#FFFFFF",
                    width=200,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Container(height=20),
            ft.Text(
                "💡 Dica: Para usar em rede, compartilhe a pasta do projeto no PC principal",
                size=11,
                color="#6B7280",
                italic=True,
                text_align=ft.TextAlign.CENTER,
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
        expand=True,
        padding=40,
        alignment=ft.alignment.center,
    )
