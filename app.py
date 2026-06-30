"""
Kanban App - Aplicativo Web de Kanban Gráfico Interativo
Backend: Flask com persistência em arquivos OKF

Rotas organizadas por perfil:
  - Admin Global (ID 0)  -> /admin/global/*
  - Admin Corporativo    -> /admin/corporativo/*
  - Usuário Comum        -> /dashboard/* e /admin/user
"""

import os
import json
from datetime import datetime, timedelta

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, abort)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from okf_manager import (
    listar_usuarios, get_usuario_por_id, get_usuario_por_email,
    criar_usuario, atualizar_usuario, remover_usuario,
    listar_quadros, criar_quadro, deletar_quadro, get_quadro_completo,
    adicionar_card, atualizar_card, remover_card, mover_card,
    adicionar_coluna, atualizar_coluna, remover_coluna,
    get_metricas_globais, get_espaco_disco_usuario
)
from permissions import (
    login_required, admin_global_required, admin_corporativo_required,
    board_owner_required, verificar_perfil
)

app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DATA_DIR = Config.DATA_DIR


# ─── Security Headers Middleware ──────────────────────────────────

@app.after_request
def add_security_headers(response):
    """Adiciona headers de segurança em todas as respostas."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "style-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Server'] = 'Kanban-App'
    return response


# ─── Rate Limiting (in-memory) ──────────────────────────────────

import time
from collections import defaultdict
from functools import wraps

_rate_limits = defaultdict(list)

def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """Rate limiter simples por IP. Padrão: 60 req/min."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = time.time()
            window_start = now - window_seconds
            _rate_limits[ip] = [t for t in _rate_limits[ip] if t > window_start]
            if len(_rate_limits[ip]) >= max_requests:
                abort(429, description="Muitas requisições. Aguarde e tente novamente.")
            _rate_limits[ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ─── Disk Quota & Limits ────────────────────────────────────────

DISK_QUOTA_BYTES = 50 * 1024 * 1024  # 50 MB por usuário
MAX_BOARDS_PER_USER = 20
MAX_CARDS_PER_BOARD = 200
MAX_COLUMNS_PER_BOARD = 10
MAX_CARD_TITLE_LENGTH = 200
MAX_CARD_DESC_LENGTH = 2000
MAX_BOARD_TITLE_LENGTH = 100
MAX_BOARD_DESC_LENGTH = 500
MAX_USER_NAME_LENGTH = 100
MAX_USER_EMAIL_LENGTH = 200
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128
MAX_COLUMN_TITLE_LENGTH = 100
MAX_CORP_ID_LENGTH = 50
MAX_USERS_PER_CORPORACAO = 100
MAX_NOME_ARQUIVO_LENGTH = 64
SESSION_TIMEOUT_MINUTES = 480  # 8 horas

# Helpers de validação
import re as _re

def validate_email(email: str) -> bool:
    """Valida formato básico de email."""
    if not email or len(email) > MAX_USER_EMAIL_LENGTH:
        return False
    return bool(_re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))

def validate_board_name_safe(name: str) -> bool:
    """Valida nome de quadro antes do sanitize."""
    if not name or len(name) > 128:
        return False
    if '..' in name or '/' in name or '\\' in name:
        return False
    return True

def validate_id_corporacao(corp_id: str) -> str:
    """Sanitiza id_corporacao - apenas alfanumérico básico."""
    if not corp_id:
        return ''
    return _re.sub(r'[^a-zA-Z0-9_-]', '', corp_id.strip())[:MAX_CORP_ID_LENGTH]

def check_disk_quota(data_dir: str, user_id: int) -> bool:
    from okf_manager import get_espaco_disco_usuario
    usage = get_espaco_disco_usuario(data_dir, user_id)
    return usage['bytes'] < DISK_QUOTA_BYTES

