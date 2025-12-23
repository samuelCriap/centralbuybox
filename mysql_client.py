# mysql_client.py — Cliente MySQL para armazenamento
"""
Substitui sqlite_client.py com armazenamento MySQL Community
Compatível com a mesma API do sqlite_client.py
"""
import os
import warnings
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# Suprimir aviso do pandas sobre conexão DBAPI2 (funciona normalmente com mysql-connector)
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

try:
    import mysql.connector
    from mysql.connector import Error, pooling
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("[AVISO] mysql-connector-python não instalado. Execute: pip install mysql-connector-python")

# Pool de conexões global
_connection_pool = None

def _load_mysql_config():
    """Carrega configuração MySQL do arquivo de configuração"""
    import json
    import sys
    from pathlib import Path
    
    config_paths = []
    
    # Se executando como EXE, verificar ao lado do executável PRIMEIRO
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        config_paths.append(exe_dir / "config" / "server_config.json")
        # Também verificar dentro do bundle
        config_paths.append(Path(sys._MEIPASS) / "config" / "server_config.json")
    else:
        config_paths.append(Path(__file__).parent / "config" / "server_config.json")
    
    # AppData como fallback
    config_paths.append(Path(os.environ.get('APPDATA', '')) / "CentralNetshoes" / "config" / "server_config.json")
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    mysql_config = config.get("mysql", {})
                    return {
                        "host": mysql_config.get("host", "localhost"),
                        "port": mysql_config.get("port", 3306),
                        "user": mysql_config.get("user", "root"),
                        "password": mysql_config.get("password", ""),
                        "database": mysql_config.get("database", "netshoes_nivia"),
                    }
            except Exception as e:
                print(f"[AVISO] Erro ao carregar config MySQL: {e}")
    
    # Configuração padrão
    return {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "netshoes_nivia",
    }


def _ensure_database_exists():
    """Garante que o banco de dados existe"""
    if not MYSQL_AVAILABLE:
        raise ImportError("mysql-connector-python não está instalado")
    
    config = _load_mysql_config()
    database_name = config.pop("database")
    
    try:
        # Conectar sem especificar banco
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Criar banco se não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        
        cursor.close()
        conn.close()
        print(f"[OK] Banco de dados '{database_name}' verificado/criado")
        return True
    except Error as e:
        print(f"[ERRO] Falha ao criar banco de dados: {e}")
        return False


def _get_connection_pool():
    """Retorna o pool de conexões (cria se necessário)"""
    global _connection_pool
    
    if _connection_pool is None:
        if not MYSQL_AVAILABLE:
            raise ImportError("mysql-connector-python não está instalado")
        
        _ensure_database_exists()
        config = _load_mysql_config()
        
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="netshoes_pool",
                pool_size=5,
                pool_reset_session=True,
                **config
            )
            print("[OK] Pool de conexões MySQL criado")
        except Error as e:
            print(f"[ERRO] Falha ao criar pool de conexões: {e}")
            raise
    
    return _connection_pool


def get_connection():
    """Retorna conexão com o banco MySQL"""
    try:
        pool = _get_connection_pool()
        conn = pool.get_connection()
        return conn
    except Error as e:
        print(f"[MYSQL] Erro ao obter conexão: {e}")
        raise


