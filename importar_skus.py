# importar_skus.py - Sistema de importação de SKUs via Excel
"""
Permite adicionar/atualizar SKUs através de um arquivo Excel modelo
"""
import flet as ft
import pandas as pd
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime


# Template Excel para importação
TEMPLATE_COLS = ["codigo_produto", "sku_seller", "nome_esperado", "link"]
TEMPLATE_DIR = Path("data/temp")
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)


def criar_dialogo_importar_skus(page: ft.Page, is_dark: list, on_complete=None):
    """Cria e exibe o diálogo de importação de SKUs"""
    
    def get_text_color():
        return "#FFFFFF" if is_dark[0] else "#000000"
    
    def get_surface():
        return "#2D2D2D" if is_dark[0] else "#F5F5F5"
    
    # Estado
    dados_importados = [None]
    excel_path = [None]
    
    # Container de status
    status_container = ft.Column(spacing=10)
    
    def fechar_dialogo(e=None):
        page.close(dialogo)
    
    def criar_template_excel():
        """Cria o arquivo Excel modelo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = TEMPLATE_DIR / f"importar_skus_{timestamp}.xlsx"
        
        # Criar DataFrame vazio com as colunas
        df_template = pd.DataFrame(columns=TEMPLATE_COLS)
        
        # Adicionar algumas linhas de exemplo
        df_template.loc[0] = ["D23-2094-028-01", "0036-9-39-44", "MEIÃO MATIS PENALTY VIII EXEMPLO", "https://www.netshoes.com.br/D23-2094-028-01"]
        df_template.loc[1] = ["", "", "", ""]  # Linha vazia para o usuário preencher
        
        # Salvar como Excel
        df_template.to_excel(path, index=False, sheet_name="SKUs")
        
        return path
    
    def abrir_excel_e_aguardar(path):
        """Abre o Excel e aguarda o usuário fechar"""
        status_container.controls.clear()
        status_container.controls.append(
            ft.Row([
                ft.ProgressRing(width=20, height=20),
                ft.Text("Abrindo Excel... Preencha os dados e FECHE o arquivo.", color=get_text_color()),
            ], spacing=10)
        )
        page.update()
        
        # Abrir Excel
        os.startfile(str(path))
        
        # Aguardar um pouco para o Excel abrir
        time.sleep(2)
        
        # Verificar periodicamente se o arquivo foi fechado
        status_container.controls.clear()
        status_container.controls.append(
            ft.Row([
                ft.ProgressRing(width=20, height=20),
                ft.Text("Aguardando você fechar o arquivo Excel...", color=get_text_color()),
            ], spacing=10)
        )
        status_container.controls.append(
            ft.ElevatedButton(
                "Já fechei o arquivo",
                icon=ft.Icons.CHECK,
                on_click=lambda e: verificar_arquivo_fechado(path),
                bgcolor="#22C55E",
                color="#FFFFFF",
            )
        )
        page.update()
    
    def verificar_arquivo_fechado(path):
        """Verifica se o arquivo Excel foi fechado e lê os dados"""
        try:
            # Tentar abrir o arquivo para verificar se está liberado
            with open(path, 'rb') as f:
                pass
            
            # Ler os dados
            df = pd.read_excel(path)
            
            # Limpar linhas vazias
            df = df.dropna(how='all')
            df = df[df['codigo_produto'].notna() & (df['codigo_produto'] != '')]
            
            if df.empty:
                status_container.controls.clear()
                status_container.controls.append(
                    ft.Text("⚠️ Nenhum SKU válido encontrado no arquivo.", color="#EF4444")
                )
                status_container.controls.append(
                    ft.ElevatedButton("Tentar Novamente", on_click=lambda e: iniciar_importacao(None))
                )
                page.update()
                return
            
            dados_importados[0] = df
            excel_path[0] = path
            
            # Mostrar confirmação
            mostrar_confirmacao(df)
            
        except PermissionError:
            status_container.controls.clear()
            status_container.controls.append(
                ft.Text("⚠️ O arquivo ainda está aberto. Feche o Excel primeiro.", color="#EF4444")
            )
            status_container.controls.append(
                ft.ElevatedButton(
                    "Já fechei o arquivo",
                    on_click=lambda e: verificar_arquivo_fechado(path),
                    bgcolor="#22C55E",
                    color="#FFFFFF",
                )
            )
            page.update()
        except Exception as ex:
            status_container.controls.clear()
            status_container.controls.append(
                ft.Text(f"❌ Erro ao ler arquivo: {ex}", color="#EF4444")
            )
            page.update()
    
    def mostrar_confirmacao(df):
        """Abre segunda janela com preview dos dados a serem importados"""
        from db_client import ler_planilha
        
        # Verificar SKUs existentes
        df_existente = ler_planilha()
        skus_existentes = set()
        if df_existente is not None and not df_existente.empty:
            if 'sku_seller' in df_existente.columns:
                skus_existentes = set(df_existente['sku_seller'].dropna().astype(str).tolist())
        
        # Classificar novos vs atualizações
        novos = []
        atualizacoes = []
        for _, row in df.iterrows():
            sku_seller = str(row.get('sku_seller', ''))
            if sku_seller in skus_existentes:
                atualizacoes.append(row)
            else:
                novos.append(row)
        
        # Criar segunda janela de confirmação
        def fechar_confirmacao(e=None):
            page.close(dialogo_confirmacao)
        
        def confirmar_e_importar(e):
            page.close(dialogo_confirmacao)
            executar_importacao(df, novos, atualizacoes)
        
        # Lista dos primeiros 10 SKUs
        preview_list = ft.Column(spacing=8, height=250, scroll=ft.ScrollMode.AUTO)
        for _, row in df.head(10).iterrows():
            sku_seller = str(row.get('sku_seller', '-'))
            is_update = sku_seller in skus_existentes
            preview_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.UPDATE if is_update else ft.Icons.ADD_CIRCLE, 
                               color="#EAB308" if is_update else "#22C55E", size=18),
                        ft.Column([
                            ft.Text(f"{row.get('codigo_produto', '-')}", size=12, weight=ft.FontWeight.BOLD, color=get_text_color()),
                            ft.Text(f"SKU Seller: {sku_seller}", size=10, color=get_text_color(), opacity=0.7),
                        ], spacing=0, expand=True),
                        ft.Container(
                            content=ft.Text("ATUALIZAR" if is_update else "NOVO", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                            bgcolor="#EAB308" if is_update else "#22C55E",
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=4,
                        ),
                    ], spacing=10),
                    bgcolor=get_surface(),
                    padding=8,
                    border_radius=6,
                )
            )
        
        if len(df) > 10:
            preview_list.controls.append(ft.Text(f"... e mais {len(df) - 10} SKUs", opacity=0.5, color=get_text_color()))
        
        # Conteúdo da segunda janela
        conteudo_confirmacao = ft.Column([
            ft.Text("📋 Confirme a Importação", size=20, weight=ft.FontWeight.BOLD, color=get_text_color()),
            ft.Divider(),
            
            # Resumo em cards
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Total de SKUs", size=11, opacity=0.7, color=get_text_color()),
                        ft.Text(str(len(df)), size=28, weight=ft.FontWeight.BOLD, color="#3B82F6"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=get_surface(),
                    padding=15,
                    border_radius=8,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Novos SKUs", size=11, opacity=0.7, color=get_text_color()),
                        ft.Text(str(len(novos)), size=28, weight=ft.FontWeight.BOLD, color="#22C55E"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=get_surface(),
                    padding=15,
                    border_radius=8,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Atualizações", size=11, opacity=0.7, color=get_text_color()),
                        ft.Text(str(len(atualizacoes)), size=28, weight=ft.FontWeight.BOLD, color="#EAB308"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=get_surface(),
                    padding=15,
                    border_radius=8,
                    expand=True,
                ),
            ], spacing=10),
            
            ft.Container(height=10),
            ft.Text("📝 Prévia dos 10 primeiros SKUs:", size=12, weight=ft.FontWeight.BOLD, color=get_text_color()),
            ft.Container(height=5),
            preview_list,
        ], spacing=10, width=550)
        
        dialogo_confirmacao = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECKLIST, color="#3B82F6"),
                ft.Text("Confirmar Importação"),
            ]),
            content=conteudo_confirmacao,
            actions=[
                ft.ElevatedButton(
                    "Cancelar",
                    icon=ft.Icons.CANCEL,
                    on_click=fechar_confirmacao,
                    bgcolor="#EF4444",
                    color="#FFFFFF",
                ),
                ft.ElevatedButton(
                    "Confirmar Importação",
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=confirmar_e_importar,
                    bgcolor="#22C55E",
                    color="#FFFFFF",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.open(dialogo_confirmacao)
    
    def executar_importacao(df, novos, atualizacoes):
        """Executa a importação dos SKUs"""
        from db_client import get_connection
        from db_client import DB_TYPE
        
        status_container.controls.clear()
        status_container.controls.append(
            ft.Row([
                ft.ProgressRing(width=20, height=20),
                ft.Text("Importando SKUs...", color=get_text_color()),
            ], spacing=10)
        )
        page.update()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Placeholder depends on DB type
            ph = "%s" if DB_TYPE == "mysql" else "?"
            
            novos_count = 0
            atualizados_count = 0
            
            for _, row in df.iterrows():
                codigo = str(row.get('codigo_produto', ''))
                sku_seller = str(row.get('sku_seller', ''))
                nome = str(row.get('nome_esperado', ''))
                link = str(row.get('link', ''))
                
                if not codigo or not sku_seller:
                    continue
                
                # Verificar se já existe
                cursor.execute(f"SELECT id FROM produtos WHERE sku_seller = {ph}", (sku_seller,))
                existe = cursor.fetchone()
                
                if existe:
                    # Atualizar
                    cursor.execute(f"""
                        UPDATE produtos 
                        SET codigo_produto = {ph}, nome_esperado = {ph}, link = {ph}
                        WHERE sku_seller = {ph}
                    """, (codigo, nome, link, sku_seller))
                    atualizados_count += 1
                else:
                    # Inserir novo
                    cursor.execute(f"""
                        INSERT INTO produtos (codigo_produto, sku_seller, nome_esperado, link, status_final)
                        VALUES ({ph}, {ph}, {ph}, {ph}, 'PENDENTE')
                    """, (codigo, sku_seller, nome, link))
                    novos_count += 1
            
            conn.commit()
            conn.close()
            
            # Limpar arquivo temporário
            if excel_path[0] and os.path.exists(excel_path[0]):
                try:
                    os.remove(excel_path[0])
                except:
                    pass
            
            # Sucesso - Fechar primeiro diálogo e mostrar mensagem
            page.close(dialogo)
            
            # Mostrar notificação de sucesso
            page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#FFFFFF"),
                    ft.Text(f"✅ Importação Concluída! {novos_count} novos + {atualizados_count} atualizados", color="#FFFFFF"),
                ]),
                bgcolor="#22C55E",
                duration=5000,
            )
            page.snack_bar.open = True
            page.update()
            
            if on_complete:
                on_complete()
            
        except Exception as ex:
            status_container.controls.clear()
            status_container.controls.append(
                ft.Text(f"❌ Erro na importação: {ex}", color="#EF4444")
            )
            page.update()
    
    def iniciar_importacao(e):
        """Cria template e abre Excel"""
        status_container.controls.clear()
        status_container.controls.append(
            ft.Row([
                ft.ProgressRing(width=20, height=20),
                ft.Text("Criando arquivo modelo...", color=get_text_color()),
            ], spacing=10)
        )
        page.update()
        
        path = criar_template_excel()
        abrir_excel_e_aguardar(path)
    
    # Conteúdo do diálogo
    conteudo = ft.Column([
        ft.Text("📦 Adicionar/Atualizar SKUs", size=20, weight=ft.FontWeight.BOLD, color=get_text_color()),
        ft.Divider(),
        ft.Text("Como funciona:", weight=ft.FontWeight.BOLD, color=get_text_color()),
        ft.Column([
            ft.Row([ft.Icon(ft.Icons.LOOKS_ONE, color="#3B82F6"), ft.Text("Um arquivo Excel modelo será aberto", color=get_text_color())]),
            ft.Row([ft.Icon(ft.Icons.LOOKS_TWO, color="#3B82F6"), ft.Text("Preencha os SKUs que deseja adicionar", color=get_text_color())]),
            ft.Row([ft.Icon(ft.Icons.LOOKS_3, color="#3B82F6"), ft.Text("Feche o arquivo Excel", color=get_text_color())]),
            ft.Row([ft.Icon(ft.Icons.LOOKS_4, color="#3B82F6"), ft.Text("Confirme a importação", color=get_text_color())]),
        ], spacing=5),
        ft.Container(height=10),
        ft.Container(
            content=ft.Column([
                ft.Text("📋 Colunas do arquivo:", weight=ft.FontWeight.BOLD, size=12),
                ft.Text("• codigo_produto - Código do produto (ex: D23-2094-028-01)", size=11),
                ft.Text("• sku_seller - SKU do vendedor (ex: 0036-9-39-44)", size=11),
                ft.Text("• nome_esperado - Nome do produto", size=11),
                ft.Text("• link - URL do produto na Netshoes", size=11),
            ], spacing=3),
            bgcolor=get_surface(),
            padding=10,
            border_radius=8,
        ),
        ft.Container(height=10),
        ft.Text("⚠️ SKUs com o mesmo sku_seller serão ATUALIZADOS.", size=11, color="#EAB308", italic=True),
        ft.Container(height=15),
        status_container,
    ], spacing=10, width=500)
    
    # Diálogo
    dialogo = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.ADD_CIRCLE, color="#22C55E"),
            ft.Text("Importar SKUs"),
        ]),
        content=conteudo,
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_dialogo),
            ft.ElevatedButton(
                "Iniciar",
                icon=ft.Icons.PLAY_ARROW,
                on_click=iniciar_importacao,
                bgcolor="#22C55E",
                color="#FFFFFF",
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.open(dialogo)
