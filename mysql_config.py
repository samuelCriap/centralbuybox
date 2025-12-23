# mysql_config.py — Configuração do MySQL
"""
Gerencia configuração específica do MySQL
"""
import json
import os
from pathlib import Path


def get_config_path():
    """Retorna caminho do arquivo de configuração"""
    # Primeiro tenta no diretório do script
    local_path = Path(__file__).parent / "config" / "server_config.json"
    if local_path.exists():
        return local_path
    
    # Depois tenta no AppData (para exe)
    appdata_path = Path(os.environ.get('APPDATA', '')) / "CentralNetshoes" / "config" / "server_config.json"
    if appdata_path.exists():
        return appdata_path
    
    # Se nenhum existe, retorna o local
    return local_path


def load_mysql_config():
    """Carrega configurações do MySQL"""
    config_path = get_config_path()
    
    default_mysql = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "netshoes_nivia",
    }
    
    if not config_path.exists():
        return default_mysql
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            mysql_config = config.get("mysql", {})
            
            # Mesclar com padrões
            for key, value in default_mysql.items():
                if key not in mysql_config:
                    mysql_config[key] = value
            
            return mysql_config
    except Exception as e:
        print(f"[ERRO] Ao carregar config MySQL: {e}")
        return default_mysql


def save_mysql_config(mysql_config):
    """Salva configurações do MySQL"""
    config_path = get_config_path()
    
    # Garantir que o diretório existe
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Carregar config existente ou criar nova
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                "mode": "local",
                "network_path": "",
                "network_ip": "",
                "share_name": "Comercial",
                "db_type": "mysql",
            }
        
        # Atualizar seção MySQL
        config["mysql"] = mysql_config
        config["db_type"] = "mysql"
        
        from datetime import datetime
        config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"[ERRO] Ao salvar config MySQL: {e}")
        return False


def test_mysql_connection(host=None, port=None, user=None, password=None, database=None):
    """Testa conexão com o MySQL"""
    try:
        import mysql.connector
        from mysql.connector import Error
    except ImportError:
        return False, "mysql-connector-python não está instalado. Execute: pip install mysql-connector-python"
    
    # Usar valores fornecidos ou carregar da config
    config = load_mysql_config()
    
    test_config = {
        "host": host or config["host"],
        "port": port or config["port"],
        "user": user or config["user"],
        "password": password if password is not None else config["password"],
    }
    
    try:
        # Primeiro testa conexão sem banco
        conn = mysql.connector.connect(**test_config)
        
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return True, f"Conexão bem-sucedida! MySQL versão: {version}"
        else:
            return False, "Não foi possível conectar ao MySQL"
            
    except Error as e:
        return False, f"Erro de conexão: {str(e)}"
    except Exception as e:
        return False, f"Erro: {str(e)}"


def enable_mysql():
    """Ativa o modo MySQL no config"""
    config_path = get_config_path()
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        config["db_type"] = "mysql"
        
        from datetime import datetime
        config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("[OK] MySQL ativado como banco de dados padrão")
        return True
    except Exception as e:
        print(f"[ERRO] Ao ativar MySQL: {e}")
        return False


def disable_mysql():
    """Desativa o modo MySQL (volta para SQLite)"""
    config_path = get_config_path()
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        config["db_type"] = "sqlite"
        
        from datetime import datetime
        config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("[OK] SQLite ativado como banco de dados padrão")
        return True
    except Exception as e:
        print(f"[ERRO] Ao desativar MySQL: {e}")
        return False


if __name__ == "__main__":
    print("=== Teste de Configuração MySQL ===")
    print()
    
    config = load_mysql_config()
    print(f"Configuração atual:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  User: {config['user']}")
    print(f"  Database: {config['database']}")
    print()
    
    success, message = test_mysql_connection()
    print(f"Teste de conexão: {message}")
