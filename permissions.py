"""
Middlewares de permissão e validação de acesso.
Garantem que cada usuário só acesse seus próprios recursos.
"""

from functools import wraps
from flask import session, redirect, url_for, abort, request, flash
from config import Config
from okf_manager import listar_usuarios, get_usuario_por_id

DATA_DIR = Config.DATA_DIR


def login_required(f):
    """
    Decorator: exige que o usuário esteja logado.
    Redireciona para /login se não houver sessão ativa.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_global_required(f):
    """
    Decorator: exige que o usuário seja o Administrador Geral (ID 0).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('user_id') != 0:
            abort(403, description="Acesso restrito ao Administrador Geral.")
        return f(*args, **kwargs)
    return decorated_function


def admin_corporativo_required(f):
    """
    Decorator: exige que o usuário seja Administrador Corporativo.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = get_usuario_por_id(DATA_DIR, session.get('user_id'))
        if not user or user.get('perfil') not in ('corporativo', 'admin'):
            abort(403, description="Acesso restrito a administradores corporativos.")
        return f(*args, **kwargs)
    return decorated_function


def user_owner_or_admin(f):
    """
    Decorator: valida que o usuário da rota (parâmetro user_id na URL)
    é o próprio usuário logado, ou é Admin Geral (ID 0).
    Previne que Usuário A acesse /kanban_users/B/.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        target_user_id = kwargs.get('user_id')
        if target_user_id is not None:
            target_user_id = int(target_user_id)
            current_user_id = session.get('user_id')

            # Admin Geral pode acessar qualquer usuário
            if current_user_id == 0:
                return f(*args, **kwargs)

            # Admin Corporativo pode acessar usuários da sua corporação
            if current_user_id != target_user_id:
                current_user = get_usuario_por_id(DATA_DIR, current_user_id)
                target_user = get_usuario_por_id(DATA_DIR, target_user_id)

                if (current_user and target_user and
                    current_user.get('perfil') == 'corporativo' and
                    current_user.get('id_corporacao') and
                    current_user.get('id_corporacao') == target_user.get('id_corporacao')):
                    return f(*args, **kwargs)

                abort(403, description="Você não tem permissão para acessar este recurso.")

        return f(*args, **kwargs)
    return decorated_function


def board_owner_required(f):
    """
    Decorator: valida que o quadro pertence ao usuário logado.
    Obtém o user_id do parâmetro na URL.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        current_user_id = session.get('user_id')
        board_user_id = kwargs.get('user_id')

        # Se não há user_id na URL, usa a rota padrão do usuário logado
        if board_user_id is None:
            kwargs['user_id'] = current_user_id
        else:
            board_user_id = int(board_user_id)
            if current_user_id != 0 and current_user_id != board_user_id:
                # Verificar se é admin corporativo com acesso ao usuário
                current_user = get_usuario_por_id(DATA_DIR, current_user_id)
                target_user = get_usuario_por_id(DATA_DIR, board_user_id)
                if (current_user and target_user and
                    current_user.get('perfil') == 'corporativo' and
                    current_user.get('id_corporacao') and
                    current_user.get('id_corporacao') == target_user.get('id_corporacao')):
                    pass  # permitido
                else:
                    abort(403, description="Este quadro não pertence ao seu domínio.")

        return f(*args, **kwargs)
    return decorated_function


def verificar_perfil(user_id: int) -> str:
    """
    Retorna o perfil do usuário: 'admin', 'corporativo' ou 'comum'.
    """
    if user_id == 0:
        return 'admin'

    user = get_usuario_por_id(DATA_DIR, user_id)
    if user:
        return user.get('perfil', 'comum')
    return 'comum'
