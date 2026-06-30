"""
Configurações da aplicação Kanban.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kanban-app-secret-key-change-in-production')
    DATA_DIR = DATA_DIR
    SESSION_COOKIE_NAME = 'kanban_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_QUADROS_POR_USUARIO = 20
    MAX_CARTOES_POR_COLUNA = 50
    MAX_COLUNAS_POR_QUADRO = 10
