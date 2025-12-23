# relatorio_historico_ia.py - Análise Histórica com IA (OTIMIZADO)
"""
Relatório de Oportunidades IA baseado em dados históricos
Analisa competição, tendências e recomendações de investimento
VERSÃO OTIMIZADA - Usa operações vetorizadas do pandas
"""
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from db_client import get_connection

# Suprimir aviso do pandas sobre conexão DBAPI2
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")


def carregar_dados_historicos(dias: int = 30):
    """Carrega dados históricos - OTIMIZADO com SQL mais eficiente"""
    conn = get_connection()
    
    try:
        # Calcular data limite
        data_limite = datetime.now() - timedelta(days=dias)
        
        # Query otimizada - pegar apenas registros mais recentes por SKU
        # Isso reduz drasticamente a quantidade de dados processados
        query = """
            SELECT 
                h.codigo_produto,
                h.nome_esperado,
                h.vendedor_1,
                h.preco_1,
                h.vendedor_2,
                h.preco_2,
                h.vendedor_3,
                h.preco_3,
                h.status_final,
                h.data_coleta,
                p.sku_seller
            FROM historico h
            LEFT JOIN produtos p ON h.codigo_produto = p.codigo_produto
            WHERE h.id IN (
                SELECT MAX(id) FROM historico GROUP BY codigo_produto
            )
            LIMIT 25000
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return pd.DataFrame()
        
        return df
    
    except Exception as e:
        print(f"[ERRO] Ao carregar histórico: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def analisar_concorrencia(df: pd.DataFrame):
    """Analisa nível de concorrência por SKU - VERSÃO VETORIZADA"""
    if df.empty:
        return pd.DataFrame()
    
    # Criar cópia para não modificar original
    df = df.copy()
    
    # Converter preços para numérico de forma vetorizada
    for col in ['preco_1', 'preco_2', 'preco_3']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).replace(',', '.') if pd.notna(x) else None)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calcular métricas de preço de forma vetorizada
    preco_cols = ['preco_1', 'preco_2', 'preco_3']
    existing_cols = [c for c in preco_cols if c in df.columns]
    
    if existing_cols:
        df['Preco Medio'] = df[existing_cols].mean(axis=1).round(2)
        df['Preco Min'] = df[existing_cols].min(axis=1).round(2)
        df['Preco Max'] = df[existing_cols].max(axis=1).round(2)
    else:
        df['Preco Medio'] = 0
        df['Preco Min'] = 0
        df['Preco Max'] = 0
    
    # Contar vendedores (forma vetorizada)
    def contar_vendedores(row):
        vendedores = set()
        for col in ['vendedor_1', 'vendedor_2', 'vendedor_3']:
            v = str(row.get(col, '-')) if pd.notna(row.get(col)) else '-'
            if v != '-' and v != '' and v != 'nan':
                vendedores.add(v)
        return len(vendedores)
    
    def listar_vendedores(row):
        vendedores = []
        for col in ['vendedor_1', 'vendedor_2', 'vendedor_3']:
            v = str(row.get(col, '-')) if pd.notna(row.get(col)) else '-'
            if v != '-' and v != '' and v != 'nan' and v not in vendedores:
                vendedores.append(v)
        return ', '.join(vendedores[:3])
    
    df['Num Vendedores'] = df.apply(contar_vendedores, axis=1)
    df['Vendedores'] = df.apply(listar_vendedores, axis=1)
    
    # Classificar concorrência (forma vetorizada)
    conditions = [
        (df['Num Vendedores'] == 0),
        (df['Num Vendedores'] == 1),
        (df['Num Vendedores'] == 2),
        (df['Num Vendedores'] >= 3)
    ]
    choices = ['Sem Oferta', 'Exclusivo', 'Baixa', 'Alta']
    df['Nivel Concorrencia'] = np.select(conditions, choices, default='Baixa')
    
    # Verificar se Color está em 1º (forma vetorizada)
    df['Color em 1o'] = df['vendedor_1'].fillna('').str.lower().str.contains('color', na=False)
    df['Color em 1o'] = df['Color em 1o'].map({True: 'Sim', False: 'Não'})
    
    # Volatilidade simplificada (diferença entre max e min)
    df['Volatilidade'] = (df['Preco Max'] - df['Preco Min']).round(2).fillna(0)
    
    # Montar resultado final
    result = pd.DataFrame({
        'SKU': df['codigo_produto'],
        'SKU Seller': df['sku_seller'].fillna('-'),
        'Nome': df['nome_esperado'].fillna('-'),
        'Num Vendedores': df['Num Vendedores'],
        'Nivel Concorrencia': df['Nivel Concorrencia'],
        'Preco Medio': df['Preco Medio'].fillna(0),
        'Preco Min': df['Preco Min'].fillna(0),
        'Preco Max': df['Preco Max'].fillna(0),
        'Volatilidade': df['Volatilidade'],
        'Color em 1o': df['Color em 1o'],
        'Status': df['status_final'].fillna('-'),
        'Vendedores': df['Vendedores'],
    })
    
    return result


def gerar_recomendacoes(df_analise: pd.DataFrame):
    """Gera recomendações de investimento baseadas na análise"""
    if df_analise.empty:
        return {
            'investir_mais': pd.DataFrame(),
            'monitorar': pd.DataFrame(),
            'otimizar_preco': pd.DataFrame(),
            'resumo': {
                'Total SKUs': 0,
                'Baixa Concorrencia': 0,
                'Alta Concorrencia': 0,
                'Color em 1o': 0,
                'Preco Medio Geral': 0,
                'Taxa BuyBox': 0,
            }
        }
    
    # SKUs para investir mais (baixa concorrência + Color em 1º)
    investir = df_analise[
        (df_analise['Nivel Concorrencia'].isin(['Exclusivo', 'Baixa'])) &
        (df_analise['Color em 1o'] == 'Sim') &
        (df_analise['Status'] == 'OK')
    ].sort_values('Preco Medio', ascending=False)
    
    # SKUs para monitorar (alta concorrência)
    monitorar = df_analise[
        df_analise['Nivel Concorrencia'] == 'Alta'
    ].sort_values('Num Vendedores', ascending=False)
    
    # SKUs para otimizar preço (alta volatilidade)
    median_vol = df_analise['Volatilidade'].median()
    otimizar = df_analise[
        df_analise['Volatilidade'] > median_vol
    ].sort_values('Volatilidade', ascending=False)
    
    # Resumo
    total_skus = len(df_analise)
    baixa_conc = len(df_analise[df_analise['Nivel Concorrencia'].isin(['Exclusivo', 'Baixa'])])
    alta_conc = len(df_analise[df_analise['Nivel Concorrencia'] == 'Alta'])
    color_lider = len(df_analise[df_analise['Color em 1o'] == 'Sim'])
    preco_medio_geral = df_analise['Preco Medio'].mean() if total_skus > 0 else 0
    
    resumo = {
        'Total SKUs': total_skus,
        'Baixa Concorrencia': baixa_conc,
        'Alta Concorrencia': alta_conc,
        'Color em 1o': color_lider,
        'Preco Medio Geral': round(preco_medio_geral, 2),
        'Taxa BuyBox': round((color_lider / total_skus * 100) if total_skus > 0 else 0, 1),
    }
    
    return {
        'investir_mais': investir,
        'monitorar': monitorar,
        'otimizar_preco': otimizar,
        'resumo': resumo
    }


def gerar_relatorio_completo(dias: int = 30):
    """Gera relatório completo de oportunidades IA - OTIMIZADO"""
    # Carregar dados (já otimizado)
    df = carregar_dados_historicos(dias)
    
    if df.empty:
        return None
    
    # Analisar concorrência (versão vetorizada)
    df_analise = analisar_concorrencia(df)
    
    # Gerar recomendações
    recomendacoes = gerar_recomendacoes(df_analise)
    
    return {
        'analise_completa': df_analise,
        'recomendacoes': recomendacoes,
        'periodo_dias': dias,
        'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