def criar_tabelas():
    """Cria as tabelas se não existirem"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela produtos (dados atuais - equivale a Pagina1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo_produto VARCHAR(100),
            sku_seller VARCHAR(100),
            nome_esperado TEXT,
            link TEXT,
            site_disponivel VARCHAR(50),
            vendedor_1 VARCHAR(255),
            preco_1 VARCHAR(50),
            frete_1 VARCHAR(50),
            vendedor_2 VARCHAR(255),
            preco_2 VARCHAR(50),
            frete_2 VARCHAR(50),
            vendedor_3 VARCHAR(255),
            preco_3 VARCHAR(50),
            frete_3 VARCHAR(50),
            status_final VARCHAR(100),
            data_verificacao VARCHAR(50),
            INDEX idx_codigo_produto (codigo_produto)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Tabela historico (equivale a Pagina2)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo_produto VARCHAR(100),
            nome_esperado TEXT,
            link TEXT,
            site_disponivel VARCHAR(50),
            vendedor_1 VARCHAR(255),
            preco_1 VARCHAR(50),
            frete_1 VARCHAR(50),
            vendedor_2 VARCHAR(255),
            preco_2 VARCHAR(50),
            frete_2 VARCHAR(50),
            vendedor_3 VARCHAR(255),
            preco_3 VARCHAR(50),
            frete_3 VARCHAR(50),
            status_final VARCHAR(100),
            data_verificacao VARCHAR(50),
            data_coleta VARCHAR(50),
            INDEX idx_codigo_produto (codigo_produto),
            INDEX idx_data_coleta (data_coleta)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Tabela usuários (para login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario VARCHAR(100) UNIQUE,
            senha VARCHAR(255),
            status VARCHAR(50) DEFAULT 'pendente',
            role VARCHAR(50) DEFAULT 'user',
            email VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Tabela de backup do histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_backup (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo_produto VARCHAR(100),
            nome_esperado TEXT,
            link TEXT,
            site_disponivel VARCHAR(50),
            vendedor_1 VARCHAR(255),
            preco_1 VARCHAR(50),
            frete_1 VARCHAR(50),
            vendedor_2 VARCHAR(255),
            preco_2 VARCHAR(50),
            frete_2 VARCHAR(50),
            vendedor_3 VARCHAR(255),
            preco_3 VARCHAR(50),
            frete_3 VARCHAR(50),
            status_final VARCHAR(100),
            data_verificacao VARCHAR(50),
            data_coleta VARCHAR(50),
            data_backup VARCHAR(50),
            INDEX idx_data_coleta (data_coleta)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Tabelas MySQL criadas/verificadas.")


def criar_usuario_padrao():
    """Cria um usuário admin padrão se não existir nenhum"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM usuarios")
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    if count == 0:
        # Criar primeiro usuário como MASTER (super admin)
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, status, role, email)
            VALUES (%s, %s, %s, %s, %s)
        """, ("admin", "admin", "aprovado", "master", "admin@local.com"))
        conn.commit()
        print("[OK] Usuario admin padrao criado como MASTER (admin/admin)")
    
    cursor.close()
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
        print(f"[MYSQL] Erro ao ler produtos: {e}")
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
        cursor = conn.cursor()
        # Limpar tabela
        cursor.execute("DELETE FROM produtos")
        
        # Inserir dados usando INSERT com múltiplos valores
        if not df_save.empty:
            placeholders = ", ".join(["%s"] * len(colunas_presentes))
            columns = ", ".join(colunas_presentes)
            insert_query = f"INSERT INTO produtos ({columns}) VALUES ({placeholders})"
            
            # Converter DataFrame para lista de tuplas
            data = [tuple(row) for row in df_save.values]
            cursor.executemany(insert_query, data)
        
        conn.commit()
        cursor.close()
        print(f"[OK] Produtos salvos ({len(df_save)} linhas)")
    except Exception as e:
        print(f"[MYSQL] Erro ao salvar produtos: {e}")
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
        print(f"[MYSQL] Aba desconhecida: {aba}")
        return pd.DataFrame()


def ler_historico(limit: int = 0) -> pd.DataFrame:
    """
    Lê a tabela histórico e retorna como DataFrame.
    limit=0 retorna todos os dados (para relatórios)
    limit>0 retorna apenas os N mais recentes (para telas de análise rápida)
    """
    conn = get_connection()
    
    try:
        if limit > 0:
            # Query com limite para carregamento rápido
            df = pd.read_sql_query(f"""
                SELECT * FROM historico 
                ORDER BY id DESC 
                LIMIT {limit}
            """, conn)
        else:
            # Sem limite - para relatórios completos
            df = pd.read_sql_query("SELECT * FROM historico ORDER BY id DESC", conn)
        return df
    except Exception as e:
        print(f"[MYSQL] Erro ao ler histórico: {e}")
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
        cursor = conn.cursor(dictionary=True)
        
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
        if not df_envio.empty:
            placeholders = ", ".join(["%s"] * len(colunas_presentes))
            columns = ", ".join(colunas_presentes)
            insert_query = f"INSERT INTO historico ({columns}) VALUES ({placeholders})"
            data = [tuple(row) for row in df_envio.values]
            cursor.executemany(insert_query, data)
            conn.commit()
        
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
                data_coleta = row.get("data_coleta")
                if data_coleta:
                    data = datetime.strptime(data_coleta, "%d/%m/%Y %H:%M:%S")
                    if data < limite:
                        ids_para_backup.append(row["id"])
                        reg = dict(row)
                        reg.pop("id", None)
                        reg["data_backup"] = data_backup
                        registros_backup.append(reg)
            except:
                pass
        
        if registros_backup:
            # Mover para tabela de backup
            colunas_backup = list(registros_backup[0].keys())
            placeholders = ", ".join(["%s"] * len(colunas_backup))
            columns = ", ".join(colunas_backup)
            insert_query = f"INSERT INTO historico_backup ({columns}) VALUES ({placeholders})"
            data = [tuple(reg.values()) for reg in registros_backup]
            cursor.executemany(insert_query, data)
            
            # Remover do histórico principal
            placeholders = ",".join(["%s" for _ in ids_para_backup])
            cursor.execute(f"DELETE FROM historico WHERE id IN ({placeholders})", ids_para_backup)
            conn.commit()
            print(f"[BACKUP] {len(registros_backup)} registros movidos para backup (> 6 meses)")
        
        cursor.close()
        
    except Exception as e:
        print(f"[MYSQL] Erro ao atualizar histórico: {e}")
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
        print(f"[MYSQL] Erro ao ler usuários: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def verificar_usuario(usuario: str, senha: str):
    """Verifica credenciais do usuário"""
    criar_tabelas()
    criar_usuario_padrao()
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
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
        cursor.close()
        conn.close()


def adicionar_usuario(usuario: str, senha: str, email: str):
    """Adiciona um novo usuário"""
    criar_tabelas()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, status, email)
            VALUES (%s, %s, %s, %s)
        """, (usuario, senha, "pendente", email))
        conn.commit()
        return True, "Cadastro enviado! Aguarde aprovação."
    except mysql.connector.IntegrityError:
        return False, "Usuário já existe."
    except Exception as e:
        return False, f"Erro: {e}"
    finally:
        cursor.close()
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
            cursor.execute("UPDATE usuarios SET status = %s WHERE id = %s", (status, user_id))
        if role:
            cursor.execute("UPDATE usuarios SET role = %s WHERE id = %s", (role, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro atualizar usuario: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def excluir_usuario(user_id):
    """Remove um usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro excluir usuario: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def salvar_aba(df: pd.DataFrame, aba: str) -> None:
    """Salva dados em uma 'aba' - para compatibilidade"""
    if aba.lower() == "usuarios":
        # Substituir tabela usuários
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios")
            
            if not df.empty:
                columns = ", ".join(df.columns)
                placeholders = ", ".join(["%s"] * len(df.columns))
                insert_query = f"INSERT INTO usuarios ({columns}) VALUES ({placeholders})"
                data = [tuple(row) for row in df.values]
                cursor.executemany(insert_query, data)
            
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"[MYSQL] Erro ao salvar usuários: {e}")
        finally:
            conn.close()
    else:
        print(f"[MYSQL] Salvar aba '{aba}' não implementado")


# NOTA: A inicialização é feita sob demanda (lazy) nas funções
# que precisam do banco, não mais na importação do módulo.
