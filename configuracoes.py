# configuracoes.py — Tela de configurações Flet + preferências (arquivo JSON)
"""
Configurações com alternância de tema e preferências salvas
"""
import flet as ft
import os
import json
from typing import Any, Callable

CAMINHO_CONFIG = os.path.join("data", "config")
CAMINHO_PREFS = os.path.join(CAMINHO_CONFIG, "prefs.json")


def _garantir_pasta():
    os.makedirs(CAMINHO_CONFIG, exist_ok=True)


def carregar_preferencias() -> dict:
    if not os.path.exists(CAMINHO_PREFS):
        return {}
    try:
        with open(CAMINHO_PREFS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def carregar_tema() -> Any:
    prefs = carregar_preferencias()
    return prefs.get("tema", "dark")


def salvar_preferencias(dados: dict) -> None:
    _garantir_pasta()
    prefs = carregar_preferencias()
    prefs.update(dados)
    with open(CAMINHO_PREFS, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=4)


def salvar_tema(tema: str) -> None:
    salvar_preferencias({"tema": tema})


def criar_tela_configuracoes(page: ft.Page, is_dark: list, toggle_theme_callback: Callable):
    """Cria a tela de configurações"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    prefs = carregar_preferencias()
    lembrar = prefs.get("lembrar_login", False)
    usuario = prefs.get("usuario_padrao", "Nenhum")
    
    def alternar_tema(e):
        novo_tema = "light" if is_dark[0] else "dark"
        salvar_tema(novo_tema)
        toggle_theme_callback(e)
    
    def abrir_importar_skus():
        from importar_skus import criar_dialogo_importar_skus
        criar_dialogo_importar_skus(page, is_dark)
    
    tema_switch = ft.Switch(
        label="Modo Escuro",
        value=is_dark[0],
        on_change=alternar_tema,
        active_color="#16A34A",
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Container(height=10),
            ft.Text(
                "⚙️ Configurações",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=get_text_color(),
            ),
            ft.Container(height=30),
            
            # Seção Tema
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Tema da Interface",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=get_text_color(),
                    ),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Icon(
                            ft.Icons.DARK_MODE if is_dark[0] else ft.Icons.LIGHT_MODE,
                            color=get_text_color(),
                            size=24,
                        ),
                        tema_switch,
                    ], spacing=10),
                ]),
                bgcolor=get_surface(),
                padding=20,
                border_radius=10,
            ),
            
            ft.Container(height=20),
            
            # Seção Gerenciar SKUs
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Gerenciar SKUs",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=get_text_color(),
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Adicione ou atualize SKUs através de um arquivo Excel.",
                        size=12,
                        color=get_text_color(),
                        opacity=0.7,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Adicionar/Atualizar SKUs",
                        icon=ft.Icons.ADD_CIRCLE,
                        on_click=lambda e: abrir_importar_skus(),
                        bgcolor="#22C55E",
                        color="#FFFFFF",
                    ),
                ]),
                bgcolor=get_surface(),
                padding=20,
                border_radius=10,
            ),
            
            ft.Container(height=20),
            
            # Seção Preferências
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Preferências de Login",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=get_text_color(),
                    ),
                    ft.Container(height=15),
                    ft.Row([
                        ft.Icon(ft.Icons.SAVE, color=get_text_color(), size=20),
                        ft.Text(
                            f"Login lembrado: {'✅ Sim' if lembrar else '❌ Não'}",
                            size=14,
                            color=get_text_color(),
                        ),
                    ], spacing=10),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON, color=get_text_color(), size=20),
                        ft.Text(
                            f"Usuário padrão: {usuario}",
                            size=14,
                            color=get_text_color(),
                        ),
                    ], spacing=10),
                ]),
                bgcolor=get_surface(),
                padding=20,
                border_radius=10,
            ),
            
            ft.Container(height=20),
            
            # Seção Sobre
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Sobre",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=get_text_color(),
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "Central do Comercial — Netshoes",
                        size=14,
                        color=get_text_color(),
                    ),
                    ft.Text(
                        "Versão 2.0 (Flet)",
                        size=12,
                        color=get_text_color(),
                        opacity=0.7,
                    ),
                    ft.Text(
                        "Desenvolvido por Samuel Rodrigues",
                        size=12,
                        color=get_text_color(),
                        opacity=0.7,
                    ),
                ]),
                bgcolor=get_surface(),
                padding=20,
                border_radius=10,
            ),
            
            ft.Container(height=30),  # Espaço extra no final para melhor scroll
            
        ], scroll=ft.ScrollMode.AUTO),  # ← Scroll adicionado aqui
        expand=True,
        padding=20,
    )
