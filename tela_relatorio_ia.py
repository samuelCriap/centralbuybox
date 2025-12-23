# tela_relatorio_ia.py - Interface para Relatório de Oportunidades IA
"""
Tela de relatório com análise histórica e recomendações de IA
"""
import flet as ft
import pandas as pd
from datetime import datetime
from pathlib import Path
from relatorio_historico_ia import gerar_relatorio_completo


REL_DIR = Path("data/relatorios")
REL_DIR.mkdir(parents=True, exist_ok=True)


def criar_tela_relatorio_ia(page: ft.Page, is_dark: list):
    """Cria tela de relatório de oportunidades IA"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    # Estado
    relatorio_data = [None]
    periodo_selecionado = [30]  # Dias
    
    # Componentes UI
    status_text = ft.Text("", size=12)
    conteudo_relatorio = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
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
    
    def gerar_relatorio(e):
        """Gera o relatório baseado no período selecionado"""
        status_text.value = "Gerando relatório..."
        status_text.color = "#3B82F6"
        page.update()
        
        try:
            # Gerar relatório
            resultado = gerar_relatorio_completo(periodo_selecionado[0])
            
            if resultado is None:
                status_text.value = "Nenhum dado histórico encontrado. Execute 'python main.py' primeiro."
                status_text.color = "#EF4444"
                page.update()
                return
            
            relatorio_data[0] = resultado
            
            # Exibir resultados
            mostrar_relatorio()
            
            status_text.value = f"Relatório gerado com sucesso! Período: {periodo_selecionado[0]} dias"
            status_text.color = "#22C55E"
            page.update()
            
        except Exception as ex:
            status_text.value = f"Erro ao gerar relatório: {str(ex)}"
            status_text.color = "#EF4444"
            page.update()
    
    def mostrar_relatorio():
        """Exibe o relatório na tela"""
        conteudo_relatorio.controls.clear()
        
        if relatorio_data[0] is None:
            return
        
        dados = relatorio_data[0]
        resumo = dados['recomendacoes']['resumo']
        
        # ===== RESUMO EXECUTIVO =====
        conteudo_relatorio.controls.append(
            ft.Text("📊 Resumo Executivo", size=18, weight=ft.FontWeight.BOLD, color=get_text_color())
        )
        conteudo_relatorio.controls.append(ft.Container(height=10))
        
        conteudo_relatorio.controls.append(
            ft.Row([
                criar_kpi_card("Total SKUs", f"{resumo['Total SKUs']:,}", "#3B82F6"),
                criar_kpi_card("Baixa Concorrência", f"{resumo['Baixa Concorrencia']:,}", "#22C55E", f"{resumo['Baixa Concorrencia']/resumo['Total SKUs']*100:.0f}%" if resumo['Total SKUs'] > 0 else ""),
                criar_kpi_card("Alta Concorrência", f"{resumo['Alta Concorrencia']:,}", "#EF4444", f"{resumo['Alta Concorrencia']/resumo['Total SKUs']*100:.0f}%" if resumo['Total SKUs'] > 0 else ""),
                criar_kpi_card("Color em 1º", f"{resumo['Color em 1o']:,}", "#8B5CF6", f"{resumo['Taxa BuyBox']:.1f}%"),
                criar_kpi_card("Preço Médio", f"R$ {resumo['Preco Medio Geral']:.2f}", "#14B8A6"),
            ], spacing=10)
        )
        
        conteudo_relatorio.controls.append(ft.Container(height=20))
        
        # ===== AUMENTAR MARGEM =====
        investir = dados['recomendacoes']['investir_mais']
        conteudo_relatorio.controls.append(
            ft.Text(f"💰 SKUs para Aumentar a Margem de Lucro ({len(investir)} oportunidades)", size=16, weight=ft.FontWeight.BOLD, color="#22C55E")
        )
        conteudo_relatorio.controls.append(ft.Text("Baixa concorrência + Color em 1º lugar", size=12, color=get_text_color(), opacity=0.7))
        conteudo_relatorio.controls.append(ft.Container(height=5))
        
        if not investir.empty:
            for idx, row in investir.head(10).iterrows():
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(f"SKU: {row['SKU']}", weight=ft.FontWeight.BOLD, color=get_text_color()),
                                ft.Text(f"SKU Seller: {row.get('SKU Seller', '-')}", size=10, color=get_text_color(), opacity=0.7),
                                ft.Text(f"{row['Nome']}", size=11, color=get_text_color(), italic=True),
                            ], expand=True),
                            ft.Container(
                                content=ft.Text(row['Nivel Concorrencia'], size=10, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                                bgcolor="#22C55E",
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4
                            ),
                        ]),
                        ft.Row([
                            ft.Text(f"Preço Médio: R$ {row['Preco Medio']:.2f}", size=12, color=get_text_color()),
                            ft.Text(f"Vendedores: {row['Num Vendedores']}", size=12, color=get_text_color()),
                        ], spacing=20),
                    ], spacing=5),
                    bgcolor=get_surface(),
                    padding=12,
                    border_radius=8,
                    border=ft.border.all(1, "#22C55E")
                )
                conteudo_relatorio.controls.append(card)
                conteudo_relatorio.controls.append(ft.Container(height=5))
        else:
            conteudo_relatorio.controls.append(ft.Text("Nenhuma oportunidade encontrada", color=get_text_color(), opacity=0.5))
        
        conteudo_relatorio.controls.append(ft.Container(height=20))
        
        # ===== MONITORAR =====
        monitorar = dados['recomendacoes']['monitorar']
        conteudo_relatorio.controls.append(
            ft.Text(f"⚠️ SKUs para Monitorar ({len(monitorar)} itens)", size=16, weight=ft.FontWeight.BOLD, color="#EF4444")
        )
        conteudo_relatorio.controls.append(ft.Text("Alta concorrência - acompanhar de perto", size=12, color=get_text_color(), opacity=0.7))
        conteudo_relatorio.controls.append(ft.Container(height=5))
        
        if not monitorar.empty:
            for idx, row in monitorar.head(10).iterrows():
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(f"SKU: {row['SKU']}", weight=ft.FontWeight.BOLD, color=get_text_color()),
                                ft.Text(f"SKU Seller: {row.get('SKU Seller', '-')}", size=10, color=get_text_color(), opacity=0.7),
                                ft.Text(f"{row['Nome']}", size=11, color=get_text_color(), italic=True),
                            ], expand=True),
                            ft.Text(f"{row['Num Vendedores']} vendedores", size=12, color="#EF4444", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text(f"Vendedores: {row['Vendedores']}", size=11, color=get_text_color(), opacity=0.7),
                    ], spacing=5),
                    bgcolor=get_surface(),
                    padding=12,
                    border_radius=8,
                )
                conteudo_relatorio.controls.append(card)
                conteudo_relatorio.controls.append(ft.Container(height=5))
        else:
            conteudo_relatorio.controls.append(ft.Text("Nenhum SKU com alta concorrência", color=get_text_color(), opacity=0.5))
        
        page.update()
    
    def exportar_excel(e):
        """Exporta relatório para Excel usando FilePicker"""
        if relatorio_data[0] is None:
            status_text.value = "⚠️ Gere o relatório primeiro antes de exportar"
            status_text.color = "#EF4444"
            page.update()
            return
        
        # Usar FilePicker para escolher onde salvar
        file_picker = ft.FilePicker()
        page.overlay.append(file_picker)
        page.update()
        
        def on_save_result(result: ft.FilePickerResultEvent):
            if not result.path:
                status_text.value = "Exportação cancelada"
                status_text.color = "#EF4444"
                page.update()
                return
            
            try:
                dados = relatorio_data[0]
                filename = result.path if result.path.endswith('.xlsx') else result.path + '.xlsx'
                
                with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                    # Análise completa
                    if 'analise_completa' in dados and not dados['analise_completa'].empty:
                        dados['analise_completa'].to_excel(writer, sheet_name="Analise Completa", index=False)
                    
                    # Recomendações
                    if 'recomendacoes' in dados:
                        recs = dados['recomendacoes']
                        if 'investir_mais' in recs and not recs['investir_mais'].empty:
                            recs['investir_mais'].to_excel(writer, sheet_name="Aumentar Margem", index=False)
                        if 'monitorar' in recs and not recs['monitorar'].empty:
                            recs['monitorar'].to_excel(writer, sheet_name="Monitorar", index=False)
                        if 'otimizar_preco' in recs and not recs['otimizar_preco'].empty:
                            recs['otimizar_preco'].to_excel(writer, sheet_name="Otimizar Preco", index=False)
                        
                        # Resumo
                        if 'resumo' in recs:
                            resumo_df = pd.DataFrame([recs['resumo']])
                            resumo_df.to_excel(writer, sheet_name="Resumo", index=False)
                
                status_text.value = f"✅ Relatório exportado com sucesso!"
                status_text.color = "#22C55E"
                page.update()
                
            except Exception as ex:
                status_text.value = f"Erro ao exportar: {str(ex)}"
                status_text.color = "#EF4444"
                page.update()
        
        file_picker.on_result = on_save_result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_picker.save_file(
            dialog_title="Salvar Relatório Oportunidades IA",
            file_name=f"oportunidades_ia_{periodo_selecionado[0]}dias_{timestamp}.xlsx",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
        )
    
    def atualizar_periodo(e):
        """Atualiza o período selecionado"""
        periodo_selecionado[0] = int(e.control.value)
    
    # ===== INTERFACE =====
    header = ft.Row([
        ft.Text("🤖 Oportunidades IA - Análise Histórica", size=22, weight=ft.FontWeight.BOLD, color=get_text_color()),
        ft.Container(expand=True),
        ft.ElevatedButton(
            "Exportar Excel",
            icon=ft.Icons.DOWNLOAD,
            on_click=exportar_excel,
            bgcolor="#22C55E",
            color="#FFFFFF",
        ),
    ])
    
    # Seleção de período
    periodo_selector = ft.Row([
        ft.Text("Período de análise:", size=14, color=get_text_color()),
        ft.Dropdown(
            width=150,
            value="30",
            options=[
                ft.dropdown.Option("7", "7 dias"),
                ft.dropdown.Option("15", "15 dias"),
                ft.dropdown.Option("30", "30 dias"),
                ft.dropdown.Option("60", "60 dias"),
            ],
            on_change=atualizar_periodo,
        ),
        ft.ElevatedButton(
            "Gerar Relatório",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=gerar_relatorio,
            bgcolor="#3B82F6",
            color="#FFFFFF",
        ),
    ], spacing=10)
    
    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(height=10),
            periodo_selector,
            ft.Container(height=5),
            status_text,
            ft.Container(height=15),
            conteudo_relatorio,
        ]),
        expand=True,
        padding=15,
    )
