# utils.py — Utilitários (versão Flet - sem TkAgg)
"""
Funções utilitárias para a aplicação
"""
from typing import Any
import os
import sys


def resource_path(relative_path: str) -> str:
    """Retorna o caminho absoluto para um recurso (funciona como script e exe)"""
    if getattr(sys, 'frozen', False):
        # Executando como exe (PyInstaller/Flet pack)
        base_path = sys._MEIPASS
    else:
        # Executando como script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def carregar_tema_padrao():
    """Carrega o tema padrão das preferências"""
    try:
        from configuracoes import carregar_tema as _carregar
        return _carregar()
    except Exception:
        return "dark"


def carregar_tema():
    """Wrapper para carregar tema"""
    return carregar_tema_padrao()
