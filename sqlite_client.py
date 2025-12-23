# sqlite_client.py — Cliente SQLite para armazenamento local/rede
"""
Substitui google_sheet_client.py com armazenamento SQLite local ou em rede
Suporta modo WAL para melhor concorrência em rede
"""
import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

try:
    from network_config import get_database_path
    USE_NETWORK_CONFIG = True
except ImportError:
    USE_NETWORK_CONFIG = False
    DB_PATH = os.path.join("data", "netshoes.db")


def _get_db_path():
    """Retorna o caminho do banco de dados (local ou rede)"""
    if USE_NETWORK_CONFIG:
        return str(get_database_path())
    return DB_PATH


def _garantir_pasta():
    """Garante que a pasta do banco existe"""
    db_path = _get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)


def get_connection():
    """Retorna conexão com o banco SQLite"""
    _garantir_pasta()
    db_path = _get_db_path()
    
    conn = sqlite3.connect(db_path, timeout=30.0)  # Timeout maior para rede
    conn.row_factory = sqlite3.Row
    
    # Habilitar modo WAL para melhor concorrência
    # Permite múltiplos leitores simultâneos
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")  # Melhor performance
        conn.execute("PRAGMA busy_timeout=30000")  # 30 segundos de timeout
    except Exception as e:
        print(f"[AVISO] Não foi possível habilitar WAL: {e}")
    
    return conn


def criar_tabelas():
    """Cria as tabelas se não existirem - só cria se o banco já existir ou precisar ser criado"""
    db_path = _get_db_path()
    
    # Se o banco já existe, verificar se já tem as tabelas principais
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            # Verificar se a tabela produtos já existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produtos'")
            if cursor.fetchone():
                # Tabela já existe, não precisa criar novamente
                conn.close()
                return
            conn.close()
        except Exception:
            pass
    
    # Se chegou aqui, precisa criar as tabelas
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela produtos (dados atuais - equivale a Pagina1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_produto TEXT,
            sku_seller TEXT,
            nome_esperado TEXT,
            link TEXT,
            site_disponivel TEXT,
            vendedor_1 TEXT,
            preco_1 TEXT,
            frete_1 TEXT,
            vendedor_2 TEXT,
            preco_2 TEXT,
            frete_2 TEXT,
            vendedor_3 TEXT,
            preco_3 TEXT,
            frete_3 TEXT,
            status_final TEXT,
            data_verificacao TEXT
        )
    """)
    
    # Tabela historico (equivale a Pagina2)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_produto TEXT,
            nome_esperado TEXT,
            link TEXT,
            site_disponivel TEXT,
            vendedor_1 TEXT,
            preco_1 TEXT,
            frete_1 TEXT,
            vendedor_2 TEXT,
            preco_2 TEXT,
            frete_2 TEXT,
            vendedor_3 TEXT,
            preco_3 TEXT,
            frete_3 TEXT,
            status_final TEXT,
            data_verificacao TEXT,
            data_coleta TEXT
        )
    """)
    
    # Tabela usuários (para login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT,
            status TEXT DEFAULT 'pendente',
            role TEXT DEFAULT 'user',
            email TEXT
        )
    """)
    
    # Migracao simples para adicionar coluna role se nao existir
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN role TEXT DEFAULT 'user'")
    except sqlite3.OperationalError:
        pass # Coluna ja existe
    
    conn.commit()
    conn.close()
    print("[OK] Tabelas SQLite criadas/verificadas.")


def criar_usuario_padrao():
    """Cria um usuário admin padrão se não existir nenhum"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Criar primeiro usuário como MASTER (super admin)
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, status, role, email)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin", "aprovado", "master", "admin@local.com"))
        conn.commit()
        print("[OK] Usuario admin padrao criado como MASTER (admin/admin)")
    # Removido: não resetar mais o role do admin a cada inicialização
    
    conn.close()


# ============================================================
# FUNÇÕES DE PRODUTOS (substitui ler_planilha/salvar_planilha)
# ============================================================

