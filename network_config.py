# network_config.py - Gerenciamento de Configuração de Rede
"""
Gerencia configuração de servidor local vs rede
Permite acesso compartilhado ao banco de dados SQLite
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def get_base_path():
    """Retorna o diretório base do aplicativo (funciona tanto como script quanto como exe)"""
    if getattr(sys, 'frozen', False):
        # Executando como exe (PyInstaller)
        return Path(sys._MEIPASS)
    else:
        # Executando como script
        return Path(__file__).parent


def get_config_dir():
    """Retorna o diretório de configuração persistente"""
    if getattr(sys, 'frozen', False):
        # Executando como exe - usar AppData para persistência
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(appdata) / "CentralNetshoes" / "config"
    else:
        # Executando como script - usar pasta local
        return Path(__file__).parent / "config"


BASE_PATH = get_base_path()
CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "server_config.json"

# Configuração padrão
DEFAULT_CONFIG = {
    "mode": "local",  # "local" ou "network"
    "network_path": "",  # Ex: "\\\\192.168.1.100\\NetShoes"
    "network_ip": "",  # Ex: "192.168.1.100"
    "share_name": "Comercial",  # Nome do compartilhamento
    "last_updated": "",
    "auto_connect": False,
}


def ensure_config_dir():
    """Garante que o diretório de configuração existe"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    """Carrega configuração do servidor"""
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        # Criar configuração padrão
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Garantir que todas as chaves existem
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
        
        return config
    except Exception as e:
        print(f"[ERRO] Ao carregar configuração: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Salva configuração do servidor"""
    ensure_config_dir()
    
    config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERRO] Ao salvar configuração: {e}")
        return False


def get_database_base_path():
    """Retorna o caminho base para o banco de dados baseado na configuração"""
    config = load_config()
    
    if config["mode"] == "network":
        # Modo rede - usar caminho UNC
        network_path = config.get("network_path", "")
        
        if not network_path:
            # Construir caminho a partir de IP e share_name
            ip = config.get("network_ip", "")
            share = config.get("share_name", "NetShoes")
            
            if ip:
                network_path = f"\\\\{ip}\\{share}"
        
        if network_path:
            return Path(network_path)
    
    # Modo local - usar diretório atual
    return Path.cwd()


def get_database_path():
    """Retorna o caminho completo para o arquivo de banco de dados"""
    config = load_config()
    
    # MODO REDE - usar caminho UNC
    if config.get("mode") == "network":
        network_path = config.get("network_path", "")
        
        if not network_path:
            # Construir caminho a partir de IP e share_name
            ip = config.get("network_ip", "")
            share = config.get("share_name", "Comercial")
            
            if ip:
                network_path = f"\\\\{ip}\\{share}"
        
        if network_path:
            db_path = Path(network_path) / "netshoes.db"
            return db_path
    
    # MODO LOCAL - usar caminho direto ou padrão
    direct_path = config.get("direct_path", "")
    if direct_path:
        db_path = Path(direct_path) / "netshoes.db"
        # Garantir que a pasta existe
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path
    
    # Fallback - usar diretório atual
    base_path = Path.cwd()
    return base_path / "data" / "netshoes.db"


def test_network_connection(ip_or_path):
    """Testa se consegue acessar o caminho de rede"""
    try:
        # Se for um IP, construir caminho UNC
        if ip_or_path and not ip_or_path.startswith("\\\\"):
            # Assumir que é um IP
            test_path = Path(f"\\\\{ip_or_path}\\NetShoes")
        else:
            test_path = Path(ip_or_path)
        
        # Tentar acessar o diretório
        if test_path.exists():
            # Tentar listar conteúdo
            list(test_path.iterdir())
            return True, "Conexão bem-sucedida!"
        else:
            return False, f"Caminho não encontrado: {test_path}"
    
    except PermissionError:
        return False, "Sem permissão de acesso. Verifique credenciais de rede."
    except OSError as e:
        return False, f"Erro de rede: {str(e)}"
    except Exception as e:
        return False, f"Erro ao testar conexão: {str(e)}"


def set_local_mode():
    """Configura para modo local"""
    config = load_config()
    config["mode"] = "local"
    return save_config(config)


def set_network_mode(ip_or_path, share_name="NetShoes"):
    """Configura para modo rede"""
    config = load_config()
    config["mode"] = "network"
    
    # Se for um caminho UNC completo
    if ip_or_path.startswith("\\\\"):
        config["network_path"] = ip_or_path
        # Extrair IP do caminho
        parts = ip_or_path.replace("\\\\", "").split("\\")
        if parts:
            config["network_ip"] = parts[0]
            if len(parts) > 1:
                config["share_name"] = parts[1]
    else:
        # Assumir que é um IP
        config["network_ip"] = ip_or_path
        config["share_name"] = share_name
        config["network_path"] = f"\\\\{ip_or_path}\\{share_name}"
    
    return save_config(config)


def get_current_mode():
    """Retorna o modo atual (local ou network)"""
    config = load_config()
    return config.get("mode", "local")


def get_network_info():
    """Retorna informações sobre a configuração de rede"""
    config = load_config()
    
    return {
        "mode": config.get("mode", "local"),
        "network_path": config.get("network_path", ""),
        "network_ip": config.get("network_ip", ""),
        "share_name": config.get("share_name", "NetShoes"),
        "database_path": str(get_database_path()),
    }
