"""
Módulo de Abstração OKF (Objects Key Format)
Gerencia leitura, escrita, parsing e manipulação de arquivos .okf
Toda persistência é feita exclusivamente via arquivos OKF no sistema de arquivos local.
"""

import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import OrderedDict


def parse_okf(content: str) -> Dict[str, Any]:
    """
    Parseia o conteúdo de um arquivo OKF e retorna um dicionário estruturado.

    Formato:
        [section_type:section_key]
        key=value
        key2=value2

        [section_type:another_key]
        key=value

    Retorna:
        {
            'sections': {
                'user:0': {'type': 'user', 'key': '0', 'values': {'id': '0', 'nome': '...'}},
                'user:101': {'type': 'user', 'key': '101', 'values': {'id': '101', ...}},
            },
            'section_order': ['user:0', 'user:101', ...]
        }
    """
    result = {
        'sections': OrderedDict(),
        'section_order': []
    }

    current_section = None
    current_type = None
    current_key = None
    current_values = {}

    for line in content.split('\n'):
        stripped = line.strip()

        # Pular linhas vazias e comentários
        if not stripped or stripped.startswith('#'):
            continue

        # Verificar se é um cabeçalho de seção
        section_match = re.match(r'^\[([^:]+):(.+)\]$', stripped)
        if section_match:
            # Salvar seção anterior
            if current_type is not None and current_key is not None:
                section_id = f"{current_type}:{current_key}"
                result['sections'][section_id] = {
                    'type': current_type,
                    'key': current_key,
                    'values': dict(current_values)
                }
                result['section_order'].append(section_id)

            current_type = section_match.group(1).strip()
            current_key = section_match.group(2).strip()
            current_values = {}
            continue

        # Se for key=value dentro de uma seção
        if current_type is not None:
            kv_match = re.match(r'^([^=]+)=(.*)$', stripped)
            if kv_match:
                key = kv_match.group(1).strip()
                value = kv_match.group(2).strip()
                current_values[key] = value

    # Salvar última seção
    if current_type is not None and current_key is not None:
        section_id = f"{current_type}:{current_key}"
        result['sections'][section_id] = {
            'type': current_type,
            'key': current_key,
            'values': dict(current_values)
        }
        result['section_order'].append(section_id)

    return result


def serialize_okf(data: Dict[str, Any]) -> str:
    """
    Serializa um dicionário estruturado de volta para o formato OKF.
    """
    lines = []

    for section_id in data.get('section_order', []):
        section = data['sections'].get(section_id)
        if not section:
            continue

        lines.append(f"[{section['type']}:{section['key']}]")
        for key, value in section['values'].items():
            lines.append(f"{key}={value}")
        lines.append('')  # linha em branco entre seções

    return '\n'.join(lines)


def read_okf(filepath: str) -> Dict[str, Any]:
    """
    Lê um arquivo OKF do disco e retorna o dicionário estruturado.
    Se o arquivo não existir, retorna estrutura vazia.
    """
    if not os.path.exists(filepath):
        return {'sections': OrderedDict(), 'section_order': []}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return parse_okf(content)
    except Exception as e:
        raise IOError(f"Erro ao ler arquivo OKF {filepath}: {e}")


