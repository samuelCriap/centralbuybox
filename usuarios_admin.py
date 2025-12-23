# usuarios_admin.py - Painel de Gestao de Usuarios
"""
Tela para Admin/Master gerenciar usuarios:
- Aprovar/Bloquear
- Mudar Cargo (User/Admin/Master)
- Excluir usuarios
- Master: Acesso total, não pode ser modificado por admins
"""
import flet as ft
from db_client import listar_usuarios, atualizar_usuario, excluir_usuario

def criar_tela_usuarios(page: ft.Page, is_dark: list, is_master: bool = False):
    """Cria a tela de gestao de usuarios"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    status_text = ft.Text("", size=12)
    
    # Tabela de usuarios
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Usuario")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Cargo")),
            ft.DataColumn(ft.Text("Ações")),
        ],
        rows=[],
        border=ft.border.all(1, get_text_color()),
        vertical_lines=ft.border.all(1, "#333333" if is_dark[0] else "#EEEEEE"),
        heading_row_color="#3B82F6",
        heading_row_height=40,
        data_row_min_height=40,
    )
    
    def carregar_dados():
        df = listar_usuarios()
        
        tabela.rows.clear()
        
        if df.empty:
            status_text.value = "Nenhum usuario encontrado."
            page.update()
            return

        for idx, row in df.iterrows():
            user_id = row['id']
            status = row['status']
            role = row['role']
            
            # Verificar se é usuário master (protegido)
            is_user_master = role == "master"
            
            # Admin não pode modificar master
            can_modify = is_master or not is_user_master
            
            # Dropdown de Cargo - Master só aparece se o usuário logado é master
            role_options = [
                ft.dropdown.Option("user", "Usuario"),
                ft.dropdown.Option("admin", "Admin"),
            ]
            if is_master:  # Apenas master pode ver/atribuir cargo master
                role_options.append(ft.dropdown.Option("master", "Master"))
            
            dd_role = ft.Dropdown(
                value=role,
                options=role_options,
                width=100,
                text_size=12,
                content_padding=5,
                on_change=lambda e, uid=user_id: mudar_cargo(uid, e.control.value),
                disabled=not can_modify,  # Desabilitar se não pode modificar
            )
            
            # Botao Aprovar/Bloquear
            btn_status = ft.IconButton(
                icon=ft.Icons.CHECK_CIRCLE if status != "aprovado" else ft.Icons.BLOCK,
                icon_color="green" if status != "aprovado" else "red",
                tooltip="Aprovar" if status != "aprovado" else "Bloquear",
                on_click=lambda e, uid=user_id, s=status: alternar_status(uid, s),
                disabled=not can_modify,  # Desabilitar se não pode modificar
            )
            
            # Botao Excluir
            btn_excluir = ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color="red" if can_modify else "grey",
                tooltip="Excluir" if can_modify else "Protegido",
                on_click=lambda e, uid=user_id, r=role: deletar_usuario_confirm(uid, r),
                disabled=not can_modify,  # Desabilitar se não pode modificar
            )
            
            # Adicionar badge de proteção para masters
            cargo_cell = ft.Row([
                dd_role,
                ft.Icon(ft.Icons.SHIELD, color="#FFD700", size=16, tooltip="Protegido") if is_user_master else ft.Container()
            ], spacing=5)
            
            tabela.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(user_id))),
                        ft.DataCell(ft.Text(str(row['usuario']))),
                        ft.DataCell(ft.Text(str(row['email']))),
                        ft.DataCell(ft.Container(
                            content=ft.Text(status.upper(), size=10, color="white"),
                            bgcolor="green" if status == "aprovado" else "orange",
                            padding=5, border_radius=5
                        )),
                        ft.DataCell(cargo_cell),
                        ft.DataCell(ft.Row([btn_status, btn_excluir], spacing=0)),
                    ]
                )
            )
        page.update()

    def mudar_cargo(user_id, novo_cargo):
        if atualizar_usuario(user_id, role=novo_cargo):
            status_text.value = f"Cargo atualizado para {novo_cargo}"
            status_text.color = "green"
        else:
            status_text.value = "Erro ao atualizar cargo"
            status_text.color = "red"
        page.update()

    def alternar_status(user_id, status_atual):
        novo_status = "aprovado" if status_atual != "aprovado" else "bloqueado"
        if atualizar_usuario(user_id, status=novo_status):
            carregar_dados() # Recarregar para atualizar icone
            status_text.value = f"Status alterado para {novo_status}"
            status_text.color = "green"
        else:
            status_text.value = "Erro ao atualizar status"
            status_text.color = "red"
        page.update()

    def deletar_usuario_confirm(user_id, user_role):
        # Verificar proteção de master
        if user_role == "master" and not is_master:
            status_text.value = "❌ Não é possível excluir um usuário Master"
            status_text.color = "red"
            page.update()
            return
            
        def fechar_dlg(e=None):
            page.close(dlg)
            
        def confirmar(e):
            page.close(dlg)
            if excluir_usuario(user_id):
                carregar_dados()
                status_text.value = "Usuario excluido com sucesso"
                status_text.color = "green"
            else:
                status_text.value = "Erro ao excluir usuario"
                status_text.color = "red"
            page.update()
            
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text("Tem certeza que deseja excluir este usuario? Esta ação não pode ser desfeita."),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dlg),
                ft.ElevatedButton("Excluir", on_click=confirmar, bgcolor="#EF4444", color="#FFFFFF"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)

    # Inicializar dados
    carregar_dados()
    
    header = ft.Row([
        ft.Text("Gestao de Usuarios", size=24, weight=ft.FontWeight.BOLD, color=get_text_color()),
        ft.Container(expand=True),
        ft.ElevatedButton("Atualizar Lista", icon=ft.Icons.REFRESH, on_click=lambda e: carregar_dados()),
    ])
    
    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(height=20),
            ft.Text("Apenas admins podem ver esta tela.", color="grey", italic=True),
            ft.Container(height=10),
            ft.Row([tabela], scroll=ft.ScrollMode.AUTO, expand=True), # Scroll horizontal se precisar
            ft.Container(height=10),
            status_text
        ]),
        padding=20,
        expand=True
    )
