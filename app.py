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
from datetime import datetime

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

DATA_DIR = Config.DATA_DIR


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
def login():
    """Página de login / autenticação."""
    if session.get('user_id') is not None:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Preencha email e senha.', 'error')
            return render_template('login.html')

        user = get_usuario_por_email(DATA_DIR, email)
        if not user:
            flash('Usuário não encontrado.', 'error')
            return render_template('login.html')

        if user.get('ativo', 'true') == 'false':
            flash('Usuário suspenso. Contate o administrador.', 'error')
            return render_template('login.html')

        if check_password_hash(user.get('senha_hash', ''), senha):
            session['user_id'] = int(user['id'])
            session['user_name'] = user.get('nome', '')
            session['user_perfil'] = user.get('perfil', 'comum')

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
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip(),
        'senha_hash': generate_password_hash(request.form.get('senha', '')),
        'perfil': request.form.get('perfil', 'comum'),
        'id_corporacao': request.form.get('id_corporacao', '').strip(),
        'ativo': 'true',
    }


    if not dados['nome'] or not dados['email']:
        flash('Nome e email são obrigatórios.', 'error')
        return redirect(url_for('admin_global'))

    # Verificar se email já existe
    existing = get_usuario_por_email(DATA_DIR, dados['email'])
    if existing:
        flash('Email já cadastrado.', 'error')
        return redirect(url_for('admin_global'))

    criar_usuario(DATA_DIR, dados)
    flash(f'Usuário {dados["nome"]} criado com sucesso!', 'success')
    return redirect(url_for('admin_global'))


@app.route('/admin/global/usuarios/<int:user_id>/editar', methods=['POST'])
@login_required
@admin_global_required
def admin_global_editar_usuario(user_id):
    """Edita dados de um usuário (Admin Global)."""
    dados = {}
    for campo in ['nome', 'email', 'perfil', 'id_corporacao']:
        val = request.form.get(campo, '').strip()
        if val:
            dados[campo] = val

    if request.form.get('senha'):
        dados['senha_hash'] = generate_password_hash(request.form['senha'])

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

    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip(),
        'senha_hash': generate_password_hash(request.form.get('senha', '')),
        'perfil': 'comum',
        'id_corporacao': user.get('id_corporacao', ''),
        'ativo': 'true',
    }

    if not dados['nome'] or not dados['email']:
        flash('Nome e email são obrigatórios.', 'error')
        return redirect(url_for('admin_corporativo'))

    existing = get_usuario_por_email(DATA_DIR, dados['email'])
    if existing:
        flash('Email já cadastrado.', 'error')
        return redirect(url_for('admin_corporativo'))

    criar_usuario(DATA_DIR, dados)
    flash(f'Usuário {dados["nome"]} criado na corporação!', 'success')
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
def dashboard_criar_quadro():
    """Cria um novo quadro Kanban."""
    user_id = session['user_id']
    nome = request.form.get('nome', '').strip()
    titulo = request.form.get('titulo', '').strip() or nome
    descricao = request.form.get('descricao', '').strip()

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
    user_id = session['user_id']
    quadro = get_quadro_completo(DATA_DIR, user_id, board_name)
    if not quadro:
        return jsonify({'error': 'Quadro não encontrado'}), 404
    return jsonify(quadro)


@app.route('/api/quadro/<board_name>/card', methods=['POST'])
@login_required
def api_add_card(board_name):
    """Adiciona um novo cartão via JSON."""
    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    column_id = data.get('column_id', '')
    card_data = {
        'titulo': data.get('titulo', 'Novo Cartão'),
        'descricao': data.get('descricao', ''),
        'prioridade': data.get('prioridade', 'media'),
        'data_entrega': data.get('data_entrega', ''),
    }

    result = adicionar_card(DATA_DIR, user_id, board_name, column_id, card_data)
    if result:
        return jsonify({'success': True, 'card': result}), 201
    return jsonify({'error': 'Erro ao criar cartão'}), 400


@app.route('/api/quadro/<board_name>/card/<card_id>', methods=['PUT'])
@login_required
def api_update_card(board_name, card_id):
    """Atualiza dados de um cartão."""
    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if atualizar_card(DATA_DIR, user_id, board_name, card_id, data):
        return jsonify({'success': True})
    return jsonify({'error': 'Cartão não encontrado'}), 404


@app.route('/api/quadro/<board_name>/card/<card_id>', methods=['DELETE'])
@login_required
def api_delete_card(board_name, card_id):
    """Remove um cartão."""
    user_id = session['user_id']

    if remover_card(DATA_DIR, user_id, board_name, card_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Cartão não encontrado'}), 404


@app.route('/api/quadro/<board_name>/card/<card_id>/mover', methods=['PUT'])
@login_required
def api_move_card(board_name, card_id):
    """Move um cartão entre colunas ou reordena."""
    user_id = session['user_id']
    data = request.get_json()

    column_id = data.get('column_id', '')
    new_index = data.get('new_index', -1)

    if mover_card(DATA_DIR, user_id, board_name, card_id, column_id, new_index):
        return jsonify({'success': True})
    return jsonify({'error': 'Erro ao mover cartão'}), 400


@app.route('/api/quadro/<board_name>/coluna', methods=['POST'])
@login_required
def api_add_column(board_name):
    """Adiciona uma nova coluna."""
    user_id = session['user_id']
    data = request.get_json()

    titulo = data.get('title', 'Nova Coluna')
    result = adicionar_coluna(DATA_DIR, user_id, board_name, titulo)

    if result:
        return jsonify({'success': True, 'column': result}), 201
    return jsonify({'error': 'Coluna já existe ou erro ao criar'}), 400


@app.route('/api/quadro/<board_name>/coluna/<column_id>', methods=['PUT'])
@login_required
def api_update_column(board_name, column_id):
    """Atualiza dados de uma coluna."""
    user_id = session['user_id']
    data = request.get_json()

    if atualizar_coluna(DATA_DIR, user_id, board_name, column_id, data):
        return jsonify({'success': True})
    return jsonify({'error': 'Coluna não encontrada'}), 404


@app.route('/api/quadro/<board_name>/coluna/<column_id>', methods=['DELETE'])
@login_required
def api_delete_column(board_name, column_id):
    """Remove uma coluna e seus cartões."""
    user_id = session['user_id']

    if remover_coluna(DATA_DIR, user_id, board_name, column_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Coluna não encontrada'}), 404


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
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if nome:
            dados['nome'] = nome
        if email:
            # Verificar se email já está em uso
            existing = get_usuario_por_email(DATA_DIR, email)
            if existing and int(existing['id']) != user_id:
                flash('Email já está em uso por outro usuário.', 'error')
                return redirect(url_for('admin_user'))
            dados['email'] = email

        if nova_senha:
            if not check_password_hash(user['senha_hash'], senha_atual):
                flash('Senha atual incorreta.', 'error')
                return redirect(url_for('admin_user'))
            if nova_senha != confirmar_senha:
                flash('Nova senha e confirmação não conferem.', 'error')
                return redirect(url_for('admin_user'))
            dados['senha_hash'] = generate_password_hash(nova_senha)

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
    init_sample_data()
    print(f"[app] Servidor iniciando em http://0.0.0.0:5000")
    print(f"[app] Diretório de dados: {DATA_DIR}")
    app.run(host='0.0.0.0', port=5000, debug=True)