def write_okf(filepath: str, data: Dict[str, Any]) -> None:
    """
    Escreve um dicionário estruturado em um arquivo OKF no disco.
    Cria diretórios pai se necessário.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    try:
        content = serialize_okf(data)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Erro ao escrever arquivo OKF {filepath}: {e}")


# ─── Utilitários para usuários ───────────────────────────────────────

def get_usuarios_path(data_dir: str) -> str:
    return os.path.join(data_dir, 'usuarios.okf')


def get_user_dir(data_dir: str, user_id: int) -> str:
    return os.path.join(data_dir, 'kanban_users', str(user_id))


def get_board_path(data_dir: str, user_id: int, board_name: str) -> str:
    return os.path.join(get_user_dir(data_dir, user_id), f"{board_name}.okf")


def listar_usuarios(data_dir: str) -> List[Dict[str, str]]:
    """
    Retorna a lista de todos os usuários cadastrados.
    """
    path = get_usuarios_path(data_dir)
    data = read_okf(path)
    usuarios = []
    for section_id in data['section_order']:
        section = data['sections'][section_id]
        if section['type'] == 'user':
            usuarios.append(section['values'])
    return usuarios


def get_usuario_por_id(data_dir: str, user_id: int) -> Optional[Dict[str, str]]:
    """
    Busca um usuário pelo ID.
    """
    usuarios = listar_usuarios(data_dir)
    for u in usuarios:
        if u.get('id') == str(user_id):
            return u
    return None


def get_usuario_por_email(data_dir: str, email: str) -> Optional[Dict[str, str]]:
    """
    Busca um usuário pelo email.
    """
    usuarios = listar_usuarios(data_dir)
    for u in usuarios:
        if u.get('email', '').lower() == email.lower():
            return u
    return None


def criar_usuario(data_dir: str, dados: Dict[str, str]) -> Dict[str, str]:
    """
    Cria um novo usuário no arquivo usuarios.okf.
    Gera ID auto-incremental.
    """
    path = get_usuarios_path(data_dir)
    data = read_okf(path)

    # Encontrar próximo ID
    max_id = 0
    for section_id in data['section_order']:
        section = data['sections'][section_id]
        if section['type'] == 'user':
            try:
                uid = int(section['key'])
                if uid > max_id:
                    max_id = uid
            except ValueError:
                pass

    novo_id = max_id + 1
    dados['id'] = str(novo_id)
    dados['created_at'] = datetime.now().isoformat()
    dados['updated_at'] = datetime.now().isoformat()
    if 'ativo' not in dados:
        dados['ativo'] = 'true'

    section_id = f"user:{novo_id}"
    data['sections'][section_id] = {
        'type': 'user',
        'key': str(novo_id),
        'values': dict(dados)
    }
    data['section_order'].append(section_id)

    write_okf(path, data)

    # Criar diretório do usuário
    os.makedirs(get_user_dir(data_dir, novo_id), exist_ok=True)

    return dados


def atualizar_usuario(data_dir: str, user_id: int, dados: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Atualiza os dados de um usuário existente.
    """
    path = get_usuarios_path(data_dir)
    data = read_okf(path)

    section_id = f"user:{user_id}"
    if section_id not in data['sections']:
        return None

    dados['updated_at'] = datetime.now().isoformat()
    data['sections'][section_id]['values'].update(dados)

    write_okf(path, data)
    return data['sections'][section_id]['values']


def remover_usuario(data_dir: str, user_id: int) -> bool:
    """
    Remove um usuário do sistema e seu diretório de quadros.
    """
    path = get_usuarios_path(data_dir)
    data = read_okf(path)

    section_id = f"user:{user_id}"
    if section_id not in data['sections']:
        return False

    del data['sections'][section_id]
    if section_id in data['section_order']:
        data['section_order'].remove(section_id)

    write_okf(path, data)

    # Remover diretório do usuário
    user_dir = get_user_dir(data_dir, user_id)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)

    return True


# ─── Utilitários para Quadros Kanban ────────────────────────────────

def listar_quadros(data_dir: str, user_id: int) -> List[Dict[str, str]]:
    """
    Lista todos os quadros Kanban de um usuário.
    """
    user_dir = get_user_dir(data_dir, user_id)
    if not os.path.exists(user_dir):
        return []

    quadros = []
    for filename in sorted(os.listdir(user_dir)):
        if filename.endswith('.okf'):
            board_name = filename[:-4]  # remover .okf
            board_path = os.path.join(user_dir, filename)
            data = read_okf(board_path)
            meta = data['sections'].get('meta', {}).get('values', {})
            quadros.append({
                'nome': board_name,
                'titulo': meta.get('title', board_name),
                'descricao': meta.get('description', ''),
                'created_at': meta.get('created_at', ''),
                'updated_at': meta.get('updated_at', ''),
            })
    return quadros


