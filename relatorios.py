# relatorios.py - Tela de Relatorios com exportacao Excel/CSV
"""
Interface para geracao de relatorios:
- Precos
- BuyBox Wins
- Color vs Concorrencia
- Substituicoes
- Volatilidade
- Oportunidades de Lucro (NOVO)
- Dados Brutos
"""
import flet as ft
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from db_client import ler_planilha, ler_historico
from oportunidades_ia import analisar_gap_lucro


REL_DIR = Path("data/relatorios")
REL_DIR.mkdir(parents=True, exist_ok=True)


def criar_tela_relatorios(page: ft.Page, file_picker: ft.FilePicker, is_dark: list):
    """Cria a tela de relatorios"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    # Status
    status_text = ft.Text("", size=12)
    
    # Estado do período selecionado
    periodo_selecionado = [7]  # Padrão: 7 dias
    
    # Dropdown de período
    dropdown_periodo = ft.Dropdown(
        label="Período",
        value="7",
        width=200,
        options=[
            ft.dropdown.Option("1", "Último dia"),
            ft.dropdown.Option("7", "Últimos 7 dias"),
            ft.dropdown.Option("30", "Últimos 30 dias"),
            ft.dropdown.Option("60", "Últimos 60 dias"),
            ft.dropdown.Option("90", "Últimos 90 dias"),
            ft.dropdown.Option("0", "Todos os dados"),
        ],
        on_change=lambda e: atualizar_periodo(e),
    )
    
    def atualizar_periodo(e):
        periodo_selecionado[0] = int(e.control.value)
        status_text.value = f"Período selecionado: {periodo_selecionado[0]} dias" if periodo_selecionado[0] > 0 else "Período: Todos os dados"
        status_text.color = "#3B82F6"
        page.update()
    
    def filtrar_por_periodo(df, dias):
        """Filtra o DataFrame pelo período selecionado"""
        if dias == 0 or "Data Verificacao" not in df.columns:
            return df
        
        try:
            # Converter coluna de data
            df_copy = df.copy()
            df_copy["_data_dt"] = pd.to_datetime(df_copy["Data Verificacao"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
            
            # Se falhou, tentar outro formato
            if df_copy["_data_dt"].isna().all():
                df_copy["_data_dt"] = pd.to_datetime(df_copy["Data Verificacao"], dayfirst=True, errors="coerce")
            
            # Filtrar por data
            data_limite = datetime.now() - timedelta(days=dias)
            df_filtrado = df_copy[df_copy["_data_dt"] >= data_limite].drop(columns=["_data_dt"])
            
            return df_filtrado
        except Exception:
            return df
    
    # Checkboxes para selecao de relatorios
    check_precos = ft.Checkbox(label="Precos por Vendedor", value=True)
    check_buybox = ft.Checkbox(label="BuyBox Wins", value=True)
    check_color_vs = ft.Checkbox(label="Color vs Concorrencia", value=True)
    check_substituicoes = ft.Checkbox(label="Substituicoes", value=True)
    check_volatilidade = ft.Checkbox(label="Volatilidade de Precos", value=False)
    check_oportunidades = ft.Checkbox(label="Oportunidades de Lucro (Gap)", value=True)
    check_brutos = ft.Checkbox(label="Dados Brutos (Tabela Completa)", value=True)
    
    # Variáveis para armazenar dados temporariamente
    dados_exportar = [None]  # Dados atuais (produtos)
    dados_historico = [None]  # Dados históricos
    
    def on_save_excel_result(e: ft.FilePickerResultEvent):
        """Callback quando usuário escolhe onde salvar Excel"""
        if not e.path:
            status_text.value = "Exportação cancelada"
            status_text.color = ft.Colors.ORANGE_400
            page.update()
            return
        
        filename = e.path if e.path.endswith('.xlsx') else e.path + '.xlsx'
        
        try:
            # Dados ATUAIS (produtos) - para Oportunidades e Dados Brutos
            df_atual = dados_exportar[0]
            # Dados HISTÓRICOS - para análises históricas
            df_hist = dados_historico[0]
            
            # Verificar se pelo menos um tem dados
            has_atual = df_atual is not None and not df_atual.empty
            has_hist = df_hist is not None and not df_hist.empty
            
            if not has_atual and not has_hist:
                status_text.value = "Erro: Nenhum dado disponível"
                status_text.color = ft.Colors.RED_400
                page.update()
                return
            
            with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                
                # ======= DADOS BRUTOS (usa dados ATUAIS) =======
                if check_brutos.value and has_atual:
                    df_atual.to_excel(writer, sheet_name="Dados Brutos", index=False)
                
                # ======= OPORTUNIDADES DE LUCRO (usa dados ATUAIS) =======
                if check_oportunidades.value and has_atual:
                    df_opp = analisar_gap_lucro(df_atual)
                    if not df_opp.empty:
                        df_opp.to_excel(writer, sheet_name="Oportunidades de Lucro", index=False)
                    else:
                        pd.DataFrame({"Info": ["Nenhuma oportunidade detectada"]}).to_excel(writer, sheet_name="Oportunidades de Lucro", index=False)

                # ======= PRECOS POR VENDEDOR (usa HISTÓRICO) =======
                if check_precos.value and has_hist:
                    df = df_hist  # Usar histórico
                    vendedor_precos = {}
                    for v_col, p_col in [("vendedor_1", "preco_1"), ("vendedor_2", "preco_2"), ("vendedor_3", "preco_3")]:
                        if v_col in df.columns and p_col in df.columns:
                            for idx, row in df.iterrows():
                                v = str(row.get(v_col, "-"))
                                p = row.get(p_col, "-")
                                if v != "-" and v != "" and p != "-" and p != "":
                                    try:
                                        pf = float(str(p).replace(",", "."))
                                        if v not in vendedor_precos:
                                            vendedor_precos[v] = []
                                        vendedor_precos[v].append(pf)
                                    except:
                                        pass
                    
                    if vendedor_precos:
                        preco_data = []
                        for v, precos in sorted(vendedor_precos.items(), key=lambda x: sum(x[1])/len(x[1])):
                            preco_data.append({
                                "Vendedor": v,
                                "Qtd Ofertas": len(precos),
                                "Preco Medio": round(sum(precos)/len(precos), 2),
                                "Preco Min": round(min(precos), 2),
                                "Preco Max": round(max(precos), 2),
                            })
                        pd.DataFrame(preco_data).to_excel(writer, sheet_name="Precos", index=False)
                
                # ======= BUYBOX WINS (usa HISTÓRICO) =======
                if check_buybox.value and has_hist:
                    df = df_hist  # Usar histórico
                    col_vendedor = "vendedor_1" if "vendedor_1" in df.columns else "Vendedor 1"
                    if col_vendedor in df.columns:
                        contagem = df[col_vendedor].value_counts().reset_index()
                        contagem.columns = ["Vendedor", "BuyBox Wins"]
                        contagem = contagem[(contagem["Vendedor"] != "-") & (contagem["Vendedor"] != "")]
                        if not contagem.empty:
                            total = contagem["BuyBox Wins"].sum()
                            contagem["Percentual"] = (contagem["BuyBox Wins"] / total * 100).round(2)
                            contagem.to_excel(writer, sheet_name="BuyBox Wins", index=False)
                
                # ======= COLOR VS CONCORRENCIA (usa HISTÓRICO) =======
                if check_color_vs.value and has_hist:
                    df = df_hist  # Usar histórico
                    color_precos = []
                    outros_precos = {}
                    
                    for v_col, p_col in [("vendedor_1", "preco_1"), ("vendedor_2", "preco_2"), ("vendedor_3", "preco_3")]:
                        if v_col in df.columns and p_col in df.columns:
                            for idx, row in df.iterrows():
                                v = str(row.get(v_col, "-")).lower()
                                p = row.get(p_col, "-")
                                if v != "-" and v != "" and p != "-" and p != "":
                                    try:
                                        pf = float(str(p).replace(",", "."))
                                        if "color" in v:
                                            color_precos.append(pf)
                                        else:
                                            v_orig = str(row.get(v_col, "-"))
                                            if v_orig not in outros_precos:
                                                outros_precos[v_orig] = []
                                            outros_precos[v_orig].append(pf)
                                    except:
                                        pass
                    
                    media_color = sum(color_precos)/len(color_precos) if color_precos else 0
                    
                    comp_data = []
                    for conc, precos in sorted(outros_precos.items(), key=lambda x: len(x[1]), reverse=True):
                        media_conc = sum(precos)/len(precos)
                        diff = media_color - media_conc
                        comp_data.append({
                            "Concorrente": conc,
                            "Qtd Ofertas": len(precos),
                            "Preco Medio": round(media_conc, 2),
                            "Diff vs Color": round(diff, 2),
                            "Color Mais Barato": "Sim" if diff < 0 else "Nao"
                        })
                    
                    if comp_data:
                        df_comp = pd.DataFrame(comp_data)
                        resumo = pd.DataFrame([{
                            "Concorrente": "*** RESUMO COLOR SPORTS ***",
                            "Qtd Ofertas": len(color_precos),
                            "Preco Medio": round(media_color, 2),
                            "Diff vs Color": 0,
                            "Color Mais Barato": ""
                        }])
                        df_comp = pd.concat([resumo, df_comp], ignore_index=True)
                        df_comp.to_excel(writer, sheet_name="Color vs Concorrencia", index=False)
                
                # ======= SUBSTITUICOES (usa HISTÓRICO) =======
                if check_substituicoes.value and has_hist:
                    df = df_hist  # Usar histórico
                    col_vendedor = "vendedor_1" if "vendedor_1" in df.columns else "Vendedor 1"
                    if col_vendedor in df.columns:
                        substituicoes = {}
                        for idx, row in df.iterrows():
                            v1 = str(row.get(col_vendedor, "-")).lower()
                            if "color" not in v1 and v1 != "-" and v1 != "":
                                v1_orig = str(row.get(col_vendedor, "-"))
                                substituicoes[v1_orig] = substituicoes.get(v1_orig, 0) + 1
                        
                        if substituicoes:
                            subs_data = [{"Concorrente": k, "Vezes Ganhou de Color": v} for k, v in sorted(substituicoes.items(), key=lambda x: x[1], reverse=True)]
                            pd.DataFrame(subs_data).to_excel(writer, sheet_name="Substituicoes", index=False)
                
                # ======= VOLATILIDADE (usa HISTÓRICO) =======
                if check_volatilidade.value and has_hist:
                    df = df_hist  # Usar histórico
                    preco_cols = ["preco_1", "preco_2", "preco_3"] if "preco_1" in df.columns else ["Preco 1", "Preco 2", "Preco 3"]
                    if all(c in df.columns for c in preco_cols):
                        df_temp = df.copy()
                        for col in preco_cols:
                            df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce")
                        
                        df_temp["Min Preco"] = df_temp[preco_cols].min(axis=1)
                        df_temp["Max Preco"] = df_temp[preco_cols].max(axis=1)
                        df_temp["Amplitude"] = df_temp["Max Preco"] - df_temp["Min Preco"]
                        
                        # Selecionar colunas que existem
                        cols_vol = []
                        if "codigo_produto" in df_temp.columns: cols_vol.append("codigo_produto")
                        if "sku_seller" in df_temp.columns: cols_vol.append("sku_seller")
                        if "nome_esperado" in df_temp.columns: cols_vol.append("nome_esperado")
                        cols_vol.extend(["Min Preco", "Max Preco", "Amplitude"])
                        
                        # Filtrar apenas colunas que existem
                        cols_vol = [c for c in cols_vol if c in df_temp.columns]
                        
                        if cols_vol:
                            vol = df_temp[cols_vol].copy()
                            vol = vol.dropna(subset=["Amplitude"])
                            vol = vol[vol["Amplitude"] > 0].sort_values("Amplitude", ascending=False).head(200)
                            if not vol.empty:
                                vol.to_excel(writer, sheet_name="Volatilidade", index=False)
            
            status_text.value = f"✅ Relatório salvo: {filename}"
            status_text.color = "#22C55E"
            
        except Exception as ex:
            status_text.value = f"Erro: {ex}"
            status_text.color = ft.Colors.RED_400
        
        page.update()
    
    # Configurar callback do file_picker para Excel
    file_picker.on_result = on_save_excel_result
    
    def gerar_relatorio_excel(e):
        """Gera relatorio Excel com abas selecionadas (filtrado por período)"""
        status_text.value = "Carregando dados..."
        status_text.color = "#3B82F6"
        page.update()
        
        try:
            # Carregar dados ATUAIS (para Oportunidades e Dados Brutos)
            df_atual = ler_planilha()
            
            # Carregar dados HISTÓRICOS (para análises históricas)
            df_hist = ler_historico()
            
            if (df_atual is None or df_atual.empty) and (df_hist is None or df_hist.empty):
                status_text.value = "Erro: Nenhum dado disponivel. Execute 'python main.py' primeiro."
                status_text.color = ft.Colors.RED_400
                page.update()
                return
            
            # Aplicar filtro de período aos dados atuais
            if df_atual is not None and not df_atual.empty:
                df_atual = filtrar_por_periodo(df_atual, periodo_selecionado[0])
            
            # Aplicar filtro de período aos dados históricos
            if df_hist is not None and not df_hist.empty:
                df_hist = filtrar_por_periodo(df_hist, periodo_selecionado[0])
            
            # Armazenar dados para o callback
            dados_exportar[0] = df_atual
            dados_historico[0] = df_hist
            
            total_atual = len(df_atual) if df_atual is not None and not df_atual.empty else 0
            total_hist = len(df_hist) if df_hist is not None and not df_hist.empty else 0
            status_text.value = f"Dados atuais: {total_atual}, Histórico: {total_hist}. Escolha onde salvar..."
            page.update()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            periodo_str = f"{periodo_selecionado[0]}dias" if periodo_selecionado[0] > 0 else "todos"
            
            # Configurar callback e abrir diálogo
            file_picker.on_result = on_save_excel_result
            file_picker.save_file(
                dialog_title="Salvar Relatório Excel",
                file_name=f"relatorio_netshoes_{periodo_str}_{timestamp}.xlsx",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"]
            )
            
        except Exception as ex:
            status_text.value = f"Erro: {ex}"
            status_text.color = ft.Colors.RED_400
        
        page.update()
    
    def on_save_csv_result(e: ft.FilePickerResultEvent):
        """Callback quando usuário escolhe onde salvar CSV"""
        if not e.path:
            status_text.value = "Exportação cancelada"
            status_text.color = ft.Colors.ORANGE_400
            page.update()
            return
        
        filename = e.path if e.path.endswith('.csv') else e.path + '.csv'
        
        try:
            df = dados_exportar[0]
            if df is None or df.empty:
                status_text.value = "Erro: Nenhum dado disponível"
                status_text.color = ft.Colors.RED_400
                page.update()
                return
            
            # Exportar CSV com separador ; para Excel brasileiro
            df.to_csv(filename, index=False, encoding="utf-8-sig", sep=";", decimal=",")
            
            status_text.value = f"✅ CSV salvo: {filename}"
            status_text.color = "#22C55E"
            
        except Exception as ex:
            status_text.value = f"Erro: {ex}"
            status_text.color = ft.Colors.RED_400
        
        page.update()
    
    def baixar_csv(e):
        """Baixa tabela completa como CSV (filtrado por período)"""
        status_text.value = "Carregando dados..."
        status_text.color = "#3B82F6"
        page.update()
        
        try:
            df = ler_planilha()
            if df is None or df.empty:
                status_text.value = "Nenhum dado para exportar"
                status_text.color = ft.Colors.RED_400
                page.update()
                return
            
            # Aplicar filtro de período
            df = filtrar_por_periodo(df, periodo_selecionado[0])
            
            if df.empty:
                status_text.value = f"Nenhum dado encontrado no período de {periodo_selecionado[0]} dias"
                status_text.color = ft.Colors.ORANGE_400
                page.update()
                return
            
            # Armazenar para callback
            dados_exportar[0] = df
            
            total_registros = len(df)
            status_text.value = f"Encontrados {total_registros} registros. Escolha onde salvar..."
            page.update()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            periodo_str = f"{periodo_selecionado[0]}dias" if periodo_selecionado[0] > 0 else "todos"
            
            # Configurar callback e abrir diálogo
            file_picker.on_result = on_save_csv_result
            file_picker.save_file(
                dialog_title="Salvar CSV",
                file_name=f"dados_netshoes_{periodo_str}_{timestamp}.csv",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["csv"]
            )
            
        except Exception as ex:
            status_text.value = f"Erro: {ex}"
            status_text.color = ft.Colors.RED_400
        
        page.update()
    
    # Layout
    header = ft.Row([
        ft.Text("Relatorios", size=24, weight=ft.FontWeight.BOLD, color=get_text_color()),
    ])
    
    descricao = ft.Text(
        "Exporte os dados coletados para Excel ou CSV para analise externa.",
        size=13, color=get_text_color(), opacity=0.7
    )
    
    filtro_periodo = ft.Container(
        content=ft.Row([
            ft.Text("📅 Período para exportação:", size=14, weight=ft.FontWeight.BOLD, color=get_text_color()),
            dropdown_periodo,
        ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=get_surface(),
        padding=15,
        border_radius=10,
    )
    
    selecao = ft.Container(
        content=ft.Column([
            ft.Text("Selecione os relatorios para incluir no Excel:", size=14, weight=ft.FontWeight.BOLD, color=get_text_color()),
            ft.Container(height=10),
            ft.Row([check_precos, check_buybox, check_color_vs], spacing=20),
            ft.Row([check_substituicoes, check_oportunidades, check_volatilidade], spacing=20),
            ft.Row([check_brutos], spacing=20),
        ], spacing=8),
        bgcolor=get_surface(),
        padding=20,
        border_radius=10,
    )
    
    botoes = ft.Row([
        ft.ElevatedButton(
            "Gerar Relatorio Excel",
            icon=ft.Icons.DOWNLOAD,
            on_click=gerar_relatorio_excel,
            bgcolor="#3B82F6",
            color="#FFFFFF",
            height=45,
        ),
        ft.ElevatedButton(
            "Baixar Dados Brutos (CSV)",
            icon=ft.Icons.TABLE_CHART,
            on_click=baixar_csv,
            bgcolor="#22C55E",
            color="#FFFFFF",
            height=45,
        ),
    ], spacing=15)
    
    info = ft.Container(
        content=ft.Column([
            ft.Text("Descricao dos relatorios:", size=13, weight=ft.FontWeight.BOLD, color=get_text_color()),
            ft.Text("• Oportunidades de Lucro: SKUs onde Color BuyBox > Preco 2 (Chance de subir preco)", size=12, color=get_text_color(), opacity=0.8, weight=ft.FontWeight.BOLD),
            ft.Text("• Precos: Preco medio, min e max por vendedor", size=12, color=get_text_color(), opacity=0.8),
            ft.Text("• BuyBox Wins: Ranking de quem ganha mais Buy Box", size=12, color=get_text_color(), opacity=0.8),
            ft.Text("• Color vs Concorrencia: Comparativo de precos", size=12, color=get_text_color(), opacity=0.8),
            ft.Text("• Substituicoes: Quem substitui Color no 1o lugar", size=12, color=get_text_color(), opacity=0.8),
            ft.Text("• Dados Brutos: Tabela completa para manipulacao", size=12, color=get_text_color(), opacity=0.8),
        ], spacing=5),
        bgcolor=get_surface(),
        padding=15,
        border_radius=10,
    )
    
    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(height=10),
            descricao,
            ft.Container(height=15),
            filtro_periodo,
            ft.Container(height=15),
            selecao,
            ft.Container(height=20),
            botoes,
            ft.Container(height=15),
            status_text,
            ft.Container(height=20),
            info,
        ], scroll=ft.ScrollMode.AUTO),
        expand=True,
        padding=20,
    )
