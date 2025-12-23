# importar_dados.py — Utilitario para popular o SQLite inicial
"""
Importa dados do Google Sheets ou CSV para o SQLite
Execute uma vez para migrar os dados existentes
"""
import pandas as pd
from db_client import get_connection, criar_tabelas

def importar_do_google_sheets():
    """Importa dados do Google Sheets para o SQLite (uma vez)"""
    print("[IMPORT] Conectando ao Google Sheets...")
    
    try:
        from google_sheet_client import ler_planilha as ler_gsheet
        df = ler_gsheet()
        
        if df is None or df.empty:
            print("[ERRO] Nenhum dado encontrado no Google Sheets.")
            return False
        
        print(f"[IMPORT] {len(df)} registros encontrados no Google Sheets")
        
        # Salvar no SQLite
        criar_tabelas()
        conn = get_connection()
        
        # Mapear colunas
        col_map = {
            "codigo_produto": "codigo_produto",
            "nome_esperado": "nome_esperado",
            "link": "link",
            "Site Disponivel": "site_disponivel",
            "Vendedor": "vendedor",
            "Preco": "preco",
            "Status Final": "status_final",
            "Data Verificacao": "data_verificacao"
        }
        
        df_save = df.copy()
        df_save = df_save.rename(columns=col_map)
        
        colunas_validas = ["codigo_produto", "nome_esperado", "link", "site_disponivel", 
                          "vendedor", "preco", "status_final", "data_verificacao"]
        colunas_presentes = [c for c in colunas_validas if c in df_save.columns]
        df_save = df_save[colunas_presentes]
        
        conn.execute("DELETE FROM produtos")
        df_save.to_sql("produtos", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()
        
        print(f"[OK] {len(df_save)} produtos importados para o SQLite!")
        return True
        
    except Exception as e:
        print(f"[ERRO] Falha ao importar: {e}")
        return False


def importar_do_csv(caminho_csv: str):
    """Importa dados de um CSV para o SQLite"""
    print(f"[IMPORT] Lendo CSV: {caminho_csv}")
    
    # Tentar detectar delimitador
    try:
        # Primeiro le uma linha para detectar
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            primeira_linha = f.readline()
    except:
        with open(caminho_csv, 'r', encoding='latin-1') as f:
            primeira_linha = f.readline()
    
    # Detectar delimitador
    if ';' in primeira_linha and ',' not in primeira_linha:
        sep = ';'
        print("[INFO] Detectado delimitador: ponto-e-virgula (;)")
    else:
        sep = ','
        print("[INFO] Detectado delimitador: virgula (,)")
    
    try:
        df = pd.read_csv(caminho_csv, encoding="utf-8", sep=sep)
    except:
        df = pd.read_csv(caminho_csv, encoding="latin-1", sep=sep)
    
    if df.empty:
        print("[ERRO] CSV vazio.")
        return False
    
    print(f"[IMPORT] {len(df)} registros encontrados no CSV")
    print(f"[IMPORT] Colunas: {list(df.columns)}")
    
    # Verificar colunas necessarias
    colunas_esperadas = ["codigo_produto", "link"]
    faltando = [c for c in colunas_esperadas if c not in df.columns]
    if faltando:
        print(f"[AVISO] Colunas faltando: {faltando}")
        print("[AVISO] O CSV precisa ter ao menos 'codigo_produto' e 'link'")
        return False

    
    criar_tabelas()
    conn = get_connection()
    
    # Mapear colunas se necessario (novo schema com 3 vendedores)
    col_map = {
        "codigo_produto": "codigo_produto",
        "sku_seller": "sku_seller",
        "nome_esperado": "nome_esperado", 
        "link": "link",
        "Site Disponivel": "site_disponivel",
        "Vendedor 1": "vendedor_1",
        "Preco 1": "preco_1",
        "Frete 1": "frete_1",
        "Vendedor 2": "vendedor_2",
        "Preco 2": "preco_2",
        "Frete 2": "frete_2",
        "Vendedor 3": "vendedor_3",
        "Preco 3": "preco_3",
        "Frete 3": "frete_3",
        "Status Final": "status_final",
        "Data Verificacao": "data_verificacao"
    }
    
    df_save = df.copy()
    df_save = df_save.rename(columns=col_map)
    
    colunas_validas = ["codigo_produto", "sku_seller", "nome_esperado", "link", "site_disponivel", 
                      "vendedor_1", "preco_1", "frete_1",
                      "vendedor_2", "preco_2", "frete_2",
                      "vendedor_3", "preco_3", "frete_3",
                      "status_final", "data_verificacao"]
    colunas_presentes = [c for c in colunas_validas if c in df_save.columns]
    df_save = df_save[colunas_presentes]
    
    conn.execute("DELETE FROM produtos")
    df_save.to_sql("produtos", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    
    print(f"[OK] {len(df_save)} produtos importados para o SQLite!")
    return True


def criar_exemplo_csv():
    """Cria um CSV de exemplo para voce preencher"""
    exemplo = pd.DataFrame({
        "codigo_produto": ["SKU001", "SKU002", "SKU003"],
        "nome_esperado": ["Produto 1", "Produto 2", "Produto 3"],
        "link": [
            "https://www.netshoes.com.br/produto/SKU001",
            "https://www.netshoes.com.br/produto/SKU002",
            "https://www.netshoes.com.br/produto/SKU003",
        ]
    })
    exemplo.to_csv("produtos_exemplo.csv", index=False, encoding="utf-8")
    print("[OK] Arquivo 'produtos_exemplo.csv' criado!")
    print("[INFO] Edite este arquivo com seus SKUs e links, depois execute:")
    print("       python importar_dados.py csv produtos_exemplo.csv")


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("  IMPORTADOR DE DADOS PARA SQLITE")
    print("=" * 50)
    print()
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python importar_dados.py gsheet    -> Importar do Google Sheets")
        print("  python importar_dados.py csv ARQUIVO.csv -> Importar de CSV")
        print("  python importar_dados.py exemplo   -> Criar CSV de exemplo")
        print()
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "gsheet":
        importar_do_google_sheets()
    elif cmd == "csv" and len(sys.argv) >= 3:
        importar_do_csv(sys.argv[2])
    elif cmd == "exemplo":
        criar_exemplo_csv()
    else:
        print("[ERRO] Comando invalido. Use: gsheet, csv, ou exemplo")