def criar_quadro(data_dir: str, user_id: int, nome: str, titulo: str = '',
                 descricao: str = '') -> Optional[Dict[str, Any]]:
    """
    Cria um novo quadro Kanban para o usuário com colunas padrão.
    O nome do arquivo será {nome}.okf (sem espaços, lowercase).
    """
    if not nome or not isinstance(nome, str):
        return None
    if '..' in nome or '/' in nome or '\\' in nome:
        return None

    board_name = re.sub(r'[^a-z0-9_]', '', nome.lower().replace(' ', '_'))
    if not board_name or len(board_name) > 64:
        return None

    board_path = get_board_path(data_dir, user_id, board_name)
    if os.path.exists(board_path):
        return None  # já existe

    now = datetime.now().isoformat()

    data = {
        'sections': OrderedDict(),
        'section_order': []
    }

    # Seção meta
    meta_id = 'meta:main'
    data['sections'][meta_id] = {
        'type': 'meta',
        'key': 'main',
        'values': {
            'title': titulo or nome,
            'description': descricao,
            'created_at': now,
            'updated_at': now,
            'owner_id': str(user_id),
        }
    }
    data['section_order'].append(meta_id)

    # Colunas padrão
    colunas_padrao = [
        ('A Fazer', 'a-fazer', 0),
        ('Em Progresso', 'em-progresso', 1),
        ('Concluído', 'concluido', 2),
    ]

    for col_title, col_id, order in colunas_padrao:
        col_section_id = f"column:{col_id}"
        data['sections'][col_section_id] = {
            'type': 'column',
            'key': col_id,
            'values': {
                'id': col_id,
                'title': col_title,
                'order': str(order),
                'card_ids': '',
            }
        }
        data['section_order'].append(col_section_id)

    write_okf(board_path, data)
    return {
        'nome': board_name,
        'titulo': titulo or nome,
        'descricao': descricao,
        'colunas': 3,
        'cartoes': 0,
        'created_at': now,
    }


def deletar_quadro(data_dir: str, user_id: int, board_name: str) -> bool:
    """
    Remove um quadro Kanban e seu arquivo OKF.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    if not os.path.exists(board_path):
        return False
    os.remove(board_path)
    return True


def get_quadro_completo(data_dir: str, user_id: int, board_name: str) -> Optional[Dict[str, Any]]:
    """
    Retorna a estrutura completa de um quadro: metadados, colunas e cartões.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    if not os.path.exists(board_path):
        return None

    data = read_okf(board_path)

    meta = data['sections'].get('meta:main', {}).get('values', {})

    # Extrair colunas
    colunas = []
    for section_id in data['section_order']:
        section = data['sections'][section_id]
        if section['type'] == 'column':
            colunas.append(dict(section['values']))

    # Extrair cartões
    cartoes = {}
    for section_id in data['section_order']:
        section = data['sections'][section_id]
        if section['type'] == 'card':
            cartoes[section['key']] = dict(section['values'])

    # Ordenar colunas por order
    colunas.sort(key=lambda c: int(c.get('order', 0)))

    # Montar estrutura final com cartões em cada coluna
    colunas_com_cartoes = []
    for col in colunas:
        card_ids_str = col.get('card_ids', '').strip()
        card_ids = [c.strip() for c in card_ids_str.split(',') if c.strip()]

        cards_col = []
        for cid in card_ids:
            if cid in cartoes:
                cards_col.append(cartoes[cid])

        colunas_com_cartoes.append({
            'id': col.get('id', ''),
            'title': col.get('title', ''),
            'order': int(col.get('order', 0)),
            'card_ids': card_ids,
            'cards': cards_col,
        })

    return {
        'nome': board_name,
        'meta': meta,
        'colunas': colunas_com_cartoes,
    }


