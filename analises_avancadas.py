# analises_avancadas.py - Dashboard de Analises com Oportunidades de Lucro
"""
Tela de analises com multiplas abas e Oportunidades de Lucro
"""
import flet as ft
import pandas as pd
from db_client import ler_planilha
from oportunidades_ia import analisar_gap_lucro

def criar_tela_analises(page: ft.Page, is_dark: list):
    """Cria dashboard de analises com abas e oportunidades"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_bg_color():
        return "#1E1E1E" if is_dark[0] else "#FFFFFF"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    # Dados globais
    df_global = [None]
    
    def carregar_dados():
        df_global[0] = ler_planilha()
        return df_global[0]
    
    def criar_kpi_card(titulo, valor, cor="#3B82F6", subtitulo=""):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=10, color=get_text_color(), opacity=0.7, text_align=ft.TextAlign.CENTER),
                ft.Text(str(valor), size=22, weight=ft.FontWeight.BOLD, color=cor, text_align=ft.TextAlign.CENTER),
                ft.Text(subtitulo, size=9, color=get_text_color(), opacity=0.5) if subtitulo else ft.Container(),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=get_surface(),
            padding=12,
            border_radius=8,
            expand=True,
        )
    
    def criar_tabela_ranking(dados, col1_nome, col2_nome, max_rows=15):
        if not dados:
            return ft.Text("Nenhum dado", color=get_text_color(), opacity=0.5)
        
        rows = []
        for i, item in enumerate(dados[:max_rows]):
            nome, valor = item[0], item[1]
            pos_cor = "#FFD700" if i == 0 else ("#C0C0C0" if i == 1 else ("#CD7F32" if i == 2 else "#6B7280"))
            rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(f"{i+1}", size=10, weight=ft.FontWeight.BOLD, color="#FFF", text_align=ft.TextAlign.CENTER),
                            width=24, height=24, border_radius=12, bgcolor=pos_cor, alignment=ft.alignment.center,
                        ),
                        ft.Text(str(nome)[:35], size=11, color=get_text_color(), expand=True),
                        ft.Text(str(valor), size=11, color=get_text_color(), weight=ft.FontWeight.BOLD),
                    ], spacing=8),
                    padding=6, border_radius=4, bgcolor=get_surface() if i % 2 == 0 else None,
                )
            )
        
        return ft.Column([
            ft.Row([
                ft.Text("#", size=10, color=get_text_color(), opacity=0.6, width=28),
                ft.Text(col1_nome, size=10, color=get_text_color(), opacity=0.6, expand=True),
                ft.Text(col2_nome, size=10, color=get_text_color(), opacity=0.6),
            ], spacing=8),
            ft.Divider(height=1, color=get_text_color()),
            *rows,
        ], spacing=2)
    
    def criar_barra_h(label, valor, total, cor="#3B82F6"):
        pct = (valor / total * 100) if total > 0 else 0
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(label, size=11, color=get_text_color(), expand=True),
                    ft.Text(f"{valor:,} ({pct:.1f}%)", size=11, color=get_text_color(), weight=ft.FontWeight.BOLD),
                ]),
                ft.ProgressBar(value=pct/100, color=cor, bgcolor=get_surface(), height=8),
            ], spacing=3),
            padding=ft.padding.symmetric(vertical=4),
        )

    # ... [Abas anteriores omitidas para brevidade, mantendo a estrutura original] ...
    # Vou reescrever as abas principais e adicionar a nova
    
    # ======================= ABA RESUMO =======================
    def criar_aba_resumo():
        df = df_global[0]
        if df is None or df.empty:
            return ft.Container(content=ft.Text("Nenhum dado. Execute 'python main.py'.", color=get_text_color()), padding=40)
        
        total = len(df)
        ok = len(df[df.get("Status Final", "") == "OK"]) if "Status Final" in df.columns else 0
        sem_estoque = len(df[df.get("Status Final", "") == "SEM ESTOQUE"]) if "Status Final" in df.columns else 0
        v2 = len(df[df.get("Vendedor 2", "-") != "-"]) if "Vendedor 2" in df.columns else 0
        v3 = len(df[df.get("Vendedor 3", "-") != "-"]) if "Vendedor 3" in df.columns else 0
        frete_gratis = len(df[df.get("Frete 1", "") == "Gratis"]) if "Frete 1" in df.columns else 0
        
        # Verificar oportunidades
        df_opp = analisar_gap_lucro(df)
        total_opp = len(df_opp)
        ganho_total = df_opp["Ganho Potencial"].sum() if not df_opp.empty else 0
        
        # Alerta se houver oportunidades
        alerta = ft.Container()
        if total_opp > 0:
            def ir_para_oportunidades(e):
                tabs.selected_index = 6
                on_tab_change(None)
            
            alerta = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.MONETIZATION_ON, color="#FFF", size=24),
                    ft.Column([
                        ft.Text(f"ATENCAO: {total_opp} Oportunidades de Lucro detectadas!", weight=ft.FontWeight.BOLD, color="#FFFFFF", size=14),
                        ft.Text(f"Potencial de ganho extra: R$ {ganho_total:.2f}", color="#FFFFFF", size=12),
                        ft.Text("Clique aqui para ver detalhes", color="#FFFFFF", size=10, italic=True),
                    ], spacing=2),
                ], spacing=10),
                bgcolor="#10B981",
                padding=15,
                border_radius=10,
                on_click=ir_para_oportunidades,
                ink=True,
            )
        
        return ft.Container(
            content=ft.Column([
                alerta,
                ft.Container(height=10),
                ft.Row([
                    criar_kpi_card("Total SKUs", f"{total:,}", "#3B82F6"),
                    criar_kpi_card("Status OK", f"{ok:,}", "#22C55E", f"{ok/total*100:.0f}%" if total else ""),
                    criar_kpi_card("Sem Estoque", f"{sem_estoque:,}", "#EAB308"),
                    criar_kpi_card("2+ Vendedores", f"{v2:,}", "#8B5CF6"),
                    criar_kpi_card("3 Vendedores", f"{v3:,}", "#EC4899"),
                    criar_kpi_card("Frete Gratis", f"{frete_gratis:,}", "#14B8A6"),
                ], spacing=10),
                ft.Container(height=15),
                criar_barra_h("Status OK", ok, total, "#22C55E"),
                criar_barra_h("Sem Estoque", sem_estoque, total, "#EAB308"),
                criar_barra_h("Com 2+ Vendedores", v2, total, "#8B5CF6"),
                criar_barra_h("Frete Gratis", frete_gratis, total, "#14B8A6"),
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=15,
        )
    
    # ... [Reimplementando abas Precos, BuyBox, Color vs Conc, Substituicoes, Search SKU iguais anterior] ...
    # (Para simplificar, vou incluir o codigo completo dessas abas tbm para garantir que nada quebre)
    
    def criar_aba_precos():
        df = df_global[0]
        if df is None or df.empty: return ft.Container()
        
        # Versão vetorizada - muito mais rápida
        vendedor_precos = {}
        for v_col, p_col in [("Vendedor 1", "Preco 1"), ("Vendedor 2", "Preco 2"), ("Vendedor 3", "Preco 3")]:
            if v_col in df.columns and p_col in df.columns:
                # Criar DataFrame temporário com vendedor e preço
                temp = df[[v_col, p_col]].copy()
                temp.columns = ['vendedor', 'preco']
                # Filtrar valores válidos
                temp = temp[(temp['vendedor'] != '-') & (temp['vendedor'].notna())]
                temp['preco'] = temp['preco'].apply(lambda x: float(str(x).replace(',', '.')) if str(x) != '-' else None)
                temp = temp.dropna(subset=['preco'])
                
                # Agrupar por vendedor
                for vendedor, grupo in temp.groupby('vendedor'):
                    if vendedor not in vendedor_precos:
                        vendedor_precos[vendedor] = []
                    vendedor_precos[vendedor].extend(grupo['preco'].tolist())
        
        ranking_preco = [(v, f"R$ {sum(ps)/len(ps):.2f}") for v, ps in sorted(vendedor_precos.items(), key=lambda x: sum(x[1])/len(x[1]))]
        total_ofertas = sum(len(ps) for ps in vendedor_precos.values())
        return ft.Container(content=ft.Column([
                ft.Row([criar_kpi_card("Vendedores Unicos", len(vendedor_precos), "#3B82F6"), criar_kpi_card("Total Ofertas", total_ofertas, "#22C55E")], spacing=10),
                ft.Container(height=15),
                ft.Text("Preco Medio por Vendedor (menor primeiro)", size=14, weight=ft.FontWeight.BOLD, color=get_text_color()),
                ft.Container(height=5), criar_tabela_ranking(ranking_preco, "Vendedor", "Preco Medio"),
            ], scroll=ft.ScrollMode.AUTO), expand=True, padding=15)

    def criar_aba_buybox():
        df = df_global[0]
        if df is None or df.empty: return ft.Container()
        if "Vendedor 1" not in df.columns: return ft.Container()
        contagem = df["Vendedor 1"].value_counts()
        contagem = contagem[contagem.index != "-"]
        total_buybox = contagem.sum()
        ranking = [(v, f"{c} ({c/total_buybox*100:.1f}%)") for v, c in contagem.items()]
        return ft.Container(content=ft.Column([
                ft.Row([criar_kpi_card("Total BuyBox", total_buybox, "#3B82F6"), criar_kpi_card("Vendedores", len(contagem), "#22C55E")], spacing=10),
                ft.Container(height=15),
                ft.Text("Ranking BuyBox (Vendedor 1 = ganhador)", size=14, weight=ft.FontWeight.BOLD, color=get_text_color()),
                ft.Container(height=5), criar_tabela_ranking(ranking, "Vendedor", "BuyBox Wins"),
            ], scroll=ft.ScrollMode.AUTO), expand=True, padding=15)

    def criar_aba_color_vs():
        df = df_global[0]
        if df is None or df.empty: return ft.Container()
        
        # Versão vetorizada
        color_precos = []
        outros_precos = {}
        
        for v_col, p_col in [("Vendedor 1", "Preco 1"), ("Vendedor 2", "Preco 2"), ("Vendedor 3", "Preco 3")]:
            if v_col in df.columns and p_col in df.columns:
                temp = df[[v_col, p_col]].copy()
                temp.columns = ['vendedor', 'preco']
                temp['vendedor'] = temp['vendedor'].fillna('-').astype(str).str.lower()
                temp = temp[(temp['vendedor'] != '-') & (temp['vendedor'] != '')]
                temp['preco'] = temp['preco'].apply(lambda x: float(str(x).replace(',', '.')) if str(x) != '-' else None)
                temp = temp.dropna(subset=['preco'])
                
                # Separar Color e outros
                color_mask = temp['vendedor'].str.contains('color', na=False)
                color_precos.extend(temp.loc[color_mask, 'preco'].tolist())
                
                outros = temp[~color_mask]
                for vendedor, grupo in outros.groupby('vendedor'):
                    if vendedor not in outros_precos:
                        outros_precos[vendedor] = []
                    outros_precos[vendedor].extend(grupo['preco'].tolist())
        
        media_color = sum(color_precos)/len(color_precos) if color_precos else 0
        media_conc = sum(sum(ps) for ps in outros_precos.values()) / sum(len(ps) for ps in outros_precos.values()) if outros_precos else 0
        diff = media_color - media_conc
        diff_pct = (diff / media_conc * 100) if media_conc else 0
        comparativo = []
        for conc, precos in sorted(outros_precos.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            media_conc_i = sum(precos)/len(precos)
            diff_i = media_color - media_conc_i
            comparativo.append((conc, f"R$ {media_conc_i:.2f} (diff: {diff_i:+.2f})"))
        diff_cor = "#22C55E" if diff < 0 else "#EF4444"
        return ft.Container(content=ft.Column([
                ft.Row([criar_kpi_card("Media Color Sports", f"R$ {media_color:.2f}", "#3B82F6"), criar_kpi_card("Media Concorrencia", f"R$ {media_conc:.2f}", "#8B5CF6"), criar_kpi_card("Diferenca", f"R$ {diff:+.2f}", diff_cor, f"{diff_pct:+.1f}%")], spacing=10),
                ft.Container(height=15),
                ft.Text("Comparativo com Concorrentes", size=14, weight=ft.FontWeight.BOLD, color=get_text_color()),
                ft.Container(height=5), criar_tabela_ranking(comparativo, "Concorrente", "Preco Medio (diff vs Color)"),
            ], scroll=ft.ScrollMode.AUTO), expand=True, padding=15)

    def criar_aba_substituicoes():
        df = df_global[0]
        if df is None or df.empty: return ft.Container()
        
        total_produtos = len(df)
        
        # Versão vetorizada
        if "Vendedor 1" in df.columns:
            # Identificar onde Color está em primeiro
            color_em_primeiro = df["Vendedor 1"].fillna('').str.lower().str.contains("color", na=False).sum()
            
            # Quem substitui Color (vendedores que não são Color em 1o lugar)
            df_nao_color = df[~df["Vendedor 1"].fillna('').str.lower().str.contains("color", na=False)]
            df_nao_color = df_nao_color[df_nao_color["Vendedor 1"].fillna('-') != '-']
            
            substituicoes = df_nao_color["Vendedor 1"].value_counts().to_dict()
            ranking = sorted(substituicoes.items(), key=lambda x: x[1], reverse=True)
        else:
            color_em_primeiro = 0
            ranking = []
        
        color_perdeu = total_produtos - color_em_primeiro
        return ft.Container(content=ft.Column([
                ft.Row([criar_kpi_card("Color em 1o", color_em_primeiro, "#22C55E", f"{color_em_primeiro/total_produtos*100:.0f}%" if total_produtos else ""), criar_kpi_card("Color Perdeu", color_perdeu, "#EF4444", f"{color_perdeu/total_produtos*100:.0f}%" if total_produtos else "")], spacing=10),
                ft.Container(height=15),
                ft.Text("Quem Substitui Color Sports (ganha BuyBox)", size=14, weight=ft.FontWeight.BOLD, color=get_text_color()),
                ft.Container(height=5), criar_tabela_ranking(ranking, "Concorrente", "Vezes em 1o"),
            ], scroll=ft.ScrollMode.AUTO), expand=True, padding=15)

    def criar_aba_sku():
        df = df_global[0]
        search_field = ft.TextField(label="Pesquisar SKU", hint_text="Digite o codigo do produto ou SKU Seller...", width=400, autofocus=False)
        results_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        current_page = [0]  # Pagina atual
        items_per_page = 100
        
        def mostrar_resultados(resultados, termo=""):
            results_container.controls.clear()
            total = len(resultados)
            start_idx = current_page[0] * items_per_page
            end_idx = min(start_idx + items_per_page, total)
            
            if total == 0:
                if termo:
                    results_container.controls.append(ft.Text(f"Nenhum resultado para '{termo}'", color=get_text_color(), opacity=0.5))
                else:
                    results_container.controls.append(ft.Text("Nenhum produto na base", color=get_text_color(), opacity=0.5))
            else:
                # Header com info de paginacao
                info_text = f"Mostrando {start_idx+1}-{end_idx} de {total} produto(s)"
                if termo:
                    info_text = f"{total} resultado(s) para '{termo}' - " + info_text
                results_container.controls.append(ft.Text(info_text, size=12, color=get_text_color(), weight=ft.FontWeight.BOLD))
                results_container.controls.append(ft.Container(height=10))
                
                # Mostrar produtos da pagina atual
                for idx, row in resultados.iloc[start_idx:end_idx].iterrows():
                    card = ft.Container(content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(f"SKU: {row.get('codigo_produto', '-')}", size=14, weight=ft.FontWeight.BOLD, color=get_text_color()),
                                    ft.Text(f"{row.get('nome_esperado', '')}", size=12, color=get_text_color(), weight=ft.FontWeight.BOLD) if row.get('nome_esperado') else ft.Container(),
                                ], spacing=2),
                                ft.Text(f"SKU Seller: {row.get('sku_seller', '-')}", size=12, color=get_text_color(), opacity=0.7) if row.get('sku_seller') else ft.Container(),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(
                                        row.get("Status Final", "-"), 
                                        size=10, 
                                        color="#FFFFFF",
                                        weight=ft.FontWeight.BOLD,
                                    ), 
                                    bgcolor="#22C55E" if row.get("Status Final") == "OK" else "#EAB308", 
                                    padding=ft.padding.symmetric(horizontal=10, vertical=6), 
                                    border_radius=4,
                                ),
                            ]),
                            ft.Divider(height=1),
                            ft.Row([
                                ft.Column([ft.Text("Vendedor 1", size=10, color=get_text_color(), opacity=0.6), ft.Text(str(row.get("Vendedor 1", "-"))[:25], size=12, color=get_text_color()), ft.Text(f"R$ {row.get('Preco 1', '-')}", size=11, color="#22C55E", weight=ft.FontWeight.BOLD)], expand=True),
                                ft.Column([ft.Text("Vendedor 2", size=10, color=get_text_color(), opacity=0.6), ft.Text(str(row.get("Vendedor 2", "-"))[:25], size=12, color=get_text_color()), ft.Text(f"R$ {row.get('Preco 2', '-')}", size=11, color="#3B82F6", weight=ft.FontWeight.BOLD)], expand=True),
                            ], spacing=10),
                        ], spacing=8), bgcolor=get_surface(), padding=15, border_radius=8)
                    results_container.controls.append(card)
                    results_container.controls.append(ft.Container(height=5))
                
                # Botoes de paginacao
                if total > items_per_page:
                    total_pages = (total + items_per_page - 1) // items_per_page
                    
                    def proxima_pagina(e):
                        if current_page[0] < total_pages - 1:
                            current_page[0] += 1
                            mostrar_resultados(resultados, termo)
                    
                    def pagina_anterior(e):
                        if current_page[0] > 0:
                            current_page[0] -= 1
                            mostrar_resultados(resultados, termo)
                    
                    pagination = ft.Row([
                        ft.ElevatedButton("← Anterior", on_click=pagina_anterior, disabled=current_page[0]==0),
                        ft.Text(f"Página {current_page[0]+1} de {total_pages}", color=get_text_color()),
                        ft.ElevatedButton("Próxima →", on_click=proxima_pagina, disabled=current_page[0]>=total_pages-1),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
                    results_container.controls.append(ft.Container(height=10))
                    results_container.controls.append(pagination)
            
            page.update()
        
        def pesquisar(e):
            current_page[0] = 0  # Reset para primeira pagina
            if df is None or df.empty: return
            termo = search_field.value.strip().lower() if search_field.value else ""
            
            if not termo:
                # Mostrar todos os produtos (primeiros 100)
                mostrar_resultados(df, "")
            else:
                # Filtrar por termo
                mask = df["codigo_produto"].astype(str).str.lower().str.contains(termo, na=False)
                if "sku_seller" in df.columns:
                    mask = mask | df["sku_seller"].astype(str).str.lower().str.contains(termo, na=False)
                resultados = df[mask]
                mostrar_resultados(resultados, termo)
        
        search_field.on_submit = pesquisar
        
        # Carregar primeiros 100 produtos automaticamente
        if df is not None and not df.empty:
            mostrar_resultados(df.head(items_per_page * 10), "")  # Carregar ate 1000 produtos inicialmente
        
        return ft.Container(content=ft.Column([
                ft.Row([search_field, ft.ElevatedButton("Filtrar", icon=ft.Icons.SEARCH, on_click=pesquisar, bgcolor="#3B82F6", color="#FFF")], spacing=10),
                ft.Container(height=10), results_container,
            ]), expand=True, padding=15)
            
    # ======================= ABA OPORTUNIDADES (GAP LUCRO) =======================
    def criar_aba_oportunidades():
        df = df_global[0]
        if df is None or df.empty: return ft.Container()
        
        df_opp = analisar_gap_lucro(df)
        
        if df_opp.empty:
            return ft.Container(content=ft.Text("Nenhuma oportunidade de aumento de margem detectada no momento.", color=get_text_color()), padding=40)
        
        # Estado de paginação
        items_per_page = 100
        current_page = [0]
        total_opp = len(df_opp)
        total_pages = (total_opp + items_per_page - 1) // items_per_page
        ganho_total = df_opp["Ganho Potencial"].sum()
        
        # Container para os cards
        cards_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        page_info = ft.Text("", size=12, color=get_text_color())
        page_number_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=get_text_color())
        
        def atualizar_cards():
            cards_container.controls.clear()
            start_idx = current_page[0] * items_per_page
            end_idx = min(start_idx + items_per_page, total_opp)
            
            page_info.value = f"Exibindo {start_idx + 1} - {end_idx} de {total_opp} oportunidades"
            page_number_text.value = f"Página {current_page[0] + 1} de {total_pages}"
            
            for idx, row in df_opp.iloc[start_idx:end_idx].iterrows():
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(f"SKU: {row['codigo_produto']}", weight=ft.FontWeight.BOLD, color=get_text_color()),
                                ft.Text(f"{str(row.get('nome_esperado', ''))[:40]}", size=11, color=get_text_color(), italic=True) if row.get('nome_esperado') else ft.Container(),
                            ], spacing=2, expand=True),
                            ft.Text(f"(SKU Seller: {row.get('sku_seller', '-')})", size=11, color=get_text_color(), opacity=0.7) if "sku_seller" in row else ft.Container(),
                            ft.Text(f"+ R$ {row['Ganho Potencial']:.2f}", color="#10B981", weight=ft.FontWeight.BOLD, size=16),
                        ]),
                        ft.Divider(height=1),
                        ft.Row([
                            ft.Column([
                                ft.Text("Seu Preço (Atual)", size=10, color=get_text_color(), opacity=0.7),
                                ft.Text(f"R$ {row['Preco 1']:.2f}", weight=ft.FontWeight.BOLD, color="#EF4444"),
                                ft.Text(f"Frete: R$ {row.get('Frete 1', 0):.2f}" if row.get('Frete 1', 0) > 0 else "Frete: Grátis", size=9, color=get_text_color(), opacity=0.6),
                            ], expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=get_text_color()),
                            ft.Column([
                                ft.Text(f"Concorrente ({row.get('Posicao Concorrente', 2)}º lugar)", size=10, color=get_text_color(), opacity=0.7),
                                ft.Text(f"R$ {row.get('Preco Concorrente', row.get('Preco 2', 0)):.2f}", weight=ft.FontWeight.BOLD, color="#3B82F6"),
                                ft.Text(f"{str(row.get('Concorrente', row.get('Vendedor 2', '-')))[:18]}", size=9, color=get_text_color(), opacity=0.6),
                                ft.Text(f"Frete: R$ {row.get('Frete Concorrente', 0):.2f}" if row.get('Frete Concorrente', 0) > 0 else "Frete: Grátis", size=8, color=get_text_color(), opacity=0.5),
                            ], expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color="#10B981"),
                             ft.Column([
                                ft.Text("Preço Ideal", size=10, color="#10B981", weight=ft.FontWeight.BOLD),
                                ft.Text(f"R$ {row['Preco Ideal']:.2f}", weight=ft.FontWeight.BOLD, color="#10B981"),
                            ], expand=True),
                        ], spacing=5),
                    ]),
                    bgcolor=get_surface(),
                    padding=15,
                    border_radius=8,
                    border=ft.border.all(1, "#10B981")
                )
                cards_container.controls.append(card)
            
            page.update()
        
        def ir_pagina_anterior(e):
            if current_page[0] > 0:
                current_page[0] -= 1
                atualizar_cards()
        
        def ir_proxima_pagina(e):
            if current_page[0] < total_pages - 1:
                current_page[0] += 1
                atualizar_cards()
        
        def ir_primeira_pagina(e):
            current_page[0] = 0
            atualizar_cards()
        
        def ir_ultima_pagina(e):
            current_page[0] = total_pages - 1
            atualizar_cards()
        
        # Inicializar cards
        atualizar_cards()
        
        # Paginação simplificada com botões fixos
        pagination_row = ft.Row([
            ft.IconButton(ft.Icons.FIRST_PAGE, on_click=ir_primeira_pagina, tooltip="Primeira página"),
            ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=ir_pagina_anterior, tooltip="Anterior"),
            page_number_text,
            ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=ir_proxima_pagina, tooltip="Próxima"),
            ft.IconButton(ft.Icons.LAST_PAGE, on_click=ir_ultima_pagina, tooltip="Última página"),
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    criar_kpi_card("Oportunidades", total_opp, "#10B981"),
                    criar_kpi_card("Ganho Total Estimado Por Venda", f"R$ {ganho_total:.2f}", "#10B981"),
                ]),
                ft.Container(height=10),
                ft.Text("Recomendação: Subir seu preço logo abaixo do concorrente para aumentar margem.", size=13, color=get_text_color()),
                ft.Container(height=5),
                ft.Row([page_info, ft.Container(expand=True), ft.Text(f"Total: {total_pages} páginas | 100 por página", size=11, opacity=0.7, color=get_text_color())]),
                ft.Container(height=5),
                pagination_row,
                ft.Container(height=10),
                cards_container,
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=15,
        )

    # ======================= TABS =======================
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(text="Resumo", icon=ft.Icons.DASHBOARD, content=ft.Container()),
            ft.Tab(text="Precos", icon=ft.Icons.ATTACH_MONEY, content=ft.Container()),
            ft.Tab(text="BuyBox", icon=ft.Icons.EMOJI_EVENTS, content=ft.Container()),
            ft.Tab(text="Color vs Conc.", icon=ft.Icons.COMPARE_ARROWS, content=ft.Container()),
            ft.Tab(text="Substituicoes", icon=ft.Icons.SWAP_HORIZ, content=ft.Container()),
            ft.Tab(text="Pesquisa SKU", icon=ft.Icons.SEARCH, content=ft.Container()),
            ft.Tab(text="Oportunidades", icon=ft.Icons.MONETIZATION_ON, content=ft.Container()), # Nova Aba
        ],
        expand=True,
    )
    
    def on_tab_change(e):
        idx = tabs.selected_index
        if idx == 0: tabs.tabs[0].content = criar_aba_resumo()
        elif idx == 1: tabs.tabs[1].content = criar_aba_precos()
        elif idx == 2: tabs.tabs[2].content = criar_aba_buybox()
        elif idx == 3: tabs.tabs[3].content = criar_aba_color_vs()
        elif idx == 4: tabs.tabs[4].content = criar_aba_substituicoes()
        elif idx == 5: tabs.tabs[5].content = criar_aba_sku()
        elif idx == 6: tabs.tabs[6].content = criar_aba_oportunidades()
        page.update()
    
    tabs.on_change = on_tab_change
    
    def atualizar(e):
        carregar_dados()
        on_tab_change(None)
    
    # Carregar dados e primeira aba
    carregar_dados()
    tabs.tabs[0].content = criar_aba_resumo()
    
    header = ft.Row([
        ft.Text("Analises Avancadas", size=22, weight=ft.FontWeight.BOLD, color=get_text_color()),
        ft.Container(expand=True),
        ft.ElevatedButton(
            "Atualizar Dados",
            icon=ft.Icons.REFRESH,
            on_click=atualizar,
            bgcolor="#3B82F6",
            color="#FFFFFF",
        ),
    ])
    
    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(height=10),
            tabs,
        ]),
        expand=True,
        padding=15,
    )
