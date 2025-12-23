# notificacoes.py - Sistema de notificações estilo Windows
"""
Notificação que aparece no canto inferior direito após login
- Mostra atualizações recentes
- Pode ser expandida/recolhida
- Auto-fecha após 10 segundos
- Usuário pode fechar manualmente
"""
import flet as ft
import threading
import time

# Histórico de atualizações (adicione novas no topo)
CHANGELOG = [
    {
        "versao": "v2.1",
        "data": "23/12/2024",
        "titulo": "Migração MySQL",
        "itens": [
            "✅ Banco de dados migrado para MySQL",
            "✅ Sistema com funções extremamente rapidas",
            "✅ Analises e Oportunidades ia carregando imediatamente",
            "✅ Relatórios corrigidos",
            "✅ Atualização remota sem precisar de novos execuáveis", 
            "✅ Suporte a conexão via IP de rede",
            "✅ Relatórios agora usam dados históricos",
            "✅ Campo de IP do servidor no login",
        ]
    },
    {
        "versao": "v2.0",
        "data": "15/12/2024", 
        "titulo": "Nova Interface Flet",
        "itens": [
            "✅ Interface completamente redesenhada",
            "✅ Menu lateral com gradiente",
            "✅ Modo escuro/claro",
            "✅ Animações de transição",
        ]
    },
]


def criar_notificacao_update(page: ft.Page, is_dark: list):
    """Cria notificação de atualização estilo Windows Toast"""
    
    # Estado
    expandido = [False]
    visible = [True]
    usuario_interagiu = [False]  # Cancela auto-close se usuário interagir
    
    def get_bg():
        return "#2D2D2D" if is_dark[0] else "#FFFFFF"
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def fechar_notificacao(e=None):
        visible[0] = False
        if notificacao_container in page.overlay:
            page.overlay.remove(notificacao_container)
            page.update()
    
    def on_click_notificacao(e=None):
        """Usuário clicou - cancela auto-close"""
        usuario_interagiu[0] = True
    
    def toggle_expandir(e=None):
        usuario_interagiu[0] = True  # Cancela auto-close
        expandido[0] = not expandido[0]
        atualizar_conteudo()
        page.update()
    
    def atualizar_conteudo():
        if expandido[0]:
            # Versão expandida - mostra todas as atualizações com scroll
            items = []
            for update in CHANGELOG:
                items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(update["versao"], weight=ft.FontWeight.BOLD, color="#3B82F6", size=13),
                                ft.Text(f" - {update['data']}", color=get_text_color(), opacity=0.6, size=11),
                            ]),
                            ft.Text(update["titulo"], weight=ft.FontWeight.W_600, color=get_text_color(), size=12),
                            ft.Column([
                                ft.Text(item, size=11, color=get_text_color(), opacity=0.8)
                                for item in update["itens"]
                            ], spacing=2),
                        ], spacing=4),
                        padding=ft.padding.only(bottom=10),
                        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.1, get_text_color()))),
                    )
                )
            
            conteudo_expandido.content = ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO)
            conteudo_expandido.height = 300
            conteudo_expandido.visible = True
            btn_expandir.content = ft.Row([
                ft.Icon(ft.Icons.EXPAND_LESS, size=16, color="#3B82F6"),
                ft.Text("Recolher", size=11, color="#3B82F6"),
            ], spacing=5)
        else:
            conteudo_expandido.visible = False
            conteudo_expandido.height = 0
            btn_expandir.content = ft.Row([
                ft.Icon(ft.Icons.EXPAND_MORE, size=16, color="#3B82F6"),
                ft.Text("Ver todas atualizações", size=11, color="#3B82F6"),
            ], spacing=5)
    
    # Última atualização para mostrar resumo
    ultima = CHANGELOG[0] if CHANGELOG else {"versao": "-", "titulo": "-"}
    
    # Botões
    btn_fechar = ft.IconButton(
        ft.Icons.CLOSE,
        icon_size=16,
        icon_color=get_text_color(),
        tooltip="Fechar",
        on_click=fechar_notificacao,
    )
    
    btn_expandir = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.EXPAND_MORE, size=16, color="#3B82F6"),
            ft.Text("Ver todas atualizações", size=11, color="#3B82F6"),
        ], spacing=5),
        on_click=toggle_expandir,
        ink=True,
        border_radius=5,
        padding=5,
    )
    
    # Área expandida (inicialmente oculta)
    conteudo_expandido = ft.Container(
        content=ft.Container(),
        height=0,
        visible=False,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )
    
    # Container principal da notificação
    notificacao = ft.Container(
        content=ft.Column([
            # Header
            ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT, color="#22C55E", size=20),
                    ft.Text("Atualizações", weight=ft.FontWeight.BOLD, color=get_text_color(), size=13),
                ], spacing=8),
                btn_fechar,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Resumo da última atualização
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(ultima["versao"], size=10, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                            bgcolor="#3B82F6",
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=4,
                        ),
                        ft.Text(ultima["titulo"], size=12, weight=ft.FontWeight.W_500, color=get_text_color()),
                    ], spacing=8),
                    ft.Text(
                        f"{len(ultima.get('itens', []))} novidades nesta versão",
                        size=11,
                        color=get_text_color(),
                        opacity=0.7,
                    ),
                ], spacing=4),
                padding=ft.padding.only(top=5, bottom=5),
                on_click=on_click_notificacao,
            ),
            
            # Botão expandir
            ft.Row([btn_expandir], alignment=ft.MainAxisAlignment.CENTER),
            
            # Conteúdo expandido
            conteudo_expandido,
        ], spacing=5, scroll=ft.ScrollMode.AUTO),
        width=340,
        padding=15,
        bgcolor=get_bg(),
        border_radius=12,
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=2,
            color=ft.Colors.with_opacity(0.2, "#000000"),
            offset=ft.Offset(-2, -2),
        ),
        border=ft.border.all(1, ft.Colors.with_opacity(0.1, get_text_color())),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        on_click=on_click_notificacao,
    )
    
    # Container posicionado no canto inferior direito
    notificacao_container = ft.Container(
        content=notificacao,
        right=20,
        bottom=60,
        opacity=0,
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
    )
    
    return notificacao_container, fechar_notificacao, usuario_interagiu


def mostrar_notificacao_com_timeout(page: ft.Page, is_dark: list, timeout_segundos: int = 10):
    """Mostra notificação e fecha automaticamente após timeout (se usuário não interagir)"""
    
    notificacao, fechar, usuario_interagiu = criar_notificacao_update(page, is_dark)
    
    # Adicionar ao overlay
    page.overlay.append(notificacao)
    page.update()
    
    # Fade in
    time.sleep(0.1)
    notificacao.opacity = 1
    page.update()
    
    # Timer para auto-fechar (só fecha se usuário NÃO interagiu)
    def auto_fechar():
        time.sleep(timeout_segundos)
        try:
            # Se usuário interagiu, não fecha automaticamente
            if usuario_interagiu[0]:
                return
            
            if notificacao in page.overlay:
                # Fade out
                notificacao.opacity = 0
                page.update()
                time.sleep(0.5)
                fechar()
        except:
            pass  # Página pode ter sido fechada
    
    thread = threading.Thread(target=auto_fechar, daemon=True)
    thread.start()