def ler_planilha() -> pd.DataFrame:
    """Lê a tabela produtos e retorna como DataFrame"""
    criar_tabelas()
    conn = get_connection()
    
    try:
        df = pd.read_sql_query("SELECT * FROM produtos", conn)
        # Renomear colunas para manter compatibilidade
        col_map = {
            "codigo_produto": "codigo_produto",
            "sku_seller": "sku_seller",
            "nome_esperado": "nome_esperado",
            "link": "link",
            "site_disponivel": "Site Disponivel",
            "vendedor_1": "Vendedor 1",
            "preco_1": "Preco 1",
            "frete_1": "Frete 1",
            "vendedor_2": "Vendedor 2",
            "preco_2": "Preco 2",
            "frete_2": "Frete 2",
            "vendedor_3": "Vendedor 3",
            "preco_3": "Preco 3",
            "frete_3": "Frete 3",
            "status_final": "Status Final",
            "data_verificacao": "Data Verificacao"
        }
        df = df.rename(columns=col_map)
        return df
    except Exception as e:
        print(f"[SQLITE] Erro ao ler produtos: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def salvar_planilha(df: pd.DataFrame) -> None:
    """Salva DataFrame na tabela produtos (substitui dados existentes)"""
    criar_tabelas()
    
    if df is None or df.empty:
        print("[AVISO] DataFrame vazio, nada para salvar.")
        return
    
    # Mapear nomes das colunas para o banco
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
    
    # Manter apenas colunas conhecidas
    colunas_validas = ["codigo_produto", "sku_seller", "nome_esperado", "link", "site_disponivel", 
                       "vendedor_1", "preco_1", "frete_1",
                       "vendedor_2", "preco_2", "frete_2",
                       "vendedor_3", "preco_3", "frete_3",
                       "status_final", "data_verificacao"]
    colunas_presentes = [c for c in colunas_validas if c in df_save.columns]
    df_save = df_save[colunas_presentes]
    
    conn = get_connection()
    try:
        # Limpar tabela e inserir novos dados
        conn.execute("DELETE FROM produtos")
        df_save.to_sql("produtos", conn, if_exists="append", index=False)
        conn.commit()
        print(f"[OK] Produtos salvos ({len(df_save)} linhas)")
    except Exception as e:
        print(f"[SQLITE] Erro ao salvar produtos: {e}")
    finally:
        conn.close()


# ============================================================
# FUNÇÕES DE HISTÓRICO (substitui ler_aba("Pagina2"))
# ============================================================

def ler_aba(aba: str) -> pd.DataFrame:
    """Lê dados de uma 'aba' - para compatibilidade com código existente"""
    criar_tabelas()
    
    if aba.lower() in ["pagina2", "página2", "historico"]:
        return ler_historico()
    elif aba.lower() in ["pagina1", "página1", "produtos"]:
        return ler_planilha()
    elif aba.lower() == "usuarios":
        return ler_usuarios()
    else:
        print(f"[SQLITE] Aba desconhecida: {aba}")
        return pd.DataFrame()


def ler_historico() -> pd.DataFrame:
    """Lê a tabela histórico e retorna como DataFrame"""
    conn = get_connection()
    
    try:
        df = pd.read_sql_query("SELECT * FROM historico", conn)
        # Renomear para compatibilidade
        col_map = {
            "codigo_produto": "SKU Color",
            "vendedor": "Vendedor",
            "preco": "Preço",
            "data_verificacao": "Data Verificação",
            "data_coleta": "Data Coleta"
        }
        df = df.rename(columns=col_map)
        return df
    except Exception as e:
        print(f"[SQLITE] Erro ao ler histórico: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def atualizar_historico(df_atual: pd.DataFrame, dias_limite: int = 180):
    """
    Adiciona registros ao histórico.
    Registros com mais de 6 meses (180 dias) são movidos para backup.
    """
    criar_tabelas()
    
    if df_atual is None or df_atual.empty:
        print("[AVISO] Nenhum dado para salvar no historico.")
        return
    
    conn = get_connection()
    
    try:
        # Criar tabela de backup se não existir
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_produto TEXT,
                nome_esperado TEXT,
                link TEXT,
                site_disponivel TEXT,
                vendedor_1 TEXT,
                preco_1 TEXT,
                frete_1 TEXT,
                vendedor_2 TEXT,
                preco_2 TEXT,
                frete_2 TEXT,
                vendedor_3 TEXT,
                preco_3 TEXT,
                frete_3 TEXT,
                status_final TEXT,
                data_verificacao TEXT,
                data_coleta TEXT,
                data_backup TEXT
            )
        """)
        conn.commit()
        
        # Preparar dados para insercao
        df_envio = df_atual.copy()
        df_envio["Data Coleta"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Mapear colunas
        col_map = {
            "codigo_produto": "codigo_produto",
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
            "Data Verificacao": "data_verificacao",
            "Data Coleta": "data_coleta"
        }
        df_envio = df_envio.rename(columns=col_map)
        
        # Manter apenas colunas validas
        colunas_validas = ["codigo_produto", "nome_esperado", "link", "site_disponivel", 
                          "vendedor_1", "preco_1", "frete_1",
                          "vendedor_2", "preco_2", "frete_2",
                          "vendedor_3", "preco_3", "frete_3",
                          "status_final", "data_verificacao", "data_coleta"]
        colunas_presentes = [c for c in colunas_validas if c in df_envio.columns]
        df_envio = df_envio[colunas_presentes]
        
        # Inserir no histórico
        df_envio.to_sql("historico", conn, if_exists="append", index=False)
        print(f"[OK] Historico atualizado com {len(df_envio)} linhas")
        
        # BACKUP E LIMPEZA de registros com mais de 6 meses
        limite = datetime.now() - timedelta(days=dias_limite)
        
        cursor.execute("SELECT * FROM historico")
        rows = cursor.fetchall()
        
        ids_para_backup = []
        registros_backup = []
        data_backup = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        for row in rows:
            try:
                data_coleta = row["data_coleta"] if "data_coleta" in row.keys() else None
                if data_coleta:
                    data = datetime.strptime(data_coleta, "%d/%m/%Y %H:%M:%S")
                    if data < limite:
                        ids_para_backup.append(row["id"])
                        registros_backup.append(dict(row))
            except:
                pass
        
        if registros_backup:
            # Mover para tabela de backup
            for reg in registros_backup:
                reg["data_backup"] = data_backup
                reg.pop("id", None)  # Remover ID para gerar novo
            
            df_backup = pd.DataFrame(registros_backup)
            df_backup.to_sql("historico_backup", conn, if_exists="append", index=False)
            
            # Remover do histórico principal
            placeholders = ",".join(["?" for _ in ids_para_backup])
            cursor.execute(f"DELETE FROM historico WHERE id IN ({placeholders})", ids_para_backup)
            conn.commit()
            print(f"[BACKUP] {len(registros_backup)} registros movidos para backup (> 6 meses)")
        
    except Exception as e:
        print(f"[SQLITE] Erro ao atualizar histórico: {e}")
    finally:
        conn.close()


# ============================================================
# FUNÇÕES DE USUÁRIOS (substitui google sheets para login)
# ============================================================

def ler_usuarios() -> pd.DataFrame:
    """Lê a tabela usuários"""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM usuarios", conn)
        return df
    except Exception as e:
        print(f"[SQLITE] Erro ao ler usuários: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def verificar_usuario(usuario: str, senha: str):
    """Verifica credenciais do usuário"""
    criar_tabelas()
    criar_usuario_padrao()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
        row = cursor.fetchone()
        
        if not row:
            return False, "Usuário inexistente. Crie uma nova conta.", None
        
        if row["senha"] != senha:
            return False, "Usuário ou senha incorretos.", None
        
        if row["status"] != "aprovado":
            return False, "Cadastro pendente de aprovação.", None
        
        return True, "Login aprovado!", {"username": usuario, "role": row["role"]}
        
    except Exception as e:
        return False, f"Erro: {e}", None
    finally:
        conn.close()


def adicionar_usuario(usuario: str, senha: str, email: str):
    """Adiciona um novo usuário"""
    criar_tabelas()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, status, email)
            VALUES (?, ?, ?, ?)
        """, (usuario, senha, "pendente", email))
        conn.commit()
        return True, "Cadastro enviado! Aguarde aprovação."
    except sqlite3.IntegrityError:
        return False, "Usuário já existe."
    except Exception as e:
        return False, f"Erro: {e}"
    finally:
        conn.close()