def enforce_limits(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id is not None and user_id != 0:
            if not check_disk_quota(DATA_DIR, user_id):
                flash('Limite de armazenamento atingido (50 MB). Exclua dados antigos.', 'error')
                return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapped


# ─── Plan Limits ────────────────────────────────────────────

PLANO_LIMITS = {
    'gratuito': {'max_quadros': 3, 'max_cartoes': 20},
    'comum': {'max_quadros': 20, 'max_cartoes': 200},
    'corporativo': {'max_quadros': 50, 'max_cartoes': 200},
}

def get_user_plan(user_id: int) -> str:
    """Retorna o plano do usuário: gratuito, comum ou corporativo."""
    user = get_usuario_por_id(DATA_DIR, user_id)
    if not user:
        return 'gratuito'
    return user.get('plano', 'gratuito')

def get_plan_limits(user_id: int) -> dict:
    """Retorna os limites do plano do usuário."""
    plan = get_user_plan(user_id)
    return PLANO_LIMITS.get(plan, PLANO_LIMITS['gratuito'])

def check_plan_limits(f):
    """Decorator: verifica limites do plano antes de criar quadros/cartões."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id is None:
            return f(*args, **kwargs)
        plan = get_user_plan(user_id)
        limits = get_plan_limits(user_id)

        if request.path.startswith('/dashboard/criar'):
            from okf_manager import listar_quadros
            quadros = listar_quadros(DATA_DIR, user_id)
            if len(quadros) >= limits['max_quadros']:
                flash(
                    f'Limite do plano {plan}: máximo de {limits["max_quadros"]} quadros. '
                    f'<a href="{url_for("planos")}" class="underline">Faça upgrade</a>',
                    'error'
                )
                return redirect(url_for('dashboard'))

        return f(*args, **kwargs)
    return wrapped


# ─── Input Sanitization ─────────────────────────────────────────

import re

def sanitize_board_name(name: str) -> str:
    """Remove chars perigosos de nomes de quadro (path traversal)."""
    if not name:
        return ''
    if name.startswith('__') or name in ('config', 'settings', '.env', '.git'):
        return ''
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name.strip())
    return sanitized[:64]


# ─── Contexto global do template ────────────────────────────────────

@app.context_processor
def inject_global_context():
    """Injeta dados do usuário logado em todos os templates."""
    user_id = session.get('user_id')
    user = None
    if user_id is not None:
        user = get_usuario_por_id(DATA_DIR, user_id)
    return {
        'current_user': user,
        'current_user_id': user_id,
        'perfil': verificar_perfil(user_id) if user_id is not None else None,
    }


# ═══════════════════════════════════════════════════════════════════
#  AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=20, window_seconds=60)
def login():
    """Página de login / autenticação."""
    if session.get('user_id') is not None:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()[:MAX_USER_EMAIL_LENGTH]
        senha = request.form.get('senha', '')[:MAX_PASSWORD_LENGTH]

        if not email or not senha:
            flash('Preencha email e senha.', 'error')
            return render_template('login.html')

        if len(senha) < MIN_PASSWORD_LENGTH:
            flash('Senha muito curta.', 'error')
            return render_template('login.html')

        if not validate_email(email):
            flash('Email inválido.', 'error')
            return render_template('login.html')

        user = get_usuario_por_email(DATA_DIR, email)
        if not user:
            flash('Usuário não encontrado.', 'error')
            return render_template('login.html')

        if user.get('ativo', 'true') == 'false':
            flash('Usuário suspenso. Contate o administrador.', 'error')
            return render_template('login.html')

        if check_password_hash(user.get('senha_hash', ''), senha):
            session.permanent = True
            app.permanent_session_lifetime = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            session['user_id'] = int(user['id'])
            session['user_name'] = user.get('nome', '')
            session['user_perfil'] = user.get('perfil', 'comum')
            session['login_time'] = datetime.now().isoformat()

            flash(f'Bem-vindo(a), {user.get("nome")}!', 'success')

            # Redirecionar baseado no perfil
            if int(user['id']) == 0:
                return redirect(url_for('admin_global'))
            elif user.get('perfil') == 'corporativo':
                return redirect(url_for('admin_corporativo'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Senha incorreta.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════════════════════
#  ADMIN GLOBAL (ID 0)
# ═══════════════════════════════════════════════════════════════════

@app.route('/admin/global')
@login_required
@admin_global_required
def admin_global():
    """Painel do Administrador Geral."""
    metricas = get_metricas_globais(DATA_DIR)
    usuarios = listar_usuarios(DATA_DIR)
    return render_template('admin_global.html', metricas=metricas, usuarios=usuarios)


@app.route('/admin/global/usuarios', methods=['POST'])
@login_required
@admin_global_required
def admin_global_criar_usuario():
    """Cria um novo usuário (Admin Global)."""
    nome = request.form.get('nome', '').strip()[:MAX_USER_NAME_LENGTH]
    email = request.form.get('email', '').strip()[:MAX_USER_EMAIL_LENGTH]
    senha = request.form.get('senha', '')
    perfil = request.form.get('perfil', 'comum')
    id_corporacao = validate_id_corporacao(request.form.get('id_corporacao', ''))

    # Validações
    if not nome:
        flash('Nome é obrigatório.', 'error')
        return redirect(url_for('admin_global'))
    if not email:
        flash('Email é obrigatório.', 'error')
        return redirect(url_for('admin_global'))
    if not validate_email(email):
        flash('Formato de email inválido.', 'error')
        return redirect(url_for('admin_global'))
    if len(senha) < MIN_PASSWORD_LENGTH:
        flash(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres.', 'error')
        return redirect(url_for('admin_global'))
    if perfil not in ('comum', 'corporativo', 'admin'):
        flash('Perfil inválido.', 'error')
        return redirect(url_for('admin_global'))

    # Verificar limite de usuários por corporação
    if id_corporacao:
        todos = listar_usuarios(DATA_DIR)
        count_corp = sum(1 for u in todos if u.get('id_corporacao') == id_corporacao)
        if count_corp >= MAX_USERS_PER_CORPORACAO:
            flash(f'Limite máximo de {MAX_USERS_PER_CORPORACAO} usuários por corporação atingido.', 'error')
            return redirect(url_for('admin_global'))

    # Verificar se email já existe
    existing = get_usuario_por_email(DATA_DIR, email)
    if existing:
        flash('Email já cadastrado.', 'error')
        return redirect(url_for('admin_global'))

    dados = {
        'nome': nome,
        'email': email,
        'senha_hash': generate_password_hash(senha),
        'perfil': perfil,
        'id_corporacao': id_corporacao,
        'ativo': 'true',
    }

    criar_usuario(DATA_DIR, dados)
    flash(f'Usuário {nome} criado com sucesso!', 'success')
    return redirect(url_for('admin_global'))


@app.route('/admin/global/usuarios/<int:user_id>/editar', methods=['POST'])
@login_required
@admin_global_required
def admin_global_editar_usuario(user_id):
    """Edita dados de um usuário (Admin Global)."""
    # Impedir edição de campos protegidos
    PROTECTED_FIELDS = {'id', 'created_at', 'senha_hash'}

    dados = {}
    for campo in ['nome', 'email', 'perfil', 'id_corporacao']:
        if campo in PROTECTED_FIELDS:
            continue
        val = request.form.get(campo, '').strip()
        if val:
            if campo == 'nome':
                dados[campo] = val[:MAX_USER_NAME_LENGTH]
            elif campo == 'email':
                if not validate_email(val):
                    flash('Formato de email inválido.', 'error')
                    return redirect(url_for('admin_global'))
                dados[campo] = val[:MAX_USER_EMAIL_LENGTH]
            elif campo == 'id_corporacao':
                dados[campo] = validate_id_corporacao(val)
            elif campo == 'perfil':
                if val not in ('comum', 'corporativo', 'admin'):
                    flash('Perfil inválido.', 'error')
                    return redirect(url_for('admin_global'))
                dados[campo] = val
            else:
                dados[campo] = val

    nova_senha = request.form.get('senha', '')
    if nova_senha:
        if len(nova_senha) < MIN_PASSWORD_LENGTH:
            flash(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres.', 'error')
            return redirect(url_for('admin_global'))
        dados['senha_hash'] = generate_password_hash(nova_senha)

    if 'ativo' in request.form:
        dados['ativo'] = request.form['ativo']
    elif 'ativo' not in request.form and request.form.get('acao') == 'suspender':
        dados['ativo'] = 'false'
    elif request.form.get('acao') == 'reativar':
        dados['ativo'] = 'true'

    result = atualizar_usuario(DATA_DIR, user_id, dados)
    if result:
        flash('Usuário atualizado com sucesso!', 'success')
    else:
        flash('Usuário não encontrado.', 'error')

    return redirect(url_for('admin_global'))


@app.route('/admin/global/usuarios/<int:user_id>/suspender', methods=['POST'])
@login_required
@admin_global_required
def admin_global_suspender_usuario(user_id):
    """Suspende/reativa um usuário."""
    acao = request.form.get('acao', '')
    if acao == 'reativar':
        atualizar_usuario(DATA_DIR, user_id, {'ativo': 'true'})
        flash('Usuário reativado.', 'success')
    else:
        atualizar_usuario(DATA_DIR, user_id, {'ativo': 'false'})
        flash('Usuário suspenso.', 'warning')

    return redirect(url_for('admin_global'))


@app.route('/admin/global/usuarios/<int:user_id>/excluir', methods=['POST'])
@login_required
@admin_global_required
def admin_global_excluir_usuario(user_id):
    """Exclui permanentemente um usuário."""
    if user_id == 0:
        flash('Não é possível excluir o Administrador Geral.', 'error')
        return redirect(url_for('admin_global'))

    if remover_usuario(DATA_DIR, user_id):
        flash('Usuário e seus dados excluídos.', 'success')
    else:
        flash('Usuário não encontrado.', 'error')

    return redirect(url_for('admin_global'))


@app.route('/admin/global/metricas')
@login_required
@admin_global_required
def admin_global_metricas_api():
    """API de métricas globais (JSON)."""
    metricas = get_metricas_globais(DATA_DIR)
    return jsonify(metricas)


@app.route('/admin/global/logs')
@login_required
@admin_global_required
def admin_global_logs():
    """Visualiza logs de armazenamento (tamanhos de arquivos OKF)."""
    logs = []
    # Informações do arquivo usuarios.okf
    usuarios_path = os.path.join(DATA_DIR, 'usuarios.okf')
    if os.path.exists(usuarios_path):
        logs.append({
            'arquivo': 'usuarios.okf',
            'tamanho': os.path.getsize(usuarios_path),
            'modificado': datetime.fromtimestamp(
                os.path.getmtime(usuarios_path)
            ).isoformat(),
        })

    # Informações dos diretórios de usuários
    users_dir = os.path.join(DATA_DIR, 'kanban_users')
    if os.path.exists(users_dir):
        for uid in sorted(os.listdir(users_dir)):
            uid_dir = os.path.join(users_dir, uid)
            if os.path.isdir(uid_dir):
                user = get_usuario_por_id(DATA_DIR, int(uid)) if uid.isdigit() else None
                for fname in sorted(os.listdir(uid_dir)):
                    fpath = os.path.join(uid_dir, fname)
                    if fname.endswith('.okf') and os.path.isfile(fpath):
                        logs.append({
                            'arquivo': f"kanban_users/{uid}/{fname}",
                            'usuario': user.get('nome', uid) if user else uid,
                            'tamanho': os.path.getsize(fpath),
                            'modificado': datetime.fromtimestamp(
                                os.path.getmtime(fpath)
                            ).isoformat(),
                        })

    return render_template('admin_global.html',
                          metricas=get_metricas_globais(DATA_DIR),
                          usuarios=listar_usuarios(DATA_DIR),
                          logs=logs)


# ═══════════════════════════════════════════════════════════════════
#  ADMIN CORPORATIVO
# ═══════════════════════════════════════════════════════════════════

@app.route('/admin/corporativo')
@login_required
@admin_corporativo_required
def admin_corporativo():
    """Painel do Administrador Corporativo."""
    user = get_usuario_por_id(DATA_DIR, session['user_id'])
    corporacao_id = user.get('id_corporacao', '') if user else ''

    # Filtrar usuários da mesma corporação
    todos = listar_usuarios(DATA_DIR)
    usuarios_corp = [u for u in todos
                     if u.get('id_corporacao') == corporacao_id
                     or u.get('id') == str(session['user_id'])]

    # Quadros da equipe
    quadros_equipe = []
    for u in usuarios_corp:
        uid = int(u['id'])
        if uid == session['user_id']:
            continue
        boards = listar_quadros(DATA_DIR, uid)
        for b in boards:
            b['usuario_nome'] = u.get('nome', uid)
            b['usuario_id'] = uid
            quadros_equipe.append(b)

    # Quadros do próprio admin corporativo
    meus_quadros = listar_quadros(DATA_DIR, session['user_id'])

    return render_template('admin_corporativo.html',
                          usuarios=usuarios_corp,
                          quadros_equipe=quadros_equipe,
                          corporacao_id=corporacao_id,
                          meus_quadros=meus_quadros)


@app.route('/admin/corporativo/usuarios', methods=['POST'])
@login_required
@admin_corporativo_required
def admin_corporativo_criar_usuario():
    """Cria um usuário comum sob a corporação."""
    user = get_usuario_por_id(DATA_DIR, session['user_id'])
    corporacao_id = user.get('id_corporacao', '')

    nome = request.form.get('nome', '').strip()[:MAX_USER_NAME_LENGTH]
    email = request.form.get('email', '').strip()[:MAX_USER_EMAIL_LENGTH]
    senha = request.form.get('senha', '')

    if not nome:
        flash('Nome é obrigatório.', 'error')
        return redirect(url_for('admin_corporativo'))
    if not email:
        flash('Email é obrigatório.', 'error')
        return redirect(url_for('admin_corporativo'))
    if not validate_email(email):
        flash('Formato de email inválido.', 'error')
        return redirect(url_for('admin_corporativo'))
    if len(senha) < MIN_PASSWORD_LENGTH:
        flash(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres.', 'error')
        return redirect(url_for('admin_corporativo'))

    # Limite de usuários por corporação
    todos = listar_usuarios(DATA_DIR)
    count_corp = sum(1 for u in todos if u.get('id_corporacao') == corporacao_id)
    if count_corp >= MAX_USERS_PER_CORPORACAO:
        flash(f'Limite máximo de {MAX_USERS_PER_CORPORACAO} usuários por corporação.', 'error')
        return redirect(url_for('admin_corporativo'))

    existing = get_usuario_por_email(DATA_DIR, email)
    if existing:
        flash('Email já cadastrado.', 'error')
        return redirect(url_for('admin_corporativo'))

    dados = {
        'nome': nome,
        'email': email,
        'senha_hash': generate_password_hash(senha),
        'perfil': 'comum',
        'id_corporacao': corporacao_id,
        'ativo': 'true',
    }

    criar_usuario(DATA_DIR, dados)
    flash(f'Usuário {nome} criado na corporação!', 'success')
    return redirect(url_for('admin_corporativo'))


@app.route('/admin/corporativo/quadros/<int:user_id>')
@login_required
@admin_corporativo_required
def admin_corporativo_ver_quadros(user_id):
    """Visualiza quadros de um usuário da equipe (admin corporativo)."""
    quadros = listar_quadros(DATA_DIR, user_id)
    usuario = get_usuario_por_id(DATA_DIR, user_id)
    return render_template('admin_corporativo.html',
                          quadros_usuario=quadros,
                          usuario_alvo=usuario,
                          usuarios=[],
                          quadros_equipe=[])


# ═══════════════════════════════════════════════════════════════════
#  DASHBOARD DO USUÁRIO (Quadros)
# ═══════════════════════════════════════════════════════════════════

@app.route('/')
@login_required
def index():
    """Redireciona para o dashboard apropriado baseado no perfil."""
    perfil = session.get('user_perfil', 'comum')
    if session.get('user_id') == 0:
        return redirect(url_for('admin_global'))
    elif perfil == 'corporativo':
        return redirect(url_for('admin_corporativo'))
    else:
        return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard do usuário: lista de quadros Kanban."""
    user_id = session['user_id']
    quadros = listar_quadros(DATA_DIR, user_id)
    user = get_usuario_por_id(DATA_DIR, user_id)
    espaco = get_espaco_disco_usuario(DATA_DIR, user_id)
    return render_template('dashboard.html', quadros=quadros,
                          user=user, espaco=espaco)


@app.route('/dashboard/criar', methods=['POST'])
@login_required
@enforce_limits
@check_plan_limits
def dashboard_criar_quadro():
    """Cria um novo quadro Kanban."""
    user_id = session['user_id']
    nome = request.form.get('nome', '').strip()
    titulo = request.form.get('titulo', '').strip() or nome
    descricao = request.form.get('descricao', '').strip()

    nome = sanitize_board_name(nome)
    if not nome:
        flash('Nome do quadro inválido.', 'error')
        return redirect(url_for('dashboard'))

    titulo = titulo[:MAX_BOARD_TITLE_LENGTH]
    descricao = descricao[:MAX_BOARD_DESC_LENGTH]

    if not nome:
        flash('Nome do quadro é obrigatório.', 'error')
        return redirect(url_for('dashboard'))

    # Verificar limite de quadros
    quadros = listar_quadros(DATA_DIR, user_id)
    if len(quadros) >= Config.MAX_QUADROS_POR_USUARIO:
        flash(f'Limite máximo de {Config.MAX_QUADROS_POR_USUARIO} quadros atingido.', 'error')
        return redirect(url_for('dashboard'))

    result = criar_quadro(DATA_DIR, user_id, nome, titulo, descricao)
    if result:
        flash(f'Quadro "{titulo}" criado com sucesso!', 'success')
    else:
        flash('Erro ao criar quadro. Nome pode já existir.', 'error')

    return redirect(url_for('dashboard'))


@app.route('/dashboard/<board_name>')
@login_required
def board_view(board_name):
    """Visualiza um quadro Kanban específico.
    Suporta user_id opcional na query string para admin corporativo ver quadros da equipe.
    """
    board_name = sanitize_board_name(board_name)
    if not board_name:
        flash('Quadro não encontrado.', 'error')
        return redirect(url_for('dashboard'))

    target_user_id = request.args.get('user_id', session['user_id'], type=int)

    # Validação de permissão
    current_user_id = session['user_id']
    if current_user_id != 0 and current_user_id != target_user_id:
        # Verificar se é admin corporativo com acesso ao usuário
        current_user = get_usuario_por_id(DATA_DIR, current_user_id)
        target_user = get_usuario_por_id(DATA_DIR, target_user_id)
        if (current_user and target_user and
            current_user.get('perfil') == 'corporativo' and
            current_user.get('id_corporacao') and
            current_user.get('id_corporacao') == target_user.get('id_corporacao')):
            pass  # permitido
        else:
            abort(403, description="Você não tem permissão para acessar este quadro.")

    quadro = get_quadro_completo(DATA_DIR, target_user_id, board_name)

    if not quadro:
        flash('Quadro não encontrado.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('board.html', quadro=quadro)


@app.route('/dashboard/<board_name>/excluir', methods=['POST'])
@login_required
def board_delete(board_name):
    """Exclui um quadro Kanban."""
    user_id = session['user_id']
    board_name = sanitize_board_name(board_name)
    if not board_name:
        flash('Quadro não encontrado.', 'error')
        return redirect(url_for('dashboard'))
    if deletar_quadro(DATA_DIR, user_id, board_name):
        flash('Quadro excluído.', 'success')
    else:
        flash('Erro ao excluir quadro.', 'error')
    return redirect(url_for('dashboard'))


# ═══════════════════════════════════════════════════════════════════
#  API KANBAN (JSON - usada pelo frontend Drag & Drop)
# ═══════════════════════════════════════════════════════════════════

@app.route('/api/quadro/<board_name>')
@login_required
def api_get_quadro(board_name):
    """Retorna dados completos do quadro em JSON."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404
    user_id = session['user_id']
    quadro = get_quadro_completo(DATA_DIR, user_id, board_name)
    if not quadro:
        return jsonify({'error': 'Quadro não encontrado'}), 404
    return jsonify(quadro)


@app.route('/api/quadro/<board_name>/card', methods=['POST'])
@login_required
@rate_limit(max_requests=30, window_seconds=60)
def api_add_card(board_name):
    """Adiciona um novo cartão via JSON."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404
    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    column_id = data.get('column_id', '')
    card_data = {
        'titulo': (data.get('titulo', 'Novo Cartão') or '')[:MAX_CARD_TITLE_LENGTH],
        'descricao': (data.get('descricao', '') or '')[:MAX_CARD_DESC_LENGTH],
        'prioridade': data.get('prioridade', 'media') if data.get('prioridade') in ('alta', 'media', 'baixa') else 'media',
        'data_entrega': (data.get('data_entrega', '') or '')[:10],
    }

    # Limite de cartões por quadro (plano-based)
    quadro = get_quadro_completo(DATA_DIR, user_id, board_name)
    if quadro:
        total_cards = sum(len(c['cards']) for c in quadro['colunas'])
        plan_limits = get_plan_limits(user_id)
        max_cards = plan_limits.get('max_cartoes', MAX_CARDS_PER_BOARD)
        if total_cards >= max_cards:
            return jsonify({'error': f'Limite do seu plano: máximo de {max_cards} cartões por quadro.'}), 400

    result = adicionar_card(DATA_DIR, user_id, board_name, column_id, card_data)
    if result:
        return jsonify({'success': True, 'card': result}), 201
    return jsonify({'error': 'Erro ao criar cartão'}), 400


@app.route('/api/quadro/<board_name>/card/<card_id>', methods=['PUT'])
@login_required
def api_update_card(board_name, card_id):
    """Atualiza dados de um cartão."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404

    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    # Validar card_id
    if not card_id or not _re.match(r'^card_\d{3,}$', card_id):
        return jsonify({'error': 'ID de cartão inválido.'}), 400

    # Sanitizar dados - só permitir campos conhecidos
    ALLOWED_CARD_FIELDS = {'titulo', 'descricao', 'prioridade', 'data_entrega'}
    sanitized = {}
    for key in data:
        if key in ALLOWED_CARD_FIELDS:
            if key == 'titulo':
                sanitized[key] = str(data[key])[:MAX_CARD_TITLE_LENGTH]
            elif key == 'descricao':
                sanitized[key] = str(data[key])[:MAX_CARD_DESC_LENGTH]
            elif key == 'prioridade':
                sanitized[key] = data[key] if data[key] in ('alta', 'media', 'baixa') else 'media'
            elif key == 'data_entrega':
                sanitized[key] = str(data[key])[:10]

    if not sanitized:
        return jsonify({'error': 'Nenhum campo válido para atualizar.'}), 400

    if atualizar_card(DATA_DIR, user_id, board_name, card_id, sanitized):
        return jsonify({'success': True})
    return jsonify({'error': 'Cartão não encontrado'}), 404


@app.route('/api/quadro/<board_name>/card/<card_id>', methods=['DELETE'])
@login_required
def api_delete_card(board_name, card_id):
    """Remove um cartão."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404
    if not card_id or not _re.match(r'^card_\d{3,}$', card_id):
        return jsonify({'error': 'ID de cartão inválido.'}), 400

    user_id = session['user_id']
    if remover_card(DATA_DIR, user_id, board_name, card_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Cartão não encontrado'}), 404


@app.route('/api/quadro/<board_name>/card/<card_id>/mover', methods=['PUT'])
@login_required
def api_move_card(board_name, card_id):
    """Move um cartão entre colunas ou reordena."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404

    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    column_id = (data.get('column_id', '') or '')[:50]
    if not column_id:
        return jsonify({'error': 'column_id é obrigatório.'}), 400

    # Validar card_id
    if not card_id or not _re.match(r'^card_\d{3,}$', card_id):
        return jsonify({'error': 'ID de cartão inválido.'}), 400

    # Validar new_index
    try:
        new_index = int(data.get('new_index', -1))
    except (ValueError, TypeError):
        new_index = -1
    if new_index < -1 or new_index > 500:
        new_index = -1

    # Verificar se a coluna de destino existe
    quadro = get_quadro_completo(DATA_DIR, user_id, board_name)
    if quadro:
        col_ids = [c['id'] for c in quadro['colunas']]
        if column_id not in col_ids:
            return jsonify({'error': 'Coluna de destino não encontrada.'}), 400

    if mover_card(DATA_DIR, user_id, board_name, card_id, column_id, new_index):
        return jsonify({'success': True})
    return jsonify({'error': 'Erro ao mover cartão'}), 400


@app.route('/api/quadro/<board_name>/coluna', methods=['POST'])
@login_required
@rate_limit(max_requests=30, window_seconds=60)
def api_add_column(board_name):
    """Adiciona uma nova coluna."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404

    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    titulo = (data.get('title', 'Nova Coluna') or '')[:MAX_COLUMN_TITLE_LENGTH]
    if not titulo.strip():
        return jsonify({'error': 'Título da coluna é obrigatório.'}), 400

    # Verificar limite de colunas por quadro
    quadro = get_quadro_completo(DATA_DIR, user_id, board_name)
    if quadro and len(quadro['colunas']) >= MAX_COLUMNS_PER_BOARD:
        return jsonify({'error': f'Limite máximo de {MAX_COLUMNS_PER_BOARD} colunas por quadro.'}), 400

    result = adicionar_coluna(DATA_DIR, user_id, board_name, titulo)

    if result:
        return jsonify({'success': True, 'column': result}), 201
    return jsonify({'error': 'Coluna já existe ou erro ao criar'}), 400


@app.route('/api/quadro/<board_name>/coluna/<column_id>', methods=['PUT'])
@login_required
def api_update_column(board_name, column_id):
    """Atualiza dados de uma coluna."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404

    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    # Sanitizar dados - só permitir campos conhecidos
    ALLOWED_COLUMN_FIELDS = {'title', 'order'}
    sanitized = {}
    for key in data:
        if key in ALLOWED_COLUMN_FIELDS:
            if key == 'title':
                sanitized[key] = str(data[key])[:MAX_COLUMN_TITLE_LENGTH]
            elif key == 'order':
                try:
                    val = int(data[key])
                    if 0 <= val <= 20:
                        sanitized[key] = str(val)
                except (ValueError, TypeError):
                    pass

    if not sanitized:
        return jsonify({'error': 'Nenhum campo válido para atualizar.'}), 400

    if atualizar_coluna(DATA_DIR, user_id, board_name, column_id, sanitized):
        return jsonify({'success': True})
    return jsonify({'error': 'Coluna não encontrada'}), 404


@app.route('/api/quadro/<board_name>/coluna/<column_id>', methods=['DELETE'])
@login_required
def api_delete_column(board_name, column_id):
    """Remove uma coluna e seus cartões."""
    board_name = sanitize_board_name(board_name)
    if not board_name:
        return jsonify({'error': 'Quadro não encontrado'}), 404
    if not column_id or len(column_id) > 50:
        return jsonify({'error': 'ID de coluna inválido.'}), 400

    user_id = session['user_id']
    if remover_coluna(DATA_DIR, user_id, board_name, column_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Coluna não encontrada'}), 404


# ═══════════════════════════════════════════════════════════════════
#  PLANOS E ASSINATURAS
# ═══════════════════════════════════════════════════════════════════

from datetime import datetime

@app.route('/planos')
@login_required
def planos():
    """Página de planos disponíveis."""
    user_id = session['user_id']
    user = get_usuario_por_id(DATA_DIR, user_id)
    return render_template('planos.html', user=user)


@app.route('/planos/assinar', methods=['POST'])
@login_required
@rate_limit(max_requests=10, window_seconds=60)
def planos_assinar():
    """Assina um plano (simulação de pagamento)."""
    user_id = session['user_id']
    plano = request.form.get('plano', '')[:20]
    tipo_pagamento = request.form.get('tipo_pagamento', 'pago')[:20]

    if plano not in ('comum', 'corporativo'):
        flash('Plano inválido.', 'error')
        return redirect(url_for('planos'))

    if tipo_pagamento not in ('pago', 'propaganda'):
        flash('Tipo de pagamento inválido.', 'error')
        return redirect(url_for('planos'))

    # Validar: corporativo só para admins corporativos
    if plano == 'corporativo':
        user = get_usuario_por_id(DATA_DIR, user_id)
        if not user or user.get('perfil') != 'corporativo':
            flash('Plano corporativo disponível apenas para administradores corporativos.', 'error')
            return redirect(url_for('planos'))

    dados = {
        'plano': plano,
        'assinatura_desde': datetime.now().isoformat(),
        'assinatura_ativa': 'true',
    }

    if plano == 'comum' and tipo_pagamento == 'propaganda':
        dados['aceita_propaganda'] = 'true'
    else:
        dados['aceita_propaganda'] = 'false'

    atualizar_usuario(DATA_DIR, user_id, dados)
    session['user_plan'] = plano
    flash(f'Plano {plano} ativado com sucesso!', 'success')
    return redirect(url_for('planos'))


@app.route('/planos/cancelar', methods=['POST'])
@login_required
def planos_cancelar():
    """Cancela a assinatura (volta para gratuito)."""
    user_id = session['user_id']
    dados = {
        'plano': 'gratuito',
        'aceita_propaganda': 'false',
    }
    atualizar_usuario(DATA_DIR, user_id, dados)
    session['user_plan'] = 'gratuito'
    flash('Assinatura cancelada. Você está no plano Gratuito.', 'info')
    return redirect(url_for('planos'))


@app.route('/admin/global/usuarios/<int:user_id>/plano', methods=['POST'])
@login_required
@admin_global_required
def admin_global_plano_usuario(user_id):
    """Admin Global altera o plano de um usuário."""
    plano = request.form.get('plano', 'gratuito')
    if plano not in ('gratuito', 'comum', 'corporativo'):
        flash('Plano inválido.', 'error')
        return redirect(url_for('admin_global'))

    dados = {
        'plano': plano,
        'assinatura_ativa': 'true' if plano != 'gratuito' else 'false',
    }
    if plano == 'gratuito':
        dados['aceita_propaganda'] = 'false'

    atualizar_usuario(DATA_DIR, user_id, dados)
    flash(f'Plano do usuário alterado para {plano}.', 'success')
    return redirect(url_for('admin_global'))


# ═══════════════════════════════════════════════════════════════════
#  ADMIN DO USUÁRIO (Configurações pessoais)
# ═══════════════════════════════════════════════════════════════════

@app.route('/admin/user', methods=['GET', 'POST'])
@login_required
def admin_user():
    """Página de configurações do usuário comum."""
    user_id = session['user_id']
    user = get_usuario_por_id(DATA_DIR, user_id)
    espaco = get_espaco_disco_usuario(DATA_DIR, user_id)

    if request.method == 'POST':
        dados = {}
        nome = request.form.get('nome', '').strip()[:MAX_USER_NAME_LENGTH]
        email = request.form.get('email', '').strip()[:MAX_USER_EMAIL_LENGTH]
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if nome:
            if len(nome) < 2:
                flash('Nome deve ter no mínimo 2 caracteres.', 'error')
                return redirect(url_for('admin_user'))
            dados['nome'] = nome
        if email:
            if not validate_email(email):
                flash('Formato de email inválido.', 'error')
                return redirect(url_for('admin_user'))
            # Verificar se email já está em uso
            existing = get_usuario_por_email(DATA_DIR, email)
            if existing and int(existing['id']) != user_id:
                flash('Email já está em uso por outro usuário.', 'error')
                return redirect(url_for('admin_user'))
            dados['email'] = email

        if nova_senha:
            if len(nova_senha) < MIN_PASSWORD_LENGTH:
                flash(f'Nova senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres.', 'error')
                return redirect(url_for('admin_user'))
            if not check_password_hash(user['senha_hash'], senha_atual):
                flash('Senha atual incorreta.', 'error')
                return redirect(url_for('admin_user'))
            if nova_senha != confirmar_senha:
                flash('Nova senha e confirmação não conferem.', 'error')
                return redirect(url_for('admin_user'))
            dados['senha_hash'] = generate_password_hash(nova_senha)

            # Renovar sessão após troca de senha
            session['login_time'] = datetime.now().isoformat()

        if dados:
            atualizar_usuario(DATA_DIR, user_id, dados)
            session['user_name'] = dados.get('nome', session.get('user_name'))
            flash('Dados atualizados com sucesso!', 'success')

        return redirect(url_for('admin_user'))

    return render_template('admin_user.html', user=user, espaco=espaco)


# ═══════════════════════════════════════════════════════════════════
#  INICIALIZAÇÃO
# ═══════════════════════════════════════════════════════════════════

def init_sample_data():
    """
    Inicializa dados de exemplo se o arquivo usuarios.okf não existir.
    Cria usuários padrão e quadros de exemplo.
    """
    usuarios_path = os.path.join(DATA_DIR, 'usuarios.okf')
    if os.path.exists(usuarios_path):
        return  # Já inicializado

    print("[init] Inicializando dados de exemplo...")

    # Garantir diretórios
    os.makedirs(DATA_DIR, exist_ok=True)

    # Criar usuários
    usuarios = [
        {
            'id': '0',
            'nome': 'Administrador Geral',
            'email': 'admin@sistema.com',
            'senha_hash': generate_password_hash('admin123'),
            'perfil': 'admin',
            'plano': 'comum',
            'id_corporacao': '',
            'ativo': 'true',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        },
        {
            'id': '101',
            'nome': 'Admin Corporativo',
            'email': 'corp@empresa.com',
            'senha_hash': generate_password_hash('corp123'),
            'perfil': 'corporativo',
            'plano': 'corporativo',
            'assinatura_ativa': 'true',
            'id_corporacao': '1',
            'ativo': 'true',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        },
        {
            'id': '102',
            'nome': 'Usuário Comum',
            'email': 'user@email.com',
            'senha_hash': generate_password_hash('user123'),
            'perfil': 'comum',
            'plano': 'gratuito',
            'id_corporacao': '1',
            'ativo': 'true',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        },
    ]

    from okf_manager import parse_okf, serialize_okf, write_okf, get_user_dir

    # Construir conteúdo OKF manualmente para garantir formato
    lines = []
    for u in usuarios:
        lines.append(f"[user:{u['id']}]")
        for key, value in u.items():
            lines.append(f"{key}={value}")
        lines.append('')

    content = '\n'.join(lines)
    with open(usuarios_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Criar diretórios dos usuários
    for u in usuarios:
        uid = int(u['id'])
        os.makedirs(get_user_dir(DATA_DIR, uid), exist_ok=True)

    # Criar quadros de exemplo
    # Quadro do Admin Geral (ID 0)
    criar_quadro(DATA_DIR, 0, 'sistema', 'Monitoramento do Sistema',
                 'Quadro para acompanhar tarefas do sistema.')

    # Adicionar cartões ao quadro do Admin
    adicionar_card(DATA_DIR, 0, 'sistema', 'a-fazer', {
        'titulo': 'Revisar logs de segurança',
        'descricao': 'Verificar tentativas de acesso suspeitas',
        'prioridade': 'alta',
        'data_entrega': '2026-07-05',
    })
    adicionar_card(DATA_DIR, 0, 'sistema', 'em-progresso', {
        'titulo': 'Atualizar política de senhas',
        'descricao': 'Implementar requisitos mínimos de segurança',
        'prioridade': 'media',
        'data_entrega': '2026-07-10',
    })
    adicionar_card(DATA_DIR, 0, 'sistema', 'concluido', {
        'titulo': 'Backup semanal realizado',
        'descricao': 'Backup completo do banco de dados OKF',
        'prioridade': 'baixa',
        'data_entrega': '2026-06-28',
    })

    # Quadros do Admin Corporativo (ID 101)
    criar_quadro(DATA_DIR, 101, 'vendas', 'Vendas',
                 'Acompanhamento de metas de vendas da equipe.')
    criar_quadro(DATA_DIR, 101, 'marketing', 'Marketing',
                 'Campanhas e ações de marketing.')

    adicionar_card(DATA_DIR, 101, 'vendas', 'a-fazer', {
        'titulo': 'Prospectar novos clientes',
        'descricao': 'Listar empresas do setor para abordagem',
        'prioridade': 'alta',
        'data_entrega': '2026-07-15',
    })
    adicionar_card(DATA_DIR, 101, 'vendas', 'em-progresso', {
        'titulo': 'Follow-up propostas enviadas',
        'descricao': 'Revisar propostas da semana anterior',
        'prioridade': 'media',
        'data_entrega': '2026-07-08',
    })
    adicionar_card(DATA_DIR, 101, 'marketing', 'a-fazer', {
        'titulo': 'Criar campanha redes sociais',
        'descricao': 'Planejar conteúdo para Instagram e LinkedIn',
        'prioridade': 'alta',
        'data_entrega': '2026-07-20',
    })
    adicionar_card(DATA_DIR, 101, 'marketing', 'concluido', {
        'titulo': 'Relatório de métricas mensais',
        'descricao': 'Compilar dados de engajamento do mês',
        'prioridade': 'media',
        'data_entrega': '2026-06-30',
    })

    # Quadro do Usuário Comum (ID 102)
    criar_quadro(DATA_DIR, 102, 'pessoal', 'Projetos Pessoais',
                 'Tarefas e projetos pessoais.')

    adicionar_card(DATA_DIR, 102, 'pessoal', 'a-fazer', {
        'titulo': 'Organizar documentos',
        'descricao': 'Digitalizar e arquivar documentos importantes',
        'prioridade': 'baixa',
        'data_entrega': '2026-07-30',
    })
    adicionar_card(DATA_DIR, 102, 'pessoal', 'em-progresso', {
        'titulo': 'Curso online de Python',
        'descricao': 'Finalizar módulo de manipulação de arquivos',
        'prioridade': 'media',
        'data_entrega': '2026-07-12',
    })
    adicionar_card(DATA_DIR, 102, 'pessoal', 'a-fazer', {
        'titulo': 'Planejar viagem de férias',
        'descricao': 'Pesquisar destinos e orçar passagens',
        'prioridade': 'baixa',
        'data_entrega': '2026-08-01',
    })
    adicionar_card(DATA_DIR, 102, 'pessoal', 'concluido', {
        'titulo': 'Renovar assinaturas',
        'descricao': 'Atualizar pagamentos recorrentes',
        'prioridade': 'alta',
        'data_entrega': '2026-06-25',
    })

    print("[init] Dados de exemplo criados com sucesso!")
    print("  Admin Geral:    admin@sistema.com / admin123")
    print("  Admin Corp:     corp@empresa.com / corp123")
    print("  Usuário Comum:  user@email.com / user123")


# ─── Main ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    init_sample_data()
    bind_host = os.environ.get('FLASK_HOST', '127.0.0.1')
    bind_port = int(os.environ.get('FLASK_PORT', '5000'))
    print(f"[app] Servidor iniciando em http://{bind_host}:{bind_port}")
    print(f"[app] Diretório de dados: {DATA_DIR}")
    app.run(host=bind_host, port=bind_port, debug=debug_mode)