def adicionar_card(data_dir: str, user_id: int, board_name: str,
                   column_id: str, card_data: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Adiciona um novo cartão a uma coluna do quadro.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    if not os.path.exists(board_path):
        return None

    data = read_okf(board_path)

    # Validar que a coluna existe
    col_section_id = f"column:{column_id}"
    if col_section_id not in data['sections']:
        return None  # coluna não existe

    # Validar dados do cartão
    if not card_data or not isinstance(card_data, dict):
        return None

    # Gerar ID do cartão
    next_card_num = 1
    for section_id in data['sections']:
        section = data['sections'][section_id]
        if section['type'] == 'card':
            try:
                num = int(section['key'].replace('card_', ''))
                if num >= next_card_num:
                    next_card_num = num + 1
            except ValueError:
                pass

    if next_card_num > 9999:
        return None  # limite de segurança de cards por quadro

    card_id = f"card_{next_card_num:04d}"

    # Adicionar seção do cartão
    card_section_id = f"card:{card_id}"
    card_values = {
        'id': card_id,
        'titulo': str(card_data.get('titulo', 'Novo Cartão'))[:200],
        'descricao': str(card_data.get('descricao', ''))[:2000],
        'prioridade': card_data.get('prioridade', 'media') if card_data.get('prioridade') in ('alta', 'media', 'baixa') else 'media',
        'data_entrega': str(card_data.get('data_entrega', ''))[:10],
    }
    data['sections'][card_section_id] = {
        'type': 'card',
        'key': card_id,
        'values': card_values
    }
    data['section_order'].append(card_section_id)

    # Adicionar ID do cartão à coluna
    col = data['sections'][col_section_id]
    current_ids = col['values'].get('card_ids', '').strip()
    if current_ids:
        col['values']['card_ids'] = f"{current_ids},{card_id}"
    else:
        col['values']['card_ids'] = card_id

    # Atualizar timestamp
    if 'meta:main' in data['sections']:
        data['sections']['meta:main']['values']['updated_at'] = datetime.now().isoformat()

    write_okf(board_path, data)

    card_values['column_id'] = column_id
    return card_values


def atualizar_card(data_dir: str, user_id: int, board_name: str,
                   card_id: str, card_data: Dict[str, str]) -> bool:
    """
    Atualiza os dados de um cartão existente.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    data = read_okf(board_path)

    card_section_id = f"card:{card_id}"
    if card_section_id not in data['sections']:
        return False

    data['sections'][card_section_id]['values'].update(card_data)

    # Atualizar timestamp
    if 'meta:main' in data['sections']:
        data['sections']['meta:main']['values']['updated_at'] = datetime.now().isoformat()

    write_okf(board_path, data)
    return True


def remover_card(data_dir: str, user_id: int, board_name: str, card_id: str) -> bool:
    """
    Remove um cartão do quadro e de todas as colunas.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    data = read_okf(board_path)

    # Remover de todas as colunas
    for section_id in data['sections']:
        section = data['sections'][section_id]
        if section['type'] == 'column':
            ids_str = section['values'].get('card_ids', '').strip()
            if ids_str:
                ids = [c.strip() for c in ids_str.split(',')]
                if card_id in ids:
                    ids.remove(card_id)
                    section['values']['card_ids'] = ','.join(ids)

    # Remover seção do cartão
    card_section_id = f"card:{card_id}"
    if card_section_id in data['sections']:
        del data['sections'][card_section_id]
        if card_section_id in data['section_order']:
            data['section_order'].remove(card_section_id)

    # Atualizar timestamp
    if 'meta:main' in data['sections']:
        data['sections']['meta:main']['values']['updated_at'] = datetime.now().isoformat()

    write_okf(board_path, data)
    return True


def mover_card(data_dir: str, user_id: int, board_name: str,
               card_id: str, column_id: str, new_index: int = -1) -> bool:
    """
    Move um cartão para outra coluna e/ou posição.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    data = read_okf(board_path)

    card_section_id = f"card:{card_id}"
    if card_section_id not in data['sections']:
        return False

    # Remover de todas as colunas
    for section_id in list(data['sections'].keys()):
        section = data['sections'][section_id]
        if section['type'] == 'column':
            ids_str = section['values'].get('card_ids', '').strip()
            if ids_str:
                ids = [c.strip() for c in ids_str.split(',')]
                if card_id in ids:
                    ids.remove(card_id)
                    section['values']['card_ids'] = ','.join(ids)

    # Adicionar à coluna de destino na posição especificada
    col_section_id = f"column:{column_id}"
    if col_section_id in data['sections']:
        col = data['sections'][col_section_id]
        current_ids = col['values'].get('card_ids', '').strip()
        ids_list = [c.strip() for c in current_ids.split(',') if c.strip()]

        if 0 <= new_index < len(ids_list):
            ids_list.insert(new_index, card_id)
        else:
            ids_list.append(card_id)

        col['values']['card_ids'] = ','.join(ids_list)

    # Atualizar timestamp
    if 'meta:main' in data['sections']:
        data['sections']['meta:main']['values']['updated_at'] = datetime.now().isoformat()

    write_okf(board_path, data)
    return True


# ─── Utilitários para Colunas ──────────────────────────────────────

def adicionar_coluna(data_dir: str, user_id: int, board_name: str,
                     titulo: str) -> Optional[Dict[str, str]]:
    """
    Adiciona uma nova coluna a um quadro Kanban.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    data = read_okf(board_path)

    # Gerar ID da coluna
    col_id = re.sub(r'[^a-z0-9]', '-', titulo.lower().strip())
    col_id = col_id.strip('-') or 'nova-coluna'

    # Encontrar próximo order
    max_order = -1
    for section_id in data['sections']:
        section = data['sections'][section_id]
        if section['type'] == 'column':
            try:
                order = int(section['values'].get('order', 0))
                if order > max_order:
                    max_order = order
            except ValueError:
                pass

    col_section_id = f"column:{col_id}"
    if col_section_id in data['sections']:
        return None  # já existe

    data['sections'][col_section_id] = {
        'type': 'column',
        'key': col_id,
        'values': {
            'id': col_id,
            'title': titulo,
            'order': str(max_order + 1),
            'card_ids': '',
        }
    }
    data['section_order'].append(col_section_id)

    # Atualizar timestamp
    if 'meta:main' in data['sections']:
        data['sections']['meta:main']['values']['updated_at'] = datetime.now().isoformat()

    write_okf(board_path, data)
    return data['sections'][col_section_id]['values']


def atualizar_coluna(data_dir: str, user_id: int, board_name: str,
                     column_id: str, dados: Dict[str, str]) -> bool:
    """
    Atualiza uma coluna (título, ordem).
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    data = read_okf(board_path)

    col_section_id = f"column:{column_id}"
    if col_section_id not in data['sections']:
        return False

    data['sections'][col_section_id]['values'].update(dados)

    if 'meta:main' in data['sections']:
        data['sections']['meta:main']['values']['updated_at'] = datetime.now().isoformat()

    write_okf(board_path, data)
    return True


def remover_coluna(data_dir: str, user_id: int, board_name: str, column_id: str) -> bool:
    """
    Remove uma coluna e seus cartões do quadro.
    """
    board_path = get_board_path(data_dir, user_id, board_name)
    data = read_okf(board_path)

    col_section_id = f"column:{column_id}"
    if col_section_id not in data['sections']:
        return False

    # Obter IDs dos cartões desta coluna para remover
    col = data['sections'][col_section_id]
    card_ids_str = col['values'].get('card_ids', '').strip()
    card_ids = [c.strip() for c in card_ids_str.split(',') if c.strip()]

    # Remover cartões
    for cid in card_ids:
        card_section_id = f"card:{cid}"
        if card_section_id in data['sections']:
            del data['sections'][card_section_id]
            if card_section_id in data['section_order']:
                data['section_order'].remove(card_section_id)

    # Remover coluna
    del data['sections'][col_section_id]
    if col_section_id in data['section_order']:
        data['section_order'].remove(col_section_id)

    if 'meta:main' in data['sections']:
        data['sections']['meta:main']['values']['updated_at'] = datetime.now().isoformat()

    write_okf(board_path, data)
    return True


# ─── Métricas Globais ──────────────────────────────────────────────

def get_metricas_globais(data_dir: str) -> Dict[str, Any]:
    """
    Retorna métricas globais do sistema.
    """
    usuarios = listar_usuarios(data_dir)
    total_usuarios = len(usuarios)
    total_quadros = 0
    total_arquivos_okf = 1  # usuarios.okf
    usuarios_por_perfil = {'admin': 0, 'corporativo': 0, 'comum': 0}

    for u in usuarios:
        perfil = u.get('perfil', 'comum')
        if perfil in usuarios_por_perfil:
            usuarios_por_perfil[perfil] += 1

        # Contar quadros de cada usuário
        try:
            uid = int(u['id'])
        except (ValueError, KeyError):
            continue
        user_dir = get_user_dir(data_dir, uid)
        if os.path.exists(user_dir):
            for fname in os.listdir(user_dir):
                if fname.endswith('.okf'):
                    total_quadros += 1
                    total_arquivos_okf += 1

    return {
        'total_usuarios': total_usuarios,
        'total_quadros': total_quadros,
        'total_arquivos_okf': total_arquivos_okf,
        'usuarios_por_perfil': usuarios_por_perfil,
    }


def get_espaco_disco_usuario(data_dir: str, user_id: int) -> Dict[str, Any]:
    """
    Calcula o espaço em disco utilizado por um usuário.
    """
    user_dir = get_user_dir(data_dir, user_id)
    total_bytes = 0
    total_arquivos = 0

    if os.path.exists(user_dir):
        for root, dirs, files in os.walk(user_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    total_bytes += os.path.getsize(fpath)
                    total_arquivos += 1
                except OSError:
                    pass

    # Tamanho do registro no usuarios.okf
    try:
        usuarios_path = get_usuarios_path(data_dir)
        total_bytes += os.path.getsize(usuarios_path)
    except OSError:
        pass

    if total_bytes < 1024:
        espaco_str = f"{total_bytes} B"
    elif total_bytes < 1024 * 1024:
        espaco_str = f"{total_bytes / 1024:.1f} KB"
    else:
        espaco_str = f"{total_bytes / (1024 * 1024):.1f} MB"

    return {
        'bytes': total_bytes,
        'formatado': espaco_str,
        'arquivos': total_arquivos,
    }
