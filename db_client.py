# db_client.py — Abstração para escolha do banco de dados
"""
Este módulo escolhe automaticamente entre SQLite e MySQL
baseado na configuração do servidor.

Permite alternar entre bancos sem modificar os arquivos que importam as funções.
"""
import os
import sys
import json
from pathlib import Path

def _get_db_type():
    """Determina qual tipo de banco usar baseado na configuração"""
    config_paths = []
    
    # Se executando como EXE, verificar ao lado do executável
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
                    return config.get("db_type", "sqlite")
            except Exception:
                pass
    
    return "mysql"  # Padrão agora é MySQL


# Determinar tipo de banco e importar módulo correto
_db_type = _get_db_type()

if _db_type == "mysql":
    print("[DB] Usando MySQL como banco de dados")
    from mysql_client import (
        get_connection,
        criar_tabelas,
        criar_usuario_padrao,
        ler_planilha,
        salvar_planilha,
        ler_aba,
        ler_historico,
        atualizar_historico,
        ler_usuarios,
        verificar_usuario,
        adicionar_usuario,
        listar_usuarios,
        atualizar_usuario,
        excluir_usuario,
        salvar_aba,
    )
else:
    print("[DB] Usando SQLite como banco de dados")
    from sqlite_client import (
        get_connection,
        criar_tabelas,
        criar_usuario_padrao,
        ler_planilha,
        salvar_planilha,
        ler_aba,
        ler_historico,
        atualizar_historico,
        ler_usuarios,
        verificar_usuario,
        adicionar_usuario,
        listar_usuarios,
        atualizar_usuario,
        excluir_usuario,
        salvar_aba,
    )

# Exportar também o tipo de banco para verificações
DB_TYPE = _db_type