def listar_usuarios():
    """Retorna lista de todos os usuários"""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT id, usuario, email, status, role FROM usuarios", conn)
        return df
    except Exception as e:
        print(f"Erro listar usuarios: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def atualizar_usuario(user_id, status=None, role=None):
    """Atualiza status ou cargo do usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if status:
            cursor.execute("UPDATE usuarios SET status = ? WHERE id = ?", (status, user_id))
        if role:
            cursor.execute("UPDATE usuarios SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro atualizar usuario: {e}")
        return False
    finally:
        conn.close()


def excluir_usuario(user_id):
    """Remove um usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro excluir usuario: {e}")
        return False
    finally:
        conn.close()


def salvar_aba(df: pd.DataFrame, aba: str) -> None:
    """Salva dados em uma 'aba' - para compatibilidade"""
    if aba.lower() == "usuarios":
        # Substituir tabela usuários
        conn = get_connection()
        try:
            conn.execute("DELETE FROM usuarios")
            df.to_sql("usuarios", conn, if_exists="append", index=False)
            conn.commit()
        except Exception as e:
            print(f"[SQLITE] Erro ao salvar usuários: {e}")
        finally:
            conn.close()
    else:
        print(f"[SQLITE] Salvar aba '{aba}' não implementado")


# NOTA: A inicialização é feita sob demanda (lazy) nas funções
# que precisam do banco, não mais na importação do módulo.
# Isso garante que a configuração de rede do login seja respeitada.
