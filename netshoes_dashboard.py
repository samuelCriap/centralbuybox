# netshoes_dashboard.py - Dashboard Flet (com 3 vendedores)
"""
Dashboard com KPIs, filtro de SKU, SKU Seller e paginação
"""
import flet as ft
import pandas as pd
from datetime import datetime
from db_client import ler_planilha, ler_aba


def criar_tela_dashboard(page: ft.Page, is_dark: list):
    """Cria o dashboard com KPIs e tabela de produtos"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    # Estado
    df_global = [None]
    df_filtrado = [None]
    current_page = [0]
    items_per_page = 30
    
    # Container principal
    main_content = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
    info_label = ft.Text("Ultima atualizacao: -", size=11, color=get_text_color())
    tabela_container = ft.Column(spacing=5)
    pagination_row = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.CENTER)
    
    # Campo de filtro
    filtro_sku = ft.TextField(
        label="Filtrar por SKU / SKU Seller",
        hint_text="Digite o SKU ou SKU Seller para filtrar...",
        prefix_icon=ft.Icons.SEARCH,
        width=400,
        border_radius=8,
        bgcolor=get_surface(),
    )
    
    def criar_kpi_card(titulo, valor, subtitulo=""):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=11, color=get_text_color(), opacity=0.7),
                ft.Text(str(valor), size=22, weight=ft.FontWeight.BOLD, color=get_text_color()),
                ft.Text(subtitulo, size=10, color=get_text_color(), opacity=0.5),
            ], spacing=5),
            bgcolor=get_surface(),
            padding=15,
            border_radius=10,
            expand=True,
        )
    
    def criar_msg_sem_dados(msg="Nenhum dado disponivel"):
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INFO_OUTLINE, size=48, color=get_text_color(), opacity=0.5),
                ft.Text(msg, size=14, color=get_text_color(), opacity=0.7, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            bgcolor=get_surface(),
            padding=40,
            border_radius=10,
            alignment=ft.alignment.center,
        )
    
    def aplicar_filtro(e=None):
        """Aplica filtro de SKU"""
        termo = filtro_sku.value.strip().lower() if filtro_sku.value else ""
        current_page[0] = 0  # Reset para primeira página
        
        if df_global[0] is None:
            return
        
        if not termo:
            df_filtrado[0] = df_global[0]
        else:
            df = df_global[0]
            mask = df["codigo_produto"].astype(str).str.lower().str.contains(termo, na=False)
            if "sku_seller" in df.columns:
                mask = mask | df["sku_seller"].astype(str).str.lower().str.contains(termo, na=False)
            df_filtrado[0] = df[mask]
        
        atualizar_tabela()
        page.update()
    
    def ir_para_pagina(pagina):
        """Navega para uma página específica"""
        def handler(e):
            current_page[0] = pagina
            atualizar_tabela()
            page.update()
        return handler
    
    def atualizar_tabela():
        """Atualiza a tabela com paginação"""
        tabela_container.controls.clear()
        pagination_row.controls.clear()
        
        df = df_filtrado[0]
        if df is None or df.empty:
            tabela_container.controls.append(ft.Text("Nenhum resultado encontrado", color=get_text_color(), opacity=0.7))
            return
        
        total = len(df)
        total_pages = (total + items_per_page - 1) // items_per_page
        start_idx = current_page[0] * items_per_page
        end_idx = min(start_idx + items_per_page, total)
        
        # Colunas da tabela (incluindo SKU Seller e Fretes)
        colunas = []
        cols_to_show = ["codigo_produto", "sku_seller", "nome_esperado", "Vendedor 1", "Preco 1", "Frete 1",
                        "Vendedor 2", "Preco 2", "Frete 2", "Vendedor 3", "Preco 3", "Frete 3", "Status Final"]
        col_names = ["SKU", "SKU Seller", "Nome", "Vendedor 1", "Preço 1", "Frete 1",
                     "Vendedor 2", "Preço 2", "Frete 2", "Vendedor 3", "Preço 3", "Frete 3", "Status"]
        
        for col, name in zip(cols_to_show, col_names):
            if col in df.columns:
                colunas.append(ft.DataColumn(ft.Text(name, size=10, weight=ft.FontWeight.BOLD, color=get_text_color())))
        
        # Linhas da tabela
        linhas = []
        for idx, row in df.iloc[start_idx:end_idx].iterrows():
            cells = []
            for col in cols_to_show:
                if col in df.columns:
                    val = str(row.get(col, "-"))[:25]  # Limitar tamanho
                    
                    # Cor especial para status
                    if col == "Status Final":
                        color = "#22C55E" if val == "OK" else "#EAB308"
                        cells.append(ft.DataCell(ft.Text(val, size=9, color=color, weight=ft.FontWeight.BOLD)))
                    else:
                        cells.append(ft.DataCell(ft.Text(val, size=9, color=get_text_color())))
            
            linhas.append(ft.DataRow(cells=cells))
        
        if linhas:
            tabela = ft.DataTable(
                columns=colunas,
                rows=linhas,
                border=ft.border.all(1, get_text_color()),
                border_radius=8,
                horizontal_lines=ft.BorderSide(1, get_text_color()),
                heading_row_color=get_surface(),
                data_row_min_height=35,
                data_row_max_height=40,
            )
            
            tabela_container.controls.append(
                ft.Text(f"Mostrando {start_idx+1}-{end_idx} de {total} produtos", 
                        size=12, color=get_text_color(), weight=ft.FontWeight.BOLD)
            )
            tabela_container.controls.append(tabela)
        
        # Paginação
        if total_pages > 1:
            # Botão anterior
            pagination_row.controls.append(
                ft.ElevatedButton(
                    "← Anterior",
                    on_click=ir_para_pagina(current_page[0] - 1) if current_page[0] > 0 else None,
                    disabled=current_page[0] == 0,
                    bgcolor="#3B82F6" if current_page[0] > 0 else "#CCCCCC",
                    color="#FFFFFF",
                )
            )
            
            # Números de página (mostrar até 5 páginas)
            start_page = max(0, current_page[0] - 2)
            end_page = min(total_pages, start_page + 5)
            
            if start_page > 0:
                pagination_row.controls.append(ft.Text("...", color=get_text_color()))
            
            for p in range(start_page, end_page):
                is_current = p == current_page[0]
                pagination_row.controls.append(
                    ft.ElevatedButton(
                        str(p + 1),
                        on_click=ir_para_pagina(p),
                        bgcolor="#22C55E" if is_current else get_surface(),
                        color="#FFFFFF" if is_current else get_text_color(),
                        width=45,
                    )
                )
            
            if end_page < total_pages:
                pagination_row.controls.append(ft.Text("...", color=get_text_color()))
            
            # Botão próximo
            pagination_row.controls.append(
                ft.ElevatedButton(
                    "Próxima →",
                    on_click=ir_para_pagina(current_page[0] + 1) if current_page[0] < total_pages - 1 else None,
                    disabled=current_page[0] >= total_pages - 1,
                    bgcolor="#3B82F6" if current_page[0] < total_pages - 1 else "#CCCCCC",
                    color="#FFFFFF",
                )
            )
    
    def render_dashboard(e=None):
        main_content.controls.clear()
        
        try:
            df = ler_planilha()
            
            if df is None or df.empty:
                main_content.controls.append(criar_msg_sem_dados(
                    "Nenhum dado de produtos encontrado.\n\nExecute 'python main.py' para coletar dados."
                ))
                info_label.value = f"Ultima atualizacao: {datetime.now().strftime('%H:%M:%S')}"
                page.update()
                return
            
            df = df.copy()
            df_global[0] = df
            df_filtrado[0] = df
            
            total_skus = len(df)
            
            # Contar SKUs com vendedor 1 preenchido
            if "Vendedor 1" in df.columns:
                df["Vendedor 1"] = df["Vendedor 1"].fillna("-").astype(str)
                com_vendedor = len(df[df["Vendedor 1"] != "-"])
            else:
                com_vendedor = 0
            
            # Status
            if "Status Final" in df.columns:
                ok_count = len(df[df["Status Final"] == "OK"])
                sem_estoque = len(df[df["Status Final"] == "SEM ESTOQUE"])
            else:
                ok_count = 0
                sem_estoque = 0
            
            # KPIs
            kpis_row = ft.Row([
                criar_kpi_card("Total SKUs", f"{total_skus:,}"),
                criar_kpi_card("Com Vendedor", f"{com_vendedor:,}", f"{com_vendedor/total_skus*100:.1f}%" if total_skus else ""),
                criar_kpi_card("OK", f"{ok_count:,}"),
                criar_kpi_card("Sem Estoque", f"{sem_estoque:,}"),
            ], spacing=15)
            
            main_content.controls.append(kpis_row)
            
            # Filtro de SKU
            filtro_row = ft.Row([
                filtro_sku,
                ft.ElevatedButton(
                    "Filtrar",
                    icon=ft.Icons.SEARCH,
                    on_click=aplicar_filtro,
                    bgcolor="#3B82F6",
                    color="#FFFFFF",
                ),
                ft.ElevatedButton(
                    "Limpar",
                    icon=ft.Icons.CLEAR,
                    on_click=lambda e: (setattr(filtro_sku, 'value', ''), aplicar_filtro()),
                    bgcolor=get_surface(),
                    color=get_text_color(),
                ),
            ], spacing=10)
            main_content.controls.append(filtro_row)
            
            # Container da tabela
            main_content.controls.append(tabela_container)
            
            # Paginação
            main_content.controls.append(pagination_row)
            
            # Atualizar tabela inicial
            current_page[0] = 0
            atualizar_tabela()
            
            info_label.value = f"Ultima atualizacao: {datetime.now().strftime('%H:%M:%S')}"
            
        except Exception as ex:
            main_content.controls.append(ft.Container(
                content=ft.Text(f"Erro: {ex}", color=ft.Colors.RED_400),
                padding=20,
            ))
        
        page.update()
    
    # Bind Enter para filtrar
    filtro_sku.on_submit = aplicar_filtro
    
    # Header com controles
    header = ft.Row([
        ft.Text("Dashboard Netshoes", size=24, weight=ft.FontWeight.BOLD, color=get_text_color()),
        ft.Container(expand=True),
        ft.ElevatedButton(
            "Atualizar",
            icon=ft.Icons.REFRESH,
            on_click=render_dashboard,
            bgcolor="#3B82F6",
            color="#FFFFFF",
        ),
        info_label,
    ], spacing=15)
    
    # Renderizar dashboard inicial
    render_dashboard()
    
    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(height=10),
            ft.Container(content=main_content, expand=True),
        ]),
        expand=True,
        padding=10,
    )
